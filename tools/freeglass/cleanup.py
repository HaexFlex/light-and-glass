"""cleanup.py in.json out.json [passes=8] [seed=0]: post-palette sliver/branch cleanup for photo levels (colour map unchanged; detail/gift panes untouched).
 (a) SLIVERS: a thin pane (aspect>3 or solidity<0.7, see compact.py) with a same-colour neighbour is merged into the same-colour neighbour it shares the
     LONGEST border with (no compactness condition: the union is fixed by (b) if needed).
 (b) BRANCHES: every pane is opened morphologically (radius ~0.45 x its inradius); each thin arm that sticks out of the core is ALWAYS cut off. The arm is merged
     into the same-colour neighbour it shares the longest border with, if one touches it; otherwise it is cut into compact pieces (k-means partition) that pass the blob rule.
 (c) more than 10 neighbours after a merge: run degfix.py afterwards (rw pipeline does), which chord-cuts the blob into compact halves.
start/auto/clues are dropped: run rework.py and mechfirst.py afterwards."""
import sys, json, math, os, random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union, polylabel
import freeglass3
freeglass3.STRICT_SPIKES=False
from freeglass3 import check, ring, export
from split_thin import parts, insert_pts
from compact import pane, MAXASP, MINSOL, TINY
MINPIECE=0.00035; OPEN=0.45; RECOL=6*MINPIECE
def bad(g): a,s,_=pane(g,0); return max(a/MAXASP,MINSOL/max(s,1e-6))
def shared(a,b): return a.boundary.intersection(b.buffer(2e-6)).length
def inr(g): p=polylabel(g,1e-4); return g.exterior.distance(p)
def polys(x): return [x] if x.geom_type=='Polygon' else [p for p in getattr(x,'geoms',[]) if p.geom_type=='Polygon']
def arms(g,f=OPEN,simp=2e-4):
  """thin arms of g: components of g - opening(g) that are big enough and hang on a narrow neck"""
  r=f*inr(g)
  if r<=1e-4: return []
  core=g.buffer(-r,quad_segs=4).buffer(r,quad_segs=4)
  if core.is_empty: return []
  core=max(polys(core),key=lambda p:p.area); out=[]
  for c in polys(g.difference(core).buffer(-1e-6).buffer(1e-6)):
    if c.area<MINPIECE: continue
    neck=c.boundary.intersection(core.buffer(3e-6)).length; w=2*inr(c)
    if neck<0.6*c.length/2 and (c.length/2)>2.2*max(w,1e-6): out.append(c.simplify(min(simp,r*0.3)))   # long and attached by a short neck
  return out
def thin_count(G,tag):
  return sum(1 for g,t in zip(G,tag) if t is None and g.area>=TINY and bad(g)>1), sum(1 for g,t in zip(G,tag) if t is None and arms(g))
def main(a,b,passes=8,seed=0):
  lv=json.load(open(a)); G=[Polygon(p['p']) for p in lv['pieces']]; sol=list(lv['sol']); n0=len(G)
  det=set(lv.get('detail',[])); gift=set(lv.get('gift',[])); tag=['d' if i in det else 'g' if i in gift else None for i in range(n0)]; art=[lv['pieces'][i] if i in det else None for i in range(n0)]
  rnd=random.Random(int(seed)); freeglass3.set_frame(1.0,1/lv.get('aspect',1)); st={'merge':0,'arm_merge':0,'arm_cut':0,'recolour':0}
  before=thin_count(G,tag); print('before thin',before,flush=True)
  def try_commit(H,sl,tg,ar):
    nonlocal G,sol,tag,art
    try: H2,_=export(H); ok,nb,v=check(H2)
    except Exception: return False
    if ok and all(nb): G,sol,tag,art=H2,sl,tg,ar; return True
    return False
  def merge(i,j,U):   # replace i by U, drop j
    H=list(G); H[i]=U; keep=[k for k in range(len(G)) if k!=j]
    return try_commit([H[k] for k in keep],[sol[k] for k in keep],[tag[k] for k in keep],[art[k] for k in keep])
  def deg_ok(U,skip):   # a merge may exceed 10 neighbours only if the union is still a solid blob that degfix can chord-cut in two
    d=sum(1 for k in range(len(G)) if k not in skip and G[k].distance(U)<1e-6 and shared(U,G[k])>1e-3)
    return d<=10 or (U.area/U.convex_hull.area>=0.6 and d<=16)
  def best_same(i,g):
    c=[(shared(g,G[j]),j) for j in range(len(G)) if j!=i and tag[j] is None and sol[j]==sol[i] and G[j].distance(g)<1e-5]
    c=[x for x in c if x[0]>1e-3]; return [j for _,j in sorted(c,reverse=True)]
  for ps_ in range(int(passes)):
    ch=0
    # (a) slivers
    for i in sorted(range(len(G)),key=lambda i:-bad(G[i])):
      if i>=len(G) or tag[i] is not None or bad(G[i])<=1: continue
      for j in best_same(i,G[i])[:2]:
        U=unary_union([G[i],G[j]])
        if U.geom_type=='Polygon' and U.is_valid and deg_ok(U,(i,j)) and merge(j,i,U): st['merge']+=1; ch+=1; break
      else:
        if i<len(G) and tag[i] is None and bad(G[i])>1 and G[i].area<RECOL and not best_same(i,G[i]):   # small sliver, no same-colour neighbour: last resort, absorb into the neighbour with the longest border
          g=G[i]; nbs=sorted(((shared(g,G[j]),j) for j in range(len(G)) if j!=i and tag[j] is None and G[j].distance(g)<1e-5),reverse=True)
          for _,j in nbs[:2]:
            U=unary_union([G[i],G[j]])
            if U.geom_type=='Polygon' and U.is_valid and merge(j,i,U): st['recolour']+=1; ch+=1; break
    # (b) branches
    i=0
    while i<len(G):
      if tag[i] is not None: i+=1; continue
      A=arms(G[i]); A=A+[x for f,sm in ((0.45,6e-4),(0.35,6e-4),(0.55,1e-3)) for x in arms(G[i],f,sm)] if A else A; done=False
      for c in A:
        g=G[i]; rest=g.difference(c)
        rp=polys(rest)
        if not rp: continue
        main_=max(rp,key=lambda p:p.area)
        if main_.area<0.3*g.area: continue
        arm=g.difference(main_)
        ap=[p for p in polys(arm) if p.area>1e-9]
        if len(ap)!=1: continue
        arm=ap[0]
        # merge arm into same-colour neighbour (longest border)
        tgt=[(shared(arm,G[j]),j) for j in range(len(G)) if j!=i and tag[j] is None and sol[j]==sol[i] and G[j].distance(arm)<1e-5]
        tgt=[x for x in sorted(tgt,reverse=True) if x[0]>1e-3]
        ok=False
        for _,j in tgt[:2]:
          U=unary_union([G[j],arm])
          if U.geom_type!='Polygon' or not U.is_valid or not deg_ok(U,(i,j)): continue
          H=list(G); H[i]=main_; H[j]=U; pts=[tuple(x) for x in ring(main_)]
          H=[insert_pts(h,pts) if k not in (i,j) and h.distance(g)<1e-5 else h for k,h in enumerate(H)]
          if try_commit(H,list(sol),list(tag),list(art)): st['arm_merge']+=1; ok=True; break
        if not ok:   # keep as its own compact piece(s)
          pcs=[arm] if bad(arm)<=1.05 else None
          if pcs is None:
            for k in range(2,8):
              if arm.area/k<MINPIECE*0.6: break
              q=None
              for tr in range(6):
                q=parts(arm,k,rnd,pp=tr>0)
                if q and len(q)==k and max(bad(p) for p in q)<=1.05: break
                q=None
              if q: pcs=q; break
          if pcs is None and arm.area<RECOL:   # too small to split into compact pieces: last resort, absorb into the neighbour with the longest border
            nbs=sorted(((shared(arm,G[j]),j) for j in range(len(G)) if j!=i and tag[j] is None and G[j].distance(arm)<1e-5),reverse=True)
            for _,j in nbs[:2]:
              U=unary_union([G[j],arm])
              if U.geom_type!='Polygon' or not U.is_valid: continue
              H=list(G); H[i]=main_; H[j]=U; pts=[tuple(x) for x in ring(main_)]
              H=[insert_pts(h,pts) if k not in (i,j) and h.distance(g)<1e-5 else h for k,h in enumerate(H)]
              if try_commit(H,list(sol),list(tag),list(art)): st['recolour']+=1; ok=True; break
            if ok: done=True; ch+=1; break
          if pcs is None: pcs=[arm]
          H=list(G); H[i]=main_; H+=pcs; pts=[tuple(x) for p in [main_]+pcs for x in ring(p)]
          H=[insert_pts(h,pts) if k!=i and k<len(G) and h.distance(g)<1e-5 else h for k,h in enumerate(H)]
          m=len(pcs)
          if try_commit(H,sol+[sol[i]]*m,tag+[None]*m,art+[None]*m): st['arm_cut']+=1; ok=True
        if ok: done=True; ch+=1; break
      if not done: i+=1
    print('pass',ps_,st,'panes',len(G),flush=True)
    if not ch: break
  after=thin_count(G,tag)
  ok,nb,v=check(G); P=[]
  for i,g in enumerate(G):
    p=dict(art[i]) if art[i] else {}
    p['p']=[list(x) for x in ring(g)]; pl=polylabel(g,1e-4); p['pole']=[round(pl.x,5),round(pl.y,5)]; p['rin']=round(g.exterior.distance(pl),5); P.append(p)
  lv['pieces']=P; lv['sol']=sol; lv['nb']=nb
  for k in ('auto','not','canes','ros'): lv.pop(k,None)
  lv['start']=[]
  lv['detail']=[i for i,t in enumerate(tag) if t=='d']
  if 'gift' in lv: lv['gift']=[i for i,t in enumerate(tag) if t=='g']
  lv['metrics']=dict(lv.get('metrics',{}),pieces=len(G),thin_before=before[0],arms_before=before[1],thin_after=after[0],arms_after=after[1],min_angle_deg=v['min_angle_deg'],spikes=v['spikes'],ambiguous_contacts=v['ambiguous_contacts'],corner_touches=v['corner_touches'],min_shared_border=v['min_shared_border'])
  json.dump(lv,open(b,'w')); print('CLEANUP',lv['id'],'panes',n0,'->',len(G),'thin',before[0],'->',after[0],'arms',before[1],'->',after[1],st,flush=True)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:5])
