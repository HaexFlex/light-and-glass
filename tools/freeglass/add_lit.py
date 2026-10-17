"""add_lit.py in.json out.json [share=0.07] [seed=0]: raise the lit-start share of a feature_first level to `share` of the non-detail/non-gift panes.
Keeps the generator's minimal start set, then adds panes one at a time (farthest from every lit pane, must show >=2 neighbour colours so the badge says something),
then simulates autofill (uncapped, same rule as the game) and records starts/autofills in metrics. The picture is never changed."""
import sys, json, math, random, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from freeglass2 import solve
from autofill import simulate
def main(a,b,share=0.07,seed=0):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); N=len(sol)
  skip=set(gift)|set(det); body=N-len(skip); want=max(len(lv['start']),math.ceil(share*body))
  cen=[Polygon(p['p']).centroid.coords[0] for p in lv['pieces']]; start=list(lv['start']); rnd=random.Random(seed)
  ok=[i for i in range(N) if i not in skip and len({sol[q] for q in nb[i]})>=2 and not any(q in det for q in nb[i] if False)]
  while len(start)<want:
    best=max((i for i in ok if i not in start),key=lambda i:min(math.dist(cen[i],cen[s]) for s in start)+rnd.random()*1e-3); start.append(best)
  start=sorted(start); unk=solve(sol,nb,K,start,gift=gift,detail=det); af=[]
  if unk: af,unk=simulate(sol,nb,K,start,gift=gift,detail=det)
  m=lv['metrics']; m['starts']=len(start); m['autofills']=len(af); m['lit_share']=round(len(start)/body,4); m['autofill_share']=round(len(af)/body,4)
  lv['start']=start; json.dump(lv,open(b,'w')); print('panes',N,'body',body,'starts',len(start),'%.1f%%'%(100*len(start)/body),'autofill',len(af),'unsolved',unk)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:5]))
