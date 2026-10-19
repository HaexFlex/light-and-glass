"""add_not.py in.json out.json [drop=0.34] [maxdots=3] [seed=0] [minb=3]: 'Is not' bubbles (Tinted and up).
A bubble on an unlit pane lists colours that NONE of its neighbours has (crossed-out dots); shown from the start.
Generator: tries to drop lit starts (about `drop` of them); starts that are redundant stay (local starts); a needed start is dropped only if a few bubbles restore a solve that a player can do one badge at a time
(freeglass2.solve_direct == 0; implies unique and no-guess, no forced autofill). Bubbles are chosen greedily (most panes resolved),
then pruned so only the ones needed remain. Auto clusters are untouched (they never touch a start, so settle stays = starts)."""
import sys,json,random,os,math
from shapely.geometry import Polygon
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass2 import solve, solve_direct
from autofill import tap_stats, simulate
def cands(sol,nb,K,ban,maxdots,rin=None):
  out={}; big=sorted(rin)[len(rin)//2]*1.2 if rin else 0   # readability: only panes at least 1.2x the median inner radius carry a bubble
  for p in range(len(sol)):
    if p in ban or (rin and rin[p]<big): continue
    nbc={sol[q] for q in nb[p]}; absent=[c for c in range(K) if c not in nbc]
    if not absent: continue
    near={}
    for q in nb[p]:
      for r in nb[q]:
        if sol[r] in absent: near[sol[r]]=near.get(sol[r],0)+1   # colours that are nearby (2 steps) but not adjacent: the informative ones
    absent.sort(key=lambda c:(-near.get(c,0),c))
    cs=[c for c in absent if near.get(c,0)][:maxdots]
    if cs: out[p]=sorted(cs)
  return out
def main(a,b,drop=0.34,maxdots=3,seed=0,minb=3):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); auto=lv.get('auto',[])
  start=list(lv['start']); rnd=random.Random(int(seed)); maxdots=int(maxdots)
  full=lambda st,nots:solve(sol,nb,K,st,gift=gift,detail=det,auto=auto,nots=nots)
  S=lambda st,nots:solve_direct(sol,nb,K,st,gift=gift,detail=det,auto=auto,nots=nots) or full(st,nots)   # Tinted difficulty: solvable one badge at a time (and so unique/no-guess for the game's solver)
  assert full(start,{})==0, 'level must solve without bubbles first'
  nots={}; dropped=[]; floor=max(3,round((1-float(drop))*len(start))); minb=int(minb)
  # drop starts one at a time, always the one whose loss leaves the most panes unsolved (i.e. a start that is really needed), and patch the gap with bubbles.
  # If no needed start can be patched, the most crowded redundant start goes. Stops once `minb` bubbles are needed or only (1-drop) of the starts are left.
  cen=[Polygon(P['p']).centroid.coords[0] for P in lv['pieces']]
  while len(start)>floor and len(nots)<minb:
    opts=[]
    for s in start:
      st=[x for x in start if x!=s]; opts.append((S(st,nots),rnd.random(),s))
    opts=sorted((o for o in opts if o[0]>0),reverse=True); ok=False   # only starts that are really needed (redundant ones stay as local starts)
    for unk,_,s in opts[:6]:
      st=[x for x in start if x!=s]; ban=set(st)|set(gift)|set(det)|set(auto)|{s}
      C=cands(sol,nb,K,ban,maxdots,[P['rin'] for P in lv['pieces']]); trial=dict(nots); added=0
      while unk and added<6:
        best=None
        for p,cs in C.items():
          if str(p) in trial: continue
          t=dict(trial); t[str(p)]=cs; u=S(st,t)
          if best is None or u<best[0]: best=(u,p)
        if best is None or best[0]>=unk: break
        trial[str(best[1])]=C[best[1]]; unk=best[0]; added+=1
      if unk==0:
        start=st; nots=trial; dropped.append(s); ok=True; print('dropped start',s,'bubbles',len(nots),flush=True); break
    if not ok:   # nothing needed could be patched: give up the most crowded redundant start (closest to another start) and try again
      red=[s for u,_,s in sorted(((S([x for x in start if x!=s],nots),0,s) for s in start)) if u==0]
      if not red: break
      s=min(red,key=lambda s:min(math.dist(cen[s],cen[t]) for t in start if t!=s)); start=[x for x in start if x!=s]; dropped.append(s); print('dropped redundant start',s,flush=True)
  for k in sorted(nots,key=lambda k:-len(nots[k])):   # prune: keep only bubbles that are needed
    t={x:v for x,v in nots.items() if x!=k}
    if S(start,t)==0: nots=t
  for k in list(nots):   # and only the dots that are needed
    for c in list(nots[k]):
      if len(nots[k])==1: break
      t=dict(nots); t[k]=[x for x in nots[k] if x!=c]
      if S(start,t)==0: nots=t
  assert S(start,nots)==0 and full(start,nots)==0
  nots={k:nots[k] for k in sorted(nots,key=int)}
  ts=tap_stats(sol,nb,K,start,gift,det,auto,nots); body=len(sol)-len(gift)-len(det)
  lv['start']=start; lv['not']=nots; m=lv['metrics']; m['starts']=len(start); m['lit_share']=round(len(start)/body,4); m['nots']=len(nots); m['not_dots']=sum(len(v) for v in nots.values())
  for k in ('max_chain','mean_chain','max_depth','settle','taps','chains','stalls'): m[k]=ts[k]
  json.dump(lv,open(b,'w'))
  print(lv['name'],'panes',len(sol),'starts',len(start),'(dropped',len(dropped),') bubbles',len(nots),'dots',m['not_dots'],'auto',len(auto),'%.1f%%'%(100*len(auto)/body),ts)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:7])
