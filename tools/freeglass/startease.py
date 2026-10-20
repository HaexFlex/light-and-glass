"""startease.py [level.json ...]: how easy is the START of a level.
Initial state = lit starts + gift + designed autofill already applied (an auto pane is revealed as soon as a neighbour is lit, chained; detail panes likewise).
depth 1 = a pane is forced by ONE lit badge on its own (with its already known neighbours).
depth 2 = needs TWO clues combined: two badges, or a badge plus one 'is not' bubble / cane / rosette.
depth 3 = only the full one-badge-at-a-time solver (solve_direct) or more makes progress; 0 = no forced move at all.
Also: n1 = number of depth-1 forced panes at the start, spread = max adjacency distance between lit starts, near = adjacency distance from the first forced pane(s) to the lit cluster.
Importable: ease(lv) -> dict; cluster_spread(nb,starts)."""
import sys,os,json,itertools
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from collections import deque
def hops(nb,src):
  d={s:0 for s in src};q=deque(src)
  while q:
    x=q.popleft()
    for y in nb[x]:
      if y not in d: d[y]=d[x]+1;q.append(y)
  return d
def cluster_spread(nb,starts):
  return max((max(hops(nb,[s])[t] for t in starts) for s in starts),default=0)
def init_state(lv):
  sol=lv['sol'];nb=lv['nb'];start=list(lv['start']);gift=set(lv.get('gift',[]));det=set(lv.get('detail',[]));auto=set(lv.get('auto',[]))
  known=set(start)|gift;lit=set(start);ch=True
  while ch:
    ch=False
    for a in auto|det:
      if a not in known and any(q in lit for q in nb[a]):
        known.add(a);ch=True
        if a in auto: lit.add(a)
  return known,lit
def ease(lv):
  """depth = how many clues must be combined for the first forced pane: a lit badge counts as one clue, so does each 'is not' bubble, cane and rosette."""
  sol=lv['sol'];nb=lv['nb'];K=len(lv['colors']);N=len(sol)
  nots=lv.get('not',{}) or {};canes=lv.get('canes',[]) or [];ros=lv.get('ros',[]) or []
  known,lit=init_state(lv)
  ALL=set(range(K))
  def badge(p):
    cnt=[0]*K
    for q in nb[p]: cnt[sol[q]]+=1
    for q in nb[p]:
      if q in known: cnt[sol[q]]-=1
    return cnt,[q for q in nb[p] if q not in known]
  # extra clues as domain restrictions: (name, {pane: allowed colours})
  extra=[]
  for k,cs in nots.items(): extra.append(('not',{q:ALL-set(cs) for q in nb[int(k)] if q not in known}))
  for x,y in canes:
    if x in known and y not in known: extra.append(('cane',{y:ALL-{sol[x]}}))
    if y in known and x not in known: extra.append(('cane',{x:ALL-{sol[y]}}))
  for r in ros: extra.append(('ros',{q:set(r['cols']) for q in r['panes'] if q not in known}))
  def joint(badges,R):
    """panes forced when the given badges (each a (cnt,U)) are combined with restriction R: exact enumeration"""
    U=sorted({u for _,Ub in badges for u in Ub})
    D=[]
    for u in U:
      d=set(R.get(u,ALL))
      for cnt,Ub in badges:
        if u in Ub: d&={c for c in range(K) if cnt[c]>0}
      D.append(sorted(d))
    tot=1
    for d in D: tot*=max(1,len(d))
    if tot>300000 or any(not d for d in D): return set()
    seen=[set() for _ in U]
    for asg in itertools.product(*D):
      ok=True
      for cnt,Ub in badges:
        c2=[0]*K
        for u,c in zip(U,asg):
          if u in Ub: c2[c]+=1
        if c2!=cnt: ok=False;break
      if ok:
        for j,c in enumerate(asg): seen[j].add(c)
    return {u for j,u in enumerate(U) if len(seen[j])==1}
  B={p:badge(p) for p in lit};B={p:v for p,v in B.items() if v[1]}
  F1=set()
  for p,v in B.items(): F1|=joint([v],{})
  how={u:'one badge' for u in F1}
  F2=set()
  if not F1:
    for p,v in B.items():
      for nm,R in extra:
        if set(R)&set(v[1]):
          f=joint([v],R);F2|=f
          for u in f: how.setdefault(u,'badge + '+nm)
    L=list(B)
    for i,p in enumerate(L):
      for q in L[i+1:]:
        if set(B[p][1])&set(B[q][1]):
          f=joint([B[p],B[q]],{});F2|=f
          for u in f: how.setdefault(u,'two badges')
  depth=1 if F1 else 2 if F2 else 0;first=sorted(F1 or F2)
  if not first:
    from freeglass2 import solve_direct
    u0=N-len(known);u1=solve_direct(sol,nb,K,lv['start'],gift=lv.get('gift',[]),detail=lv.get('detail',[]),auto=lv.get('auto',[]),nots=nots,canes=canes,ros=ros)
    if u1<u0: depth=3
  h=hops(nb,list(lv['start']))
  near=min((h.get(u,99) for u in first),default=None)
  return dict(depth=depth,n1=len(F1),n2=len(F2),first=first[:6],how=[how[u] for u in first[:6]],near=near,spread=cluster_spread(nb,list(lv['start'])),lit=len(lv['start']))
if __name__=='__main__':
  for f in sys.argv[1:]:
    lv=json.load(open(f));print(lv['id'],lv.get('tier'),ease(lv))
