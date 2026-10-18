"""blobify.py in.json out.json [passes=4] [seed=0]: make panes compact blobs. Any pane (not tiny, not gift/detail) with aspect>3 or solidity<0.7 (see compact.py) is split by a k-means/Voronoi cut
(straight-ish cuts across the narrow direction, seeds along the long axis, k=2.. as needed) into pieces of the SAME colour, so the picture/colour map is unchanged. Cut points are inserted into the
neighbours' outlines so borders stay shared. A cut is kept only if every piece is a single polygon, the whole map passes the geometry check (no ambiguous contacts, no spikes), the min angle stays >= min(10, before)
and the worst badness of the pieces is clearly lower than the pane's, with no piece smaller than MINPIECE. New pieces are appended (indices never move). start/auto are dropped: run rework.py afterwards (rw_level.py does)."""
import sys, json, math, os, random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
import freeglass3
from freeglass3 import check, ring, export
from split_thin import metrics, parts, insert_pts
from compact import pane, MAXASP, MINSOL, TINY
MINPIECE=0.00035
def bad(g):
  a,s,_=pane(g,0); return max(a/MAXASP,MINSOL/max(s,1e-6))
def main(a,b,passes=4,seed=0):
  lv=json.load(open(a)); G=[Polygon(p['p']) for p in lv['pieces']]; sol=list(lv['sol']); skip=set(lv.get('gift',[]))|set(lv.get('detail',[])); rnd=random.Random(int(seed))
  freeglass3.set_frame(1.0,1/lv.get('aspect',1)); ok0,nb0,v0=check(G); done=0; dead=set()
  for ps_ in range(int(passes)):
    order=sorted([(bad(g),i) for i,g in enumerate(G) if i not in skip and i not in dead and g.area>=TINY and bad(g)>1],reverse=True)
    if not order: break
    n0=done
    for _,i in order:
      g=G[i]; b0=bad(g)
      if b0<=1: continue
      k0=max(2,math.ceil(metrics(g)[0]/MAXASP)); cut=False
      for k in range(k0,k0+3):
        if g.area/k<MINPIECE: break
        ps=None; sc=1e9
        for tr in range(7):
          q=parts(g,k,rnd,pp=tr>0)
          if q and len(q)>=2 and min(p.area for p in q)>=MINPIECE:
            m=max(bad(p) for p in q)
            if m<sc: ps,sc=q,m
        if not ps or sc>=b0-0.05: continue
        pts=[tuple(c) for p in ps for c in ring(p)]; H=list(G); H[i]=ps[0]; H+=ps[1:]
        for j in range(len(G)):
          if j!=i and G[j].distance(g)<1e-5: H[j]=insert_pts(G[j],pts)
        try: H2,_=export(H)
        except Exception: continue
        ok,nb,v=check(H2)
        if ok and all(nb) and v['min_angle_deg']>=min(10.0,v0['min_angle_deg']):
          G=H2; sol+=[sol[i]]*(len(ps)-1); done+=1; cut=True; break
      if not cut: dead.add(i)
    print('pass',ps_,'cuts',done-n0,'panes',len(G),flush=True)
    if done==n0: break
  ok,nb,v=check(G); from shapely.ops import polylabel
  old=lv['pieces']; P=[]
  for i,g in enumerate(G):
    p=dict(old[i]) if i<len(old) and 'detail' in old[i] else {}
    p['p']=[list(x) for x in ring(g)]; pl=polylabel(g,1e-4); p['pole']=[round(pl.x,5),round(pl.y,5)]; p['rin']=round(g.exterior.distance(pl),5); P.append(p)
  lv['pieces']=P; lv['sol']=sol; lv['nb']=nb; lv.pop('auto',None)
  lv['metrics']=dict(lv.get('metrics',{}),pieces=len(G),min_angle_deg=v['min_angle_deg'],spikes=v['spikes'],ambiguous_contacts=v['ambiguous_contacts'],corner_touches=v['corner_touches'],min_shared_border=v['min_shared_border'])
  json.dump(lv,open(b,'w')); print('cuts',done,'panes',len(G),'min_angle',v['min_angle_deg'])
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:5])
