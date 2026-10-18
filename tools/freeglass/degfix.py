"""degfix.py in.json out.json [maxdeg=10] [passes=10] [seed=0]: no pane may have more than `maxdeg` neighbours (neighbour = shared border length > 0, the game's adjacency).
For each pane above the limit (not detail/gift): (a) MERGE it with a same-colour neighbour when the union is one polygon, not snaky (bad<=1.5) and its degree is <= maxdeg, or
(b) CUT it (k-means/Voronoi, k=2..) into compact same-colour pieces that all stay <= maxdeg without pushing any other pane over the limit. Colour map unchanged. A step is kept only if
the geometry check passes (valid partition, no ambiguous contacts) and the total excess above the limit shrinks. start/auto are dropped: run rework.py afterwards."""
import sys, json, math, os, random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from shapely.ops import unary_union, polylabel
import freeglass3
freeglass3.STRICT_SPIKES=False
from freeglass3 import check, ring, export
from split_thin import parts, insert_pts
from blobify import bad, touching, MINPIECE, MAXMERGE
def excess(nb,tag,md): return sum(max(0,len(x)-md) for x,t in zip(nb,tag) if t is None)
def main(a,b,md=10,passes=10,seed=0):
  md=int(md); lv=json.load(open(a)); G=[Polygon(p['p']) for p in lv['pieces']]; sol=list(lv['sol']); n0=len(G)
  det=set(lv.get('detail',[])); gift=set(lv.get('gift',[])); tag=['d' if i in det else 'g' if i in gift else None for i in range(n0)]; art=[lv['pieces'][i] if i in det else None for i in range(n0)]
  uid=list(range(n0)); nxt=n0; rnd=random.Random(int(seed)); freeglass3.set_frame(1.0,1/lv.get('aspect',1)); nb=lv['nb']; dead=set(); stat=dict(merge=0,cut=0)
  for ps_ in range(int(passes)):
    over=sorted([(len(nb[i]),uid[i]) for i in range(len(G)) if tag[i] is None and len(nb[i])>md and uid[i] not in dead],reverse=True)
    if not over: break
    c0=stat['merge']+stat['cut']
    for _,u in over:
      if u not in uid: continue
      i=uid.index(u)
      if len(nb[i])<=md: continue
      e0=excess(nb,tag,md); done=False
      # (a) merge
      opts=[]
      for j in nb[i]:
        if tag[j] is not None or sol[j]!=sol[i]: continue
        U=unary_union([G[i],G[j]])
        if U.geom_type!='Polygon' or not U.is_valid or U.area>MAXMERGE or bad(U)>1.5: continue
        nd=len((set(nb[i])|set(nb[j]))-{i,j})
        if nd<=md: opts.append((nd,j,U))
      for nd,j,U in sorted(opts,key=lambda o:o[0]):
        H=list(G); H[i]=U; keep=[k for k in range(len(G)) if k!=j]
        try:
          H3,_=export([H[k] for k in keep]); ok,nb2,v=check(H3)
        except Exception: continue
        tg=[tag[k] for k in keep]
        if ok and all(nb2) and excess(nb2,tg,md)<e0:
          G=H3; sol=[sol[k] for k in keep]; tag=tg; art=[art[k] for k in keep]; uid=[uid[k] for k in keep]; nb=nb2; stat['merge']+=1; done=True; break
      if done: continue
      # (b) cut
      g=G[i]; best=None
      for k in range(2,6):
        if g.area/k<MINPIECE: break
        for tr in range(8):
          q=parts(g,k,rnd,pp=tr>0,repair=True)
          if not q or len(q)<2 or min(p.area for p in q)<MINPIECE: continue
          pts=[tuple(c) for p in q for c in ring(p)]; H=list(G); H[i]=q[0]; H+=q[1:]
          for j in range(len(G)):
            if j!=i and G[j].distance(g)<1e-5: H[j]=insert_pts(G[j],pts)
          try: H2,_=export(H); ok,nb2,v=check(H2)
          except Exception: continue
          if not (ok and all(nb2)): continue
          m=len(q)-1; tg=tag+[None]*m; e=excess(nb2,tg,md); sc=(e,max(bad(p) for p in q))
          if e<e0 and (best is None or sc<best[0]): best=(sc,H2,nb2,m)
        if best and best[0][0]==0: break
      if best:
        _,H2,nb2,m=best; G=H2; sol=sol+[sol[i]]*m; tag=tag+[None]*m; art=art+[None]*m; uid=uid+list(range(nxt,nxt+m)); nxt+=m; nb=nb2; stat['cut']+=1; continue
      dead.add(u)
    print('pass',ps_,stat,'panes',len(G),'max deg',max(len(x) for x in nb),'excess',excess(nb,tag,md),flush=True)
    if stat['merge']+stat['cut']==c0: break
  ok,nb,v=check(G); P=[]
  for i,g in enumerate(G):
    p=dict(art[i]) if art[i] else {}
    p['p']=[list(x) for x in ring(g)]; pl=polylabel(g,1e-4); p['pole']=[round(pl.x,5),round(pl.y,5)]; p['rin']=round(g.exterior.distance(pl),5); P.append(p)
  lv['pieces']=P; lv['sol']=sol; lv['nb']=nb; lv.pop('auto',None); lv['detail']=[i for i,t in enumerate(tag) if t=='d']
  if 'gift' in lv: lv['gift']=[i for i,t in enumerate(tag) if t=='g']
  lv['metrics']=dict(lv.get('metrics',{}),pieces=len(G),min_angle_deg=v['min_angle_deg'],spikes=v['spikes'],ambiguous_contacts=v['ambiguous_contacts'],corner_touches=v['corner_touches'],min_shared_border=v['min_shared_border'],max_degree=max(len(x) for x in nb))
  json.dump(lv,open(b,'w')); print('panes',n0,'->',len(G),'max degree',max(len(x) for x in nb),stat)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:6])
