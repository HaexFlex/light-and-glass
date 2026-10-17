"""Autofill-aware solvability (mirrors afPick/afRun in src/template.html exactly).
A player who places every pane that can be worked out reaches a fixpoint; if panes remain, the game reveals ONE pane:
candidates = unresolved, unlit panes with a lit neighbour (at most 48, evenly spaced by index); score = how many panes end up lit after revealing it
and closing the deductions; highest score wins, ties -> lowest index.  simulate() returns (autofill panes in order, unsolved count)."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass2 import line_poss
def _close(sol,nb,K,D,lit,gift=frozenset(),det=frozenset(),auto=frozenset()):   # gift: known from the start; det (detail panes): colour becomes known once a neighbour is lit; neither is ever lit itself
  N=len(sol); skip=gift|det
  while True:
    ch=False
    for d in det:
      if len(D[d])>1 and any(q in lit for q in nb[d]): D[d]={sol[d]}; ch=True
    for p in list(lit):
      cnt=[0]*K
      for q in nb[p]: cnt[sol[q]]+=1
      Pp=line_poss([D[q] for q in nb[p]],cnt)
      for ii,q in enumerate(nb[p]):
        if Pp[ii]!=D[q]: D[q]=Pp[ii]; ch=True
    for q in range(N):
      if len(D[q])==1 and q not in lit and q not in skip: lit.add(q); ch=True
    for a in auto:   # designed autofill: revealed as soon as one neighbour is lit
      if a not in lit and any(q in lit for q in nb[a]): D[a]={sol[a]}; lit.add(a); ch=True
    if not ch: return
def simulate(sol,nb,K,start,cap=None,verbose=False,gift=(),detail=(),auto=()):   # cap=None: no limit (chained autofills are a feature); cap is only a search bound for callers
  N=len(sol); gift=frozenset(gift); det=frozenset(detail); auto=frozenset(auto); skip=gift|det; D=[set(range(K)) for _ in range(N)]; lit=set(start)
  for s in start: D[s]={sol[s]}
  for g in gift: D[g]={sol[g]}
  _close(sol,nb,K,D,lit,gift,det,auto); fills=[]
  while len(lit)<N-len(skip) and (cap is None or len(fills)<cap):
    cand=[i for i in range(N) if i not in lit and i not in skip and any(q in lit for q in nb[i])]
    use=cand if len(cand)<=48 else [cand[j*len(cand)//48] for j in range(48)]
    best,bs=-1,-1
    for i in use:
      D2=[set(d) for d in D]; l2=set(lit); D2[i]={sol[i]}; l2.add(i); _close(sol,nb,K,D2,l2,gift,det,auto)
      if len(l2)>bs: bs=len(l2); best=i
    if best<0: break
    fills.append(best); D[best]={sol[best]}; lit.add(best); _close(sol,nb,K,D,lit,gift,det,auto)
    if verbose: print('autofill',best,'lit',len(lit),'/',N,flush=True)
  return fills,N-len(skip)-len(lit)

def tap_stats(sol,nb,K,start,gift=(),detail=(),auto=()):
  """Player-effort metrics for designed autofill (mirrors the game: the player taps ONE worked-out pane at a time, lowest index first; after each tap, auto panes with a locked
  neighbour reveal by themselves, chained). Returns settle (panes locked in an untouched level = starts + auto chain), max_chain (most auto panes one tap sets off), max_depth,
  taps (player placements), chains (taps that set off >=1 auto pane), stalls (times nothing was left to tap = forced autofill needed), auto_comp_max (largest connected group of auto panes)."""
  N=len(sol); gift=frozenset(gift); det=frozenset(detail); auto=frozenset(auto); skip=gift|det; D=[set(range(K)) for _ in range(N)]; lit=set(start)
  for s in start: D[s]={sol[s]}
  for g in gift: D[g]={sol[g]}
  def cascade():
    n=0; depth=0
    while True:
      new=[a for a in sorted(auto) if a not in lit and any(q in lit for q in nb[a])]
      if not new: return n,depth
      for a in new: lit.add(a); D[a]={sol[a]}
      n+=len(new); depth+=1
  def prop():
    while True:
      ch=False
      for d in det:
        if len(D[d])>1 and any(q in lit for q in nb[d]): D[d]={sol[d]}; ch=True
      for p in list(lit):
        cnt=[0]*K
        for q in nb[p]: cnt[sol[q]]+=1
        Pp=line_poss([D[q] for q in nb[p]],cnt)
        for ii,q in enumerate(nb[p]):
          if Pp[ii]!=D[q]: D[q]=Pp[ii]; ch=True
      if not ch: return
  cascade(); settle=len(lit); prop(); taps=0; chains=0; mx=0; md=0; stalls=0
  while True:
    todo=[q for q in range(N) if q not in lit and q not in skip and len(D[q])==1]
    if not todo:
      left=[q for q in range(N) if q not in lit and q not in skip]
      if not left: break
      stalls+=1; q=min(q for q in left if any(x in lit for x in nb[q])); D[q]={sol[q]}; lit.add(q); n,d=cascade(); prop(); continue
    q=todo[0]; lit.add(q); taps+=1; n,d=cascade(); prop()
    if n: chains+=1
    mx=max(mx,n); md=max(md,d)
  seen=set(); comp=0
  for a in auto:
    if a in seen: continue
    st=[a]; seen.add(a); c=0
    while st:
      x=st.pop(); c+=1
      for y in nb[x]:
        if y in auto and y not in seen: seen.add(y); st.append(y)
    comp=max(comp,c)
  return dict(settle=settle,max_chain=mx,max_depth=md,taps=taps,chains=chains,stalls=stalls,auto_comp_max=comp)
