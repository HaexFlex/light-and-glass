"""add_auto.py in.json out.json [share=0.38] [seeds=30] [maxcomp=3]: designed autofill, SMALL and SCATTERED. Marks about `share` of the panes as `auto`: the game reveals them by itself as soon as
one neighbour is locked (chained). Auto panes come in small clusters (connected groups of 1..maxcomp panes, mostly 2-3) that never touch each other, never touching a lit start pane, and are loaded so that
one player tap sets off at most 3 auto panes in total (no pane touches clusters of more than 3 auto panes altogether), an untouched level settles at exactly its lit starts, and the panes between clusters must be placed by the player (worked out by logic).
Clusters are placed by farthest-point sampling so they are spread evenly. The picture and the start set are never changed; auto panes only add information, so the level stays solvable.
Best seed = closest to the wanted share, then fewest forced autofills, then best spread. Records metrics (auto, auto_share, max_chain, settle, ...)."""
import sys, json, math, random, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from freeglass2 import solve
from autofill import simulate, tap_stats
def load_ok(auto,nb,N,cap):
  """clusters = connected groups of auto panes; a player tap on pane x sets off every cluster touching x -> their total size must be <= cap for every x"""
  cid={}; size=[]
  for a in auto:
    if a in cid: continue
    st=[a]; cid[a]=len(size); c=0
    while st:
      x=st.pop(); c+=1
      for y in nb[x]:
        if y in auto and y not in cid: cid[y]=len(size); st.append(y)
    size.append(c)
  if size and max(size)>cap: return False
  for x in range(N):
    if x in auto: continue
    seen={cid[y] for y in nb[x] if y in auto}
    if sum(size[c] for c in seen)>cap: return False
  return True
def build(sol,nb,start,skip,cen,want,maxcomp,rnd,sizes,cap=3):
  N=len(sol); auto=set(); st=set(start); bad=set(skip)|st|{q for s in st for q in nb[s]}
  d={i:1e9 for i in range(N)}; dead=set()
  while len(auto)<want:
    cand=[i for i in range(N) if i not in bad and i not in auto and i not in dead and not any(q in auto for q in nb[i])]
    if not cand: break
    cand.sort(key=lambda i:-(d[i]+rnd.random()*0.5)); placed=False
    for s in cand[:40]:
      if not load_ok(auto|{s},nb,N,cap): dead.add(s); continue
      cl=[s]; t=rnd.choice(sizes)
      while len(cl)<t:
        ext=[q for c in cl for q in nb[c] if q not in cl and q not in bad and q not in auto and not any(r in auto for r in nb[q])]
        rnd.shuffle(ext); g=False
        for q in ext:
          if load_ok(auto|set(cl)|{q},nb,N,cap): cl.append(q); g=True; break
        if not g: break
      auto|=set(cl); placed=True
      for i in range(N): d[i]=min(d[i],min(math.dist(cen[i],cen[c]) for c in cl))
      break
    if not placed: break
  return sorted(auto)
def main(a,b,share=0.38,seeds=30,maxcomp=3):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); N=len(sol); start=lv['start']; maxcomp=int(maxcomp)
  skip=set(gift)|set(det); body=N-len(skip); want=round(share*body)
  cen=[Polygon(p['p']).centroid.coords[0] for p in lv['pieces']]; best=None
  for sd in range(int(seeds)):
    rnd=random.Random(sd); sizes=[[2,3,3],[2,2,3],[1,2,3],[1,2],[2,2],[1,1,2],[2,3]][sd%7][:]
    auto=build(sol,nb,start,skip,cen,want,maxcomp,rnd,[min(x,maxcomp) for x in sizes])
    unk=solve(sol,nb,K,start,gift=gift,detail=det,auto=auto); af=[]
    if unk: af,unk=simulate(sol,nb,K,start,gift=gift,detail=det,auto=auto)
    ts=tap_stats(sol,nb,K,start,gift,det,auto); ac=set(auto)
    nn=[min(math.dist(cen[i],cen[j]) for j in auto if j!=i) for i in auto]; spread=sum(nn)/max(1,len(nn))
    key=(unk,abs(len(auto)-want)//2,len(af),ts['stalls'],-spread)
    print('seed',sd,'auto',len(auto),'forced',len(af),'unsolved',unk,'max_chain',ts['max_chain'],'settle',ts['settle'],flush=True)
    if best is None or key<best[0]: best=(key,auto,af,ts)
  key,auto,af,ts=best; lv['auto']=auto; m=lv['metrics']; m['auto']=len(auto); m['auto_share']=round(len(auto)/body,4); m['autofills']=len(af); m['autofill_share']=round(len(af)/body,4)
  m['starts']=len(start); m['lit_share']=round(len(start)/body,4); m['max_chain']=ts['max_chain']; m['max_depth']=ts['max_depth']; m['settle']=ts['settle']; m['taps']=ts['taps']; m['chains']=ts['chains']; m['stalls']=ts['stalls']
  json.dump(lv,open(b,'w')); print('panes',N,'body',body,'starts',len(start),'auto',len(auto),'%.1f%%'%(100*len(auto)/body),'forced autofill',len(af),'unsolved',key[0],ts)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:6]))
