"""add_canes.py in.json out.json [minc=5] [maxc=10] [floor=0.5] [seed=0] [minlen=0.04]: lead canes (Stained and up) + is-not bubbles where canes cannot help.
A cane [a,b] = a thick lead line on the border of neighbours a and b: they have DIFFERENT colours (only placed where the solution colours differ).
Difficulty model = one badge at a time (freeglass2.solve_direct, which also uses canes and bubbles); this implies unique and no-guess for the game's solver.
1) add the fewest clues (best cane per step; a bubble only when no cane helps) until the level solves; 2) drop lit starts that are really needed and patch
each gap with canes, until at least `minc` canes are needed (at most `maxc`; never below `floor` of the original starts); 3) prune clues that are not needed.
Auto clusters are untouched (never touch a start), so the autofill share stays as built."""
import sys,json,random,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass2 import solve, solve_direct
from autofill import tap_stats
from add_not import cands
def main(a,b,minc=5,maxc=10,floor=0.5,seed=0,minlen=0.04):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); auto=lv.get('auto',[])
  minc=int(minc); maxc=int(maxc); rnd=random.Random(int(seed)); start=list(lv['start']); start0=len(start); nfloor=max(3,round(float(floor)*start0))
  nots=dict(lv.get('not',{})); canes=[tuple(c) for c in lv.get('canes',[])]; rin=[P['rin'] for P in lv['pieces']]
  Pt=[[tuple(x) for x in P['p']] for P in lv['pieces']]
  def shared(p,q):   # length of the border p and q share (readability: canes only on borders >= minlen of the window width)
    eb={frozenset((Pt[q][i],Pt[q][(i+1)%len(Pt[q])])) for i in range(len(Pt[q]))}; t=0
    for i in range(len(Pt[p])):
      u,v=Pt[p][i],Pt[p][(i+1)%len(Pt[p])]
      if frozenset((u,v)) in eb: t+=((u[0]-v[0])**2+(u[1]-v[1])**2)**.5
    return t
  pool=[(p,q) for p in range(len(sol)) for q in nb[p] if q>p and sol[p]!=sol[q] and shared(p,q)>=float(minlen)]
  full=lambda st,nt,cn:solve(sol,nb,K,st,gift=gift,detail=det,auto=auto,nots=nt,canes=cn)
  S=lambda st,nt,cn:solve_direct(sol,nb,K,st,gift=gift,detail=det,auto=auto,nots=nt,canes=cn) or full(st,nt,cn)
  def patch(st,nt,cn,budget):
    nt=dict(nt); cn=list(cn); unk=S(st,nt,cn); added=0
    while unk and added<budget:
      sc=sorted(((S(st,nt,cn+[c]),rnd.random(),c) for c in pool if c not in cn))
      if sc and sc[0][0]<unk: cn.append(sc[0][2]); unk=sc[0][0]; added+=1; continue
      ban=set(st)|set(gift)|set(det)|set(auto); C=cands(sol,nb,K,ban,3,rin); best=None
      for p,cs in C.items():
        if str(p) in nt: continue
        t=dict(nt); t[str(p)]=cs; u=S(st,t,cn)
        if best is None or u<best[0]: best=(u,p,cs)
      if best is None or best[0]>=unk: break
      nt[str(best[1])]=best[2]; unk=best[0]; added+=1
    return unk,nt,cn
  unk,nots,canes=patch(start,nots,canes,40); assert unk==0,'could not make the level solvable one badge at a time'
  print('base: canes',len(canes),'bubbles',len(nots),flush=True)
  def prune(nots,canes):
    for c in list(canes):
      t=[x for x in canes if x!=c]
      if S(start,nots,t)==0: canes=t
    for k in list(nots):
      t={x:v for x,v in nots.items() if x!=k}
      if S(start,t,canes)==0: nots=t
    return nots,canes
  nots,canes=prune(nots,canes); dropped=[]
  while len(canes)<minc and len(start)>nfloor:   # pruned count is what counts
    opts=sorted(((S([x for x in start if x!=s],nots,canes),rnd.random(),s) for s in start),reverse=True); ok=False
    for u,_,s in opts[:6]:
      if u==0: continue
      st=[x for x in start if x!=s]; u2,nt,cn=patch(st,nots,canes,maxc-len(canes))
      if u2==0 and len(cn)<=maxc: start=st; nots,canes=prune(nt,cn); dropped.append(s); ok=True; print('dropped start',s,'canes',len(canes),'bubbles',len(nots),flush=True); break
    if not ok: break
  assert S(start,nots,canes)==0 and full(start,nots,canes)==0
  canes=sorted([list(c) for c in canes]); nots={k:nots[k] for k in sorted(nots,key=int)}
  ts=tap_stats(sol,nb,K,start,gift,det,auto,nots,canes); body=len(sol)-len(gift)-len(det)
  lv['start']=start; lv['canes']=canes
  if nots: lv['not']=nots
  else: lv.pop('not',None)
  m=lv['metrics']; m['starts']=len(start); m['lit_share']=round(len(start)/body,4); m['canes']=len(canes); m['nots']=len(nots); m['not_dots']=sum(len(v) for v in nots.values())
  for k in ('max_chain','mean_chain','max_depth','settle','taps','chains','stalls'): m[k]=ts[k]
  json.dump(lv,open(b,'w'))
  print(lv['name'],'panes',len(sol),'starts',start0,'->',len(start),'canes',len(canes),'bubbles',len(nots),'auto',len(auto),'%.1f%%'%(100*len(auto)/body),ts)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:8])
