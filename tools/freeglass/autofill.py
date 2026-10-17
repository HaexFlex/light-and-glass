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
