"""blobify.py in.json out.json [passes=8] [seed=0]: make panes compact blobs. Any pane (not tiny, not gift/detail) with aspect>3 or solidity<0.7 (see compact.py) is either
 (a) MERGED into a neighbouring pane of the SAME colour when the union is a single, clearly more compact polygon (fewer panes), or
 (b) cut by a k-means/Voronoi partition into 2.. compact pieces of the same colour (k-means++ restarts, best by worst badness).
The colour map is unchanged. Sharp angles are allowed (min angle is informational only). Game-necessary checks only: every piece one valid polygon, exact partition, no ambiguous near-touching contacts,
no zero-area/degenerate pieces (MINPIECE). Detail/gift panes are never touched. start/auto are dropped: run rework.py afterwards (rw_level.py does), which restores a unique no-guess solution."""
import sys, json, math, os, random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from shapely.ops import unary_union, polylabel
import freeglass3
freeglass3.STRICT_SPIKES=False
from freeglass3 import check, ring, export
from split_thin import metrics, parts, insert_pts
from compact import pane, MAXASP, MINSOL, TINY
MINPIECE=0.00035; MAXMERGE=0.04
def bad(g):
  a,s,_=pane(g,0); return max(a/MAXASP,MINSOL/max(s,1e-6))
def touching(G,i,j): return G[i].boundary.intersection(G[j].buffer(2e-6)).length>1e-3
def main(a,b,passes=8,seed=0):
  lv=json.load(open(a)); G=[Polygon(p['p']) for p in lv['pieces']]; sol=list(lv['sol']); n0=len(G)
  det=set(lv.get('detail',[])); gift=set(lv.get('gift',[])); tag=['d' if i in det else 'g' if i in gift else None for i in range(n0)]; art=[lv['pieces'][i] if i in det else None for i in range(n0)]
  uid=list(range(n0)); nxt=n0; rnd=random.Random(int(seed)); freeglass3.set_frame(1.0,1/lv.get('aspect',1)); dead=set(); merges=0; cuts=0
  def commit(H,sl,tg,ar,ids):
    nonlocal G,sol,tag,art,uid; G,sol,tag,art,uid=H,sl,tg,ar,ids
  for ps_ in range(int(passes)):
    order=sorted([(bad(g),u) for g,u,t in zip(G,uid,tag) if t is None and u not in dead and g.area>=TINY and bad(g)>1],reverse=True)
    if not order: break
    c0=merges+cuts
    for _,u in order:
      if u not in uid: continue
      i=uid.index(u); g=G[i]; b0=bad(g)
      if b0<=1: continue
      done=False
      # (a) merge into same-colour neighbour
      best=None
      for j in range(len(G)):
        if j==i or tag[j] is not None or sol[j]!=sol[i] or not touching(G,i,j): continue
        U=unary_union([G[i],G[j]])
        if U.geom_type!='Polygon' or not U.is_valid or U.area>MAXMERGE: continue
        bu=bad(U)
        if bu<=max(1.2,0.8*b0) and (best is None or bu<best[0]): best=(bu,j,U)
      if best:
        bu,j,U=best; H=list(G); H[i]=U; keep=[k for k in range(len(G)) if k!=j]
        H2=[H[k] for k in keep]
        try: H3,_=export(H2); ok,nb,v=check(H3)
        except Exception: ok=False
        if ok and all(nb):
          commit(H3,[sol[k] for k in keep],[tag[k] for k in keep],[art[k] for k in keep],[uid[k] for k in keep]); merges+=1; continue
      # (b) cut
      k0=max(2,math.ceil(metrics(g)[0]/MAXASP)); cands=[]
      for k in range(2,k0+3):
        if g.area/k<MINPIECE: break
        for tr in range(7):
          q=parts(g,k,rnd,pp=tr>0)
          if q and len(q)>=2 and min(p.area for p in q)>=MINPIECE:
            m=max(bad(p) for p in q)
            if m<b0-0.05: cands.append((0,k,m,q) if m<=1.05 else (1,m,k,q))
        if any(c[0]==0 for c in cands): break
      cand=None
      if cands:
        c=min(cands,key=lambda c:c[:3]); cand=(c[2] if c[0]==0 else c[1],0,c[3])
      if cand:
        ps=cand[2]; pts=[tuple(c) for p in ps for c in ring(p)]; H=list(G); H[i]=ps[0]; H+=ps[1:]
        for j in range(len(G)):
          if j!=i and G[j].distance(g)<1e-5: H[j]=insert_pts(G[j],pts)
        try:
          H2,_=export(H); ok,nb,v=check(H2)
        except Exception: ok=False
        if ok and all(nb):
          m=len(ps)-1; commit(H2,sol+[sol[i]]*m,tag+[None]*m,art+[None]*m,uid+list(range(nxt,nxt+m))); nxt+=m; cuts+=1; continue
      dead.add(u)
    print('pass',ps_,'merges',merges,'cuts',cuts,'panes',len(G),flush=True)
    if merges+cuts==c0: break
  ok,nb,v=check(G); P=[]
  for i,g in enumerate(G):
    p=dict(art[i]) if art[i] else {}
    p['p']=[list(x) for x in ring(g)]; pl=polylabel(g,1e-4); p['pole']=[round(pl.x,5),round(pl.y,5)]; p['rin']=round(g.exterior.distance(pl),5); P.append(p)
  lv['pieces']=P; lv['sol']=sol; lv['nb']=nb; lv.pop('auto',None)
  lv['detail']=[i for i,t in enumerate(tag) if t=='d']
  if 'gift' in lv: lv['gift']=[i for i,t in enumerate(tag) if t=='g']
  lv['metrics']=dict(lv.get('metrics',{}),pieces=len(G),min_angle_deg=v['min_angle_deg'],spikes=v['spikes'],ambiguous_contacts=v['ambiguous_contacts'],corner_touches=v['corner_touches'],min_shared_border=v['min_shared_border'])
  json.dump(lv,open(b,'w')); print('merges',merges,'cuts',cuts,'panes',n0,'->',len(G),'min_angle(info)',v['min_angle_deg'])
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:5])
