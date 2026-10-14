import itertools, json
LEVELS = {
 "tutorial": dict(name="First Light", colors=["#2b4a7a","#e0566e"], img=[
  "BRBRB","RRRRR","RRRRR","BRRRB","BBRBB"], key="BR"),
 "main": dict(name="Garden Rose", colors=["#3d6fb0","#e46c8f","#f2c14e","#4f9a5a"], img=[
  "BBPPPPBB","BPPYYPPB","BPYYYYPB","BPPYYPPB","BBPPPPBB","BGBGBBBB","BGGGBBGB","GGGGGGGG"], key="BPYG"),
}
def grid(L): return [[L["key"].index(ch) for ch in r] for r in L["img"]]
def nbrs(n,r,c):
  for dr,dc in((1,0),(-1,0),(0,1),(0,-1)):
    if 0<=r+dr<n and 0<=c+dc<n: yield r+dr,c+dc
def clueval(g,r,c): return sum(g[a][b]==g[r][c] for a,b in nbrs(len(g),r,c))
def propagate(g,K,clues,hidden=()):
  n=len(g); D=[[set(range(K)) for _ in range(n)] for _ in range(n)]
  for (r,c) in clues: D[r][c]={g[r][c]}
  lines=[[(r,c) for c in range(n)] for r in range(n)]+[[(r,c) for r in range(n)] for c in range(n)]
  lines=[l for i,l in enumerate(lines) if i not in hidden]
  while True:
    ch=False
    for ln in lines:
      ms=[g[r][c] for r,c in ln]
      poss=[set() for _ in ln]
      for p in set(itertools.permutations(ms)) if n<=5 else perms(ms,[D[r][c] for r,c in ln]):
        if all(p[i] in D[r][c] for i,(r,c) in enumerate(ln)):
          for i in range(n): poss[i].add(p[i])
      for i,(r,c) in enumerate(ln):
        if poss[i]!=D[r][c]: D[r][c]=poss[i]; ch=True
    for (r,c) in clues:
      col=g[r][c]; k=clueval(g,r,c); nb=list(nbrs(n,r,c))
      sure=[x for x in nb if D[x[0]][x[1]]=={col}]; maybe=[x for x in nb if col in D[x[0]][x[1]]]
      if len(sure)==k:
        for a,b in maybe:
          if (a,b) not in sure: D[a][b].discard(col); ch=True
      if len(maybe)==k:
        for a,b in maybe:
          if D[a][b]!={col}: D[a][b]={col}; ch=True
    if not ch: break
  return D
def perms(ms,doms):
  from collections import Counter
  cnt=Counter(ms); out=[]
  def rec(i,acc):
    if i==len(ms): out.append(tuple(acc)); return
    for col in list(cnt):
      if cnt[col] and col in doms[i]:
        cnt[col]-=1; acc.append(col); rec(i+1,acc); acc.pop(); cnt[col]+=1
  rec(0,[]); return out
def unknown(D): return sum(len(x)>1 for row in D for x in row)
def solved(D): return unknown(D)==0
res={}
for key,L in LEVELS.items():
  g=grid(L); n=len(g); K=len(L["colors"])
  import random; best=None
  for seed in range(40 if n>5 else 1):
    rnd=random.Random(seed); hidden=set(rnd.sample(range(2*n),7)) if n>5 else set(); clues=[]
    while not solved(propagate(g,K,clues,hidden)):
      b=min(((r,c) for r in range(n) for c in range(n) if (r,c) not in clues), key=lambda x:(unknown(propagate(g,K,clues+[x],hidden)),rnd.random()))
      clues.append(b)
    for x in list(clues):
      t=[y for y in clues if y!=x]
      if solved(propagate(g,K,t,hidden)): clues=t
    for i in range(2*n):  # hide more lines if still solvable
      if i not in hidden and solved(propagate(g,K,clues,hidden|{i})): hidden.add(i)
    if n>5 and not (3<=len(clues)<=12): continue
    sc=abs(len(clues)-6)+abs(len(hidden)-6)
    if best is None or sc<best[0]: best=(sc,clues,hidden)
  _,clues,hidden=best
  # every propagation step is a sound deduction, so full solve => unique solution
  assert solved(propagate(g,K,clues,hidden)); print("hidden lines",sorted(hidden))
  print(key,"clues",len(hidden),"hidden",len(clues),clues)
  res[key]=dict(name=L["name"],n=n,colors=L["colors"],sol=g,
    clues=[[r,c,clueval(g,r,c)] for r,c in clues],
    rows=[None if i in hidden else [row.count(k) for k in range(K)] for i,row in enumerate(g)],
    cols=[None if n+c in hidden else [ [g[r][c] for r in range(n)].count(k) for k in range(K)] for c in range(n)])
  print("start unknown w/o clues:",unknown(propagate(g,K,[])))
json.dump([res["tutorial"],res["main"]],open("levels.json","w"))
