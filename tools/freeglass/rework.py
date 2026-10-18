"""rework.py in.json out.json [--lit SHARE] [--auto SHARE] [--group 3] [--seeds 14]: new help layout for a finished level (picture and pane map never change).
 1. lit starts in a few SMALL LOCAL GROUPS (each group = a seed pane plus 2 close neighbours with informative badges), groups spread over the picture by farthest-point sampling,
    so the first deductions happen next to each other on one screen;
 2. designed autofill = small scattered clusters (add_auto.build: clusters <=3, never touching a start or each other, <=3 auto panes per player tap);
 3. if deduction + autofill still stalls (a forced autofill would be needed), a new local start group is added around the stalling pane and the autofill is re-picked.
Defaults come from the level's tier (lit/auto share): Clear 8%/40%, Tinted 6%/30%, Stained 4.5%/20%, Jewel 2%/8%. Records metrics like add_auto.py."""
import sys, json, math, random, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from freeglass2 import solve
from autofill import simulate, tap_stats
from add_auto import build, SIZES
TIER={1:(0.08,0.45),2:(0.06,0.30),3:(0.045,0.20),4:(0.02,0.08)}
def tier_auto_default(lv): return True   # tutorial levels use the Clear (big cluster) profile
def pick_auto(lv,start,share,seeds,cen,tier=1):
  sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); N=len(sol); skip=set(gift)|set(det); body=N-len(skip); want=round(share*body); best=None
  for sd in range(seeds):
    rnd=random.Random(sd); sizes=SIZES[tier]
    auto=build(sol,nb,start,skip,cen,want,99,rnd,sizes); unk=solve(sol,nb,K,start,gift=gift,detail=det,auto=auto); af=[]
    if unk: af,unk=simulate(sol,nb,K,start,gift=gift,detail=det,auto=auto)
    nn=[min(math.dist(cen[i],cen[j]) for j in auto if j!=i) for i in auto] if len(auto)>1 else [0]
    key=(unk,len(af),-len(auto),-sum(nn)/len(nn))
    if best is None or key<best[0]: best=(key,auto,af)
  return best
def group(lv,seed,size,cen,used,informative):
  nb=lv['nb']; g=[seed]; cand=[]
  seen={seed}; fr=[seed]
  for _ in range(2):
    nxt=[]
    for x in fr:
      for y in nb[x]:
        if y not in seen: seen.add(y); nxt.append(y)
    cand+=nxt; fr=nxt
  cand=[c for c in cand if c in informative and c not in used and c not in g]; cand.sort(key=lambda c:math.dist(cen[c],cen[seed]))
  for c in cand:
    if len(g)>=size: break
    g.append(c)
  return g
def main(a,b,lit=None,auto=None,gsize=3,seeds=14):
  lv=json.load(open(a)); sol=lv['sol']; nb=lv['nb']; N=len(sol); K=len(lv['colors']); skip=set(lv.get('gift',[]))|set(lv.get('detail',[])); body=N-len(skip)
  tl,ta=TIER.get(lv.get('tier',3),TIER[3]); lit=tl if lit is None else lit; auto_share=ta if auto is None else auto
  cen=[Polygon(p['p']).centroid.coords[0] for p in lv['pieces']]
  informative={i for i in range(N) if i not in skip and len({sol[q] for q in nb[i]})>=2}
  nstart=max(2,round(lit*body)); gsize=int(gsize); ng=max(1,round(nstart/gsize)); size=max(2,math.ceil(nstart/ng))
  stier=1 if (lv.get('set')=='tutorial' and tier_auto_default(lv)) else lv.get('tier',3)
  best=None
  for trial in range(6):
    rnd=random.Random(trial); pool=sorted(informative); first=rnd.choice(pool); centres=[first]
    while len(centres)<ng:
      centres.append(max((i for i in pool if i not in centres),key=lambda i:min(math.dist(cen[i],cen[c]) for c in centres)+rnd.random()*1e-3))
    start=[]
    for c in centres: start+=group(lv,c,size,cen,set(start),informative)
    start=list(dict.fromkeys(start))
    for it in range(10):
      r=pick_auto(lv,start,auto_share,int(seeds),cen,stier); key,au,af=r
      if key[0]==0 and not af: break
      f=af[0] if af else None
      if f is None: break
      add=group(lv,f if f in informative else (min(nb[f],key=lambda q:math.dist(cen[q],cen[f])) if nb[f] else f),size,cen,set(start),informative)
      start+= [x for x in add if x not in start]
    score=(key[0],len(af),len(start),-len(au))
    print('trial',trial,'groups',ng,'starts',len(start),'auto',len(au),'forced',len(af),'unsolved',key[0],flush=True)
    if best is None or score<best[0]: best=(score,start,au,af)
    if score[0]==0 and score[1]==0 and len(start)<=nstart+2*size: break
  _,start,au,af=best; ts=tap_stats(sol,nb,K,start,lv.get('gift',[]),lv.get('detail',[]),au)
  lv['start']=sorted(start); lv['auto']=sorted(au); m=lv['metrics']; m.update(starts=len(start),lit_share=round(len(start)/body,4),auto=len(au),auto_share=round(len(au)/body,4),autofills=len(af),autofill_share=round(len(af)/body,4),
     max_chain=ts['max_chain'],mean_chain=ts['mean_chain'],max_depth=ts['max_depth'],settle=ts['settle'],taps=ts['taps'],chains=ts['chains'],stalls=ts['stalls'],pieces=N)
  json.dump(lv,open(b,'w')); print('panes',N,'starts',len(start),'groups',ng,'auto',len(au),'%.1f%%'%(100*len(au)/body),'forced',len(af),ts)
if __name__=='__main__':
  a=sys.argv; kw={}
  for k in ('lit','auto','group','seeds'):
    if '--'+k in a: kw[{'group':'gsize'}.get(k,k)]=float(a[a.index('--'+k)+1])
  main(a[1],a[2],**kw)
