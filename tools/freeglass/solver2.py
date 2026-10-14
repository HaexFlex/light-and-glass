"""Light & Glass level generator/verifier.
Solution grid = picture flipped vertically (the window shows it upside down; the floor projection flips it back).
Deductions used (all sound, no guessing):
 * line reasoning: for each row/column with visible colour counts, every completion consistent with
   current domains is enumerated implicitly (DP over count vectors); a colour is kept only if some completion uses it.
 * number clues: clue pane (colour given) with k = #orthogonal neighbours of same colour.
Iterate to fixpoint. If every pane ends with one colour -> unique solution reachable without guessing."""
import json, random, sys, time
PICS = {
 "heart": dict(name="First Light", colors={"B":"#2b4a7a","R":"#e0566e"}, img=[
  "BRBRB","RRRRR","RRRRR","BRRRB","BBRBB"]),
 "rose": dict(name="Garden Rose", colors={"B":"#5b8fd0","P":"#f08db0","R":"#c8325e","G":"#4f9a5a","L":"#8a5a3c"}, img=[
  "BBBBBBBBBBBB",
  "BBBBPPPPBBBB",
  "BBBPPRRPPBBB",
  "BBPPRRPRRPBB",
  "BBPRRPPPRPBB",
  "BBPRPPRRRPBB",
  "BBPPRRRPPPBB",
  "BBBBPPPPBBBB",
  "BBGGBBGBBBBB",
  "BGGGGBGBGGBB",
  "BBBGGBGGGBBB",
  "LLLLLLLLLLLL"]),
 "swan": dict(name="Swan at Sunset", colors={"P":"#7a5aa6","O":"#f08a4b","Y":"#ffd45e","W":"#f6f1ea","D":"#24476e"}, img=[
  "PPPPPPPPPPPPPP",
  "PPPPPPPPPPPPPP",
  "PPPPPPPPPYYPPP",
  "OOOOOOOOYYYYOO",
  "OOOWWOOOYYYYOO",
  "OOOOWOOOOYYOOO",
  "OOOOWOOOOOOOOO",
  "OOOWOOOOOOOOOO",
  "OOOWWWWWWWWOOO",
  "DDDWWWWWWWWWDD",
  "DDDDWWWWWWWDDD",
  "DDDDDDDDDYYDDD",
  "DDYYDDDDDDYYDD",
  "DDDDDDDDDDDDDD"]),
 "balloon": dict(name="Hot-Air Balloon", colors={"S":"#7cc0e8","R":"#e2504a","Y":"#f6c445","K":"#8a5a3c","W":"#fbf7f0"}, img=[
  "SSSSSSSSSSSSS",
  "SSSSRRYRRSSSS",
  "SSSRRYYYRRSSS",
  "SSRRYYRYYRRSS",
  "SSRYYRRRYYRSS",
  "SSRYYRRRYYRSS",
  "SSRRYYRYYRRSS",
  "SSSRRYYYRRSSS",
  "SSSSRRYRRSSSS",
  "SSSSSKSKSSSSS",
  "SWWSSKKKSSSSS",
  "WWWWSKKKSSWWW",
  "WWWSSSSSSWWWW"]),
}
def nbrs(n,r,c):
  for dr,dc in((1,0),(-1,0),(0,1),(0,-1)):
    if 0<=r+dr<n and 0<=c+dc<n: yield r+dr,c+dc
def clueval(g,r,c): return sum(g[a][b]==g[r][c] for a,b in nbrs(len(g),r,c))
def line_poss(doms,counts):
  K=len(counts); n=len(doms); F=[{tuple([0]*K)}]
  for i in range(n):
    nx=set()
    for s in F[-1]:
      for k in doms[i]:
        if s[k]<counts[k]: t=list(s);t[k]+=1;nx.add(tuple(t))
    F.append(nx)
  G=[None]*(n+1); G[n]={tuple(counts)}&F[n]; poss=[set() for _ in range(n)]
  for i in range(n-1,-1,-1):
    gi=set()
    for s in F[i]:
      for k in doms[i]:
        if s[k]<counts[k]:
          t=list(s);t[k]+=1
          if tuple(t) in G[i+1]: gi.add(s);poss[i].add(k)
    G[i]=gi
  return poss
def propagate(g,K,clues,hidden):
  n=len(g); D=[[set(range(K)) for _ in range(n)] for _ in range(n)]
  for (r,c) in clues: D[r][c]={g[r][c]}
  lines=[[(r,c) for c in range(n)] for r in range(n)]+[[(r,c) for r in range(n)] for c in range(n)]
  act=[(ln,[ [g[r][c] for r,c in ln].count(k) for k in range(K)]) for i,ln in enumerate(lines) if i not in hidden]
  while True:
    ch=False
    for ln,cnt in act:
      P=line_poss([D[r][c] for r,c in ln],cnt)
      for i,(r,c) in enumerate(ln):
        if P[i]!=D[r][c]: D[r][c]=P[i]; ch=True
    for (r,c) in clues:
      col=g[r][c]; k=clueval(g,r,c); nb=list(nbrs(n,r,c))
      sure=[x for x in nb if D[x[0]][x[1]]=={col}]; maybe=[x for x in nb if col in D[x[0]][x[1]]]
      if len(sure)==k:
        for a,b in maybe:
          if (a,b) not in sure: D[a][b].discard(col); ch=True
      if len(maybe)==k:
        for a,b in maybe:
          if D[a][b]!={col}: D[a][b]={col}; ch=True
    if not ch: return D
def unknown(D): return sum(len(x)>1 for row in D for x in row)
def gen(key,seeds=3,hide_frac=.35):
  P=PICS[key]; keys=list(P["colors"]); img=P["img"][::-1]  # flipped!
  g=[[keys.index(ch) for ch in row] for row in img]; n=len(g); K=len(keys); best=None
  for seed in range(seeds):
    rnd=random.Random(seed)
    hidden=set(rnd.sample(range(2*n),int(2*n*hide_frac))) if n>5 else {0,3}
    clues=[]
    D=propagate(g,K,clues,hidden)
    while unknown(D):
      cand=[(r,c) for r in range(n) for c in range(n) if len(D[r][c])>1]; rnd.shuffle(cand)
      b=min(cand[:25],key=lambda x:unknown(propagate(g,K,clues+[x],hidden)))
      clues.append(b); D=propagate(g,K,clues,hidden)
    for x in list(clues):
      t=[y for y in clues if y!=x]
      if not unknown(propagate(g,K,t,hidden)): clues=t
    for i in rnd.sample(range(2*n),2*n):
      if i not in hidden and not unknown(propagate(g,K,clues,hidden|{i})): hidden.add(i)
    sc=len(clues)-0.3*len(hidden)
    print(key,"seed",seed,"clues",len(clues),"hidden",len(hidden),flush=True)
    if best is None or sc<best[0]: best=(sc,clues,hidden)
  _,clues,hidden=best
  assert not unknown(propagate(g,K,clues,hidden))
  return dict(id=key,name=P["name"],n=n,colors=[P["colors"][k] for k in keys],sol=g,
    clues=[[r,c,clueval(g,r,c)] for r,c in clues],
    rows=[None if i in hidden else [row.count(k) for k in range(K)] for i,row in enumerate(g)],
    cols=[None if n+c in hidden else [[g[r][c] for r in range(n)].count(k) for k in range(K)] for c in range(n)])
if __name__=="__main__":
  out=[]
  for k in ["heart","rose","swan","balloon"]:
    t=time.time(); out.append(gen(k)); print(k,"done %.1fs"%(time.time()-t),flush=True)
  json.dump(out,open("levels2.json","w"))
