"""add_auto.py in.json out.json [share=0.40] [seeds=30] [tier=1]: designed autofill in CLUSTERS OF VARIED SIZE, scattered over the picture. Marks about `share` of the panes as `auto`: the game
reveals a cluster by itself as soon as ONE neighbouring pane is locked (chained inside the cluster). No hard cap on chain length: cluster sizes come from the tier (Clear mostly 2-10, Tinted 2-6,
Stained 2-4, Jewel 1-3). Clusters never touch each other (so they are not chained together) and never touch a lit start, so an untouched level settles at exactly its lit starts and the player
triggers every cluster with a tap. Clusters are grown compactly and placed by farthest-point sampling. The picture and the start set never change; auto panes only add information.
Best seed = closest to wanted share, then fewest forced autofills, then best spread. Records metrics (auto, auto_share, max/mean chain, settle, ...)."""
import sys, json, math, random, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from freeglass2 import solve
from autofill import simulate, tap_stats
SIZES={1:[2,3,4,5,6,8,10],2:[2,3,4,5,6],3:[2,2,3,3,4],4:[1,2,2,3]}
def build(sol,nb,start,skip,cen,want,maxcomp,rnd,sizes):
  N=len(sol); auto=set(); st=set(start); bad=set(skip)|st|{q for s in st for q in nb[s]}
  d={i:1e9 for i in range(N)}; dead=set()
  while len(auto)<want:
    cand=[i for i in range(N) if i not in bad and i not in auto and i not in dead and not any(q in auto for q in nb[i])]
    if not cand: break
    cand.sort(key=lambda i:-(d[i]+rnd.random()*0.5)); placed=False
    for s in cand[:40]:
      cl=[s]; t=rnd.choice(sizes)
      while len(cl)<t:
        ext=list({q for c in cl for q in nb[c] if q not in cl and q not in bad and q not in auto and not any(r in auto for r in nb[q])})
        if not ext: break
        mx=sum(cen[c][0] for c in cl)/len(cl); my=sum(cen[c][1] for c in cl)/len(cl)
        cl.append(min(ext,key=lambda q:math.dist(cen[q],(mx,my))+rnd.random()*0.01))
      auto|=set(cl); placed=True
      for i in range(N): d[i]=min(d[i],min(math.dist(cen[i],cen[c]) for c in cl))
      break
    if not placed: break
  return sorted(auto)
def main(a,b,share=0.40,seeds=30,tier=None):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); N=len(sol); start=lv['start']; tier=int(tier) if tier else lv.get('tier',1); maxcomp=99
  skip=set(gift)|set(det); body=N-len(skip); want=round(share*body)
  cen=[Polygon(p['p']).centroid.coords[0] for p in lv['pieces']]; best=None
  for sd in range(int(seeds)):
    rnd=random.Random(sd); sizes=SIZES[tier]
    auto=build(sol,nb,start,skip,cen,want,maxcomp,rnd,sizes)
    unk=solve(sol,nb,K,start,gift=gift,detail=det,auto=auto); af=[]
    if unk: af,unk=simulate(sol,nb,K,start,gift=gift,detail=det,auto=auto)
    ts=tap_stats(sol,nb,K,start,gift,det,auto); ac=set(auto)
    nn=[min(math.dist(cen[i],cen[j]) for j in auto if j!=i) for i in auto]; spread=sum(nn)/max(1,len(nn))
    key=(unk,abs(len(auto)-want)//2,len(af),ts['stalls'],-spread)
    print('seed',sd,'auto',len(auto),'forced',len(af),'unsolved',unk,'max_chain',ts['max_chain'],'mean',ts['mean_chain'],'settle',ts['settle'],flush=True)
    if best is None or key<best[0]: best=(key,auto,af,ts)
  key,auto,af,ts=best; lv['auto']=auto; m=lv['metrics']; m['auto']=len(auto); m['auto_share']=round(len(auto)/body,4); m['autofills']=len(af); m['autofill_share']=round(len(af)/body,4)
  m['starts']=len(start); m['lit_share']=round(len(start)/body,4); m['max_chain']=ts['max_chain']; m['mean_chain']=ts['mean_chain']; m['max_depth']=ts['max_depth']; m['settle']=ts['settle']; m['taps']=ts['taps']; m['chains']=ts['chains']; m['stalls']=ts['stalls']
  json.dump(lv,open(b,'w')); print('panes',N,'body',body,'starts',len(start),'auto',len(auto),'%.1f%%'%(100*len(auto)/body),'forced autofill',len(af),'unsolved',key[0],ts)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:6]))
