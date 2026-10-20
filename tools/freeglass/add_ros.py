"""add_ros.py in.json out.json [minr=3] [maxr=6] [floor=0.4] [seed=0] [minlen=0.03]: rosettes (Jewel) + lead canes + is-not bubbles.
A rosette {panes:[3-6 contiguous panes], cols:[colour set]} = a bold lead ring around the group with a tag listing WHICH colours occur inside (no counts).
Difficulty model = one badge at a time (freeglass2.solve_direct, which also reads canes, bubbles and rosette tags); implies unique and no-guess.
1) add the fewest clues until the level solves: per step the best rosette (while fewer than maxr), else the best cane, else a bubble;
2) drop lit starts that are really needed and patch, until at least `minr` rosettes are needed (never below `floor` of the original starts);
3) prune every clue that is not needed. Auto panes are untouched."""
import sys,json,random,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass2 import solve, solve_direct
from autofill import tap_stats
from add_not import cands
def main(a,b,minr=3,maxr=6,floor=0.4,seed=0,minlen=0.03):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); auto=lv.get('auto',[])
  minr=int(minr); maxr=int(maxr); rnd=random.Random(int(seed)); start=list(lv['start']); start0=len(start); nfloor=max(2,round(float(floor)*start0))
  nots=dict(lv.get('not',{})); canes=[tuple(c) for c in lv.get('canes',[])]; ros=[dict(r) for r in lv.get('ros',[])]
  rin=[P['rin'] for P in lv['pieces']]; med=sorted(rin)[len(rin)//2]; cen=[tuple(P['pole']) for P in lv['pieces']]
  Pt=[[tuple(x) for x in P['p']] for P in lv['pieces']]
  def shared(p,q):
    eb={frozenset((Pt[q][i],Pt[q][(i+1)%len(Pt[q])])) for i in range(len(Pt[q]))}; t=0
    for i in range(len(Pt[p])):
      u,v=Pt[p][i],Pt[p][(i+1)%len(Pt[p])]
      if frozenset((u,v)) in eb: t+=math.dist(u,v)
    return t
  cpool=[(p,q) for p in range(len(sol)) for q in nb[p] if q>p and sol[p]!=sol[q] and shared(p,q)>=float(minlen)]
  def rpool(ban):
    out=[]; seen=set()
    for s in range(len(sol)):
      if s in ban: continue
      g=[s]
      while len(g)<6:
        ext=[q for x in g for q in nb[x] if q not in g and q not in ban]
        if not ext: break
        mx=sum(cen[x][0] for x in g)/len(g); my=sum(cen[x][1] for x in g)/len(g)
        g.append(min(set(ext),key=lambda q:math.dist(cen[q],(mx,my))))
        if len(g)>=3 and max(rin[x] for x in g)>=med:   # the tag needs one roomy pane
          k=frozenset(g)
          if k not in seen: seen.add(k); out.append(sorted(g))
    return out
  full=lambda st,nt,cn,rs:solve(sol,nb,K,st,gift=gift,detail=det,auto=auto,nots=nt,canes=cn,ros=rs)
  S=lambda st,nt,cn,rs:solve_direct(sol,nb,K,st,gift=gift,detail=det,auto=auto,nots=nt,canes=cn,ros=rs) or full(st,nt,cn,rs)
  R=lambda g:{'panes':g,'cols':sorted({sol[x] for x in g})}
  def patch(st,nt,cn,rs,budget):
    nt=dict(nt); cn=list(cn); rs=list(rs); unk=S(st,nt,cn,rs); added=0
    while unk and added<budget:
      if len(rs)<maxr:
        ban=set(st)|set(gift)|set(det)|set(auto)|{x for r in rs for x in r['panes']}|{int(k) for k in nt}
        rp=rpool(ban); rnd.shuffle(rp); sc=sorted((S(st,nt,cn,rs+[R(g)]),rnd.random(),i) for i,g in enumerate(rp[:300]))
        if sc and sc[0][0]<unk: rs.append(R(rp[sc[0][2]])); unk=sc[0][0]; added+=1; continue
      sc=sorted(((S(st,nt,cn+[c],rs),rnd.random(),c) for c in cpool if c not in cn))
      if sc and sc[0][0]<unk: cn.append(sc[0][2]); unk=sc[0][0]; added+=1; continue
      ban=set(st)|set(gift)|set(det)|set(auto); C=cands(sol,nb,K,ban,3,rin,lv['pieces']); best=None
      for p,cs in C.items():
        if str(p) in nt: continue
        t=dict(nt); t[str(p)]=cs; u=S(st,t,cn,rs)
        if best is None or u<best[0]: best=(u,p,cs)
      if best is None or best[0]>=unk: break
      nt[str(best[1])]=best[2]; unk=best[0]; added+=1
    return unk,nt,cn,rs
  def prune(st,nt,cn,rs):
    for r in list(rs):
      t=[x for x in rs if x is not r]
      if S(st,nt,cn,t)==0: rs=t
    for c in list(cn):
      t=[x for x in cn if x!=c]
      if S(st,nt,t,rs)==0: cn=t
    for k in list(nt):
      t={x:v for x,v in nt.items() if x!=k}
      if S(st,t,cn,rs)==0: nt=t
    return nt,cn,rs
  unk,nots,canes,ros=patch(start,nots,canes,ros,60); assert unk==0,('not solvable', unk)
  nots,canes,ros=prune(start,nots,canes,ros); print('base: ros',len(ros),'canes',len(canes),'bubbles',len(nots),flush=True)
  while len(ros)<minr and len(start)>nfloor:
    opts=sorted(((S([x for x in start if x!=s],nots,canes,ros),rnd.random(),s) for s in start),reverse=True); ok=False
    for u,_,s in opts[:4]:
      if u==0: continue
      st=[x for x in start if x!=s]; u2,nt,cn,rs=patch(st,nots,canes,ros,25)
      if u2==0: start=st; nots,canes,ros=prune(st,nt,cn,rs); ok=True; print('dropped start',s,'ros',len(ros),'canes',len(canes),'bubbles',len(nots),flush=True); break
    if not ok: break
  assert S(start,nots,canes,ros)==0 and full(start,nots,canes,ros)==0
  canes=sorted([list(c) for c in canes]); nots={k:nots[k] for k in sorted(nots,key=int)}; ros=sorted(ros,key=lambda r:r['panes'][0])
  ts=tap_stats(sol,nb,K,start,gift,det,auto,nots,canes,ros); body=len(sol)-len(gift)-len(det)
  lv['start']=start
  for key,val in (('canes',canes),('not',nots),('ros',ros)):
    if val: lv[key]=val
    else: lv.pop(key,None)
  m=lv['metrics']; m['starts']=len(start); m['lit_share']=round(len(start)/body,4); m['ros']=len(ros); m['canes']=len(canes); m['nots']=len(nots); m['not_dots']=sum(len(v) for v in nots.values())
  for k in ('max_chain','mean_chain','max_depth','settle','taps','chains','stalls'): m[k]=ts[k]
  json.dump(lv,open(b,'w'))
  print(lv['name'],'panes',len(sol),'starts',start0,'->',len(start),'ros',len(ros),'canes',len(canes),'bubbles',len(nots),'auto',len(auto),'%.1f%%'%(100*len(auto)/body),ts)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:8])
