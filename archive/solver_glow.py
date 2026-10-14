"""Glow rule set solver/generator.
Rules: no edge counts. A lit pane shows, per colour, how many of its 8 neighbours have that colour.
Cascade (option B): a pane's numbers appear once it is lit (start panes, or correctly placed by the player).
Deduction engine (sound, no guessing): for each lit pane, enumerate every colouring of its unknown neighbours
consistent with current domains and its per-colour counts (DP over count vectors); keep only colours that occur.
Newly determined panes become lit (their numbers join) -> repeat to fixpoint. Fully determined => unique & no-guess.
Also reports how many start panes would be needed WITHOUT the cascade (option A)."""
import json, random, sys
sys.path.insert(0,'.')
from solver2 import line_poss
PICS={
 "glowtulip":dict(name="Little Tulip",colors={"S":"#6aa6dc","R":"#e2504a","G":"#4f9a5a"},img=[
  "SSSSSSS","SRSRSRS","SRRRRRS","SSRRRSS","SSSGSSS","SGSGSGS","GGGGGGG"]),
 "glowlight":dict(name="Lighthouse",colors={"S":"#7cb6e6","R":"#d9483f","Y":"#ffd45e","W":"#f6f1ea","D":"#24476e"},img=[
  "SSSSSSSSSSSS",
  "SSSSSRRSSSSS",
  "SSSSRRRRSSSS",
  "YYYSWYYWSYYY",
  "SSSSRRRRSSSS",
  "SSSSSWWSSSSS",
  "SSSSSRRSSSSS",
  "SSSSWWWWSSSS",
  "SSSSRRRRSSSS",
  "SSSWWWWWWSSS",
  "DDWWWWWWWWDD",
  "DDDDDDDDDDDD"]),
}
def n8(n,r,c):
  return [(r+a,c+b) for a in(-1,0,1) for b in(-1,0,1) if (a or b) and 0<=r+a<n and 0<=c+b<n]
def counts(g,r,c,K): 
  v=[0]*K
  for a,b in n8(len(g),r,c): v[g[a][b]]+=1
  return v
def solve(g,K,start,cascade=True):
  n=len(g); D=[[set(range(K)) for _ in range(n)] for _ in range(n)]
  lit=set(start)
  for r,c in start: D[r][c]={g[r][c]}
  steps=0
  while True:
    ch=False
    for (r,c) in list(lit):
      nb=n8(n,r,c); P=line_poss([D[a][b] for a,b in nb],counts(g,r,c,K))
      for i,(a,b) in enumerate(nb):
        if P[i]!=D[a][b]: D[a][b]=P[i]; ch=True
    if cascade:
      for r in range(n):
        for c in range(n):
          if len(D[r][c])==1 and (r,c) not in lit: lit.add((r,c)); ch=True
    if not ch: break
  return D,sum(len(x)>1 for row in D for x in row)
def gen(key,cascade=True,seeds=4):
  P=PICS[key]; keys=list(P["colors"]); g=[[keys.index(ch) for ch in row] for row in P["img"][::-1]]
  n=len(g); K=len(keys); best=None
  for seed in range(seeds):
    rnd=random.Random(seed); start=[]
    while True:
      D,u=solve(g,K,start,cascade)
      if not u: break
      cand=[(r,c) for r in range(n) for c in range(n) if (r,c) not in start]; rnd.shuffle(cand)
      b=min(cand[:40],key=lambda x:(solve(g,K,start+[x],cascade)[1],rnd.random())); start.append(b)
    for x in list(start):
      t=[y for y in start if y!=x]
      if not solve(g,K,t,cascade)[1]: start=t
    if best is None or len(start)<len(best): best=start
  assert not solve(g,K,best,cascade)[1]
  return g,keys,best
if __name__=="__main__":
  out=[]
  for key in PICS:
    g,keys,startA=gen(key,cascade=False,seeds=2)
    g,keys,start=gen(key,cascade=True)
    print(key,"start panes: cascade(B) =",len(start),"| no cascade(A) =",len(startA),flush=True)
    P=PICS[key]
    out.append(dict(id=key,name=P["name"],n=len(g),mode="glow",colors=[P["colors"][k] for k in keys],sol=g,start=[list(x) for x in sorted(start)]))
  json.dump(out,open("levels_glow.json","w"))
