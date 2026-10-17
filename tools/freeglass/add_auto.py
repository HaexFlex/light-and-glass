"""add_auto.py in.json out.json [share=0.40] [seeds=8]: designed autofill. Marks `share` of the non-gift/non-detail/non-start panes as `auto`:
the game reveals them by itself (chained, same animation/pacing as autofill) as soon as one neighbour is locked, even when logic could deduce them.
Picks are spread evenly (farthest-point sampling over pane centres, random first pick per seed); the level must still be solved by the player's deductions plus those reveals
(solver mirrors the game: auto panes are lit once a neighbour is lit). Fewest forced autofills wins, ties -> best spread. The picture and the start set are never changed."""
import sys, json, math, random, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from freeglass2 import solve
from autofill import simulate
def main(a,b,share=0.40,seeds=8):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); N=len(sol); start=lv['start']
  skip=set(gift)|set(det)|set(start); pool=[i for i in range(N) if i not in skip]; body=N-len(set(gift)|set(det)); want=round(share*body)
  cen=[Polygon(p['p']).centroid.coords[0] for p in lv['pieces']]; best=None
  for sd in range(int(seeds)):
    rnd=random.Random(sd); pick=[rnd.choice(pool)]; d={i:math.dist(cen[i],cen[pick[0]]) for i in pool}
    while len(pick)<want:
      i=max((q for q in pool if q not in pick),key=lambda q:d[q]+rnd.random()*1e-3); pick.append(i)
      for q in pool: d[q]=min(d[q],math.dist(cen[q],cen[i]))
    auto=sorted(pick); unk=solve(sol,nb,K,start,gift=gift,detail=det,auto=auto); af=[]
    if unk: af,unk=simulate(sol,nb,K,start,gift=gift,detail=det,auto=auto)
    mind=min(d[q] for q in pool if q not in pick); key=(unk,len(af),-mind)
    print('seed',sd,'auto',len(auto),'autofill',len(af),'unsolved',unk,flush=True)
    if best is None or key<best[0]: best=(key,auto,af)
  key,auto,af=best; lv['auto']=auto; m=lv['metrics']; m['auto']=len(auto); m['auto_share']=round(len(auto)/body,4); m['autofills']=len(af); m['autofill_share']=round(len(af)/body,4)
  m['starts']=len(start); m['lit_share']=round(len(start)/body,4)
  json.dump(lv,open(b,'w')); print('panes',N,'body',body,'starts',len(start),'auto',len(auto),'%.1f%%'%(100*len(auto)/body),'forced autofill',len(af),'unsolved',key[0])
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:5]))
