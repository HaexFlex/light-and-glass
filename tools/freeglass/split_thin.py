"""split_thin.py in.json out.json [maxaspect=3.0] [seed=0]: cut thin, long panes into shorter pieces (aspect <= maxaspect), same colour, picture unchanged.
Aspect of a pane = length / width, width = min(minimum-rotated-rectangle short side, 2*area/perimeter) (so thin curved bands count too).
A thin pane is cut into k = ceil(aspect/maxaspect) pieces by a k-means (Lloyd) partition of its interior seeded along its long axis (straight bisector cuts); cut points are inserted into
the neighbouring outlines so every border stays shared. A cut is kept only if all pieces are single polygons and the whole map still passes the geometry check (no ambiguous contacts, no spikes).
New pieces are appended at the end (existing indices never move, detail/gift panes are never cut). start/auto are reset: run rework.py afterwards."""
import sys, json, math, os, random
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon, Point, MultiPoint
from shapely.ops import unary_union
import freeglass3
from freeglass3 import adjacency, check, ring, export, spikes_of, angles
def metrics(g):
  from shapely.ops import polylabel
  r=g.minimum_rotated_rectangle; c=list(r.exterior.coords)[:4]; a=math.dist(c[0],c[1]); b=math.dist(c[1],c[2]); L0,W0=max(a,b),max(min(a,b),1e-6)
  pl=polylabel(g,2e-4); rin=max(g.exterior.distance(pl),1e-6); W=2*rin; asp=max(L0/W0,g.area/(W*W)); return asp,asp*W,W,c
def axis(g):
  _,L,W,c=metrics(g); a=math.dist(c[0],c[1]); b=math.dist(c[1],c[2])
  p,q=(c[0],c[1]) if a>=b else (c[1],c[2]); d=np.array([q[0]-p[0],q[1]-p[1]]); d/=np.linalg.norm(d); return np.array(g.centroid.coords[0]),d,L
def parts(g,k,rnd):
  ctr,d,L=axis(g); minx,miny,maxx,maxy=g.bounds
  xs=np.linspace(minx,maxx,60); ys=np.linspace(miny,maxy,60); pts=np.array([(x,y) for x in xs for y in ys if g.contains(Point(x,y))])
  if len(pts)<k*4: return None
  t=(pts-ctr)@d; qs=np.linspace(t.min(),t.max(),2*k+1)[1::2]; C=np.array([pts[np.argmin(abs(t-q))] for q in qs],float)
  for _ in range(25):
    lab=np.argmin(((pts[:,None,:]-C[None])**2).sum(2),1)
    C2=np.array([pts[lab==i].mean(0) if (lab==i).any() else C[i] for i in range(k)])
    if np.allclose(C2,C): break
    C=C2
  cells=[]
  big=MultiPoint([tuple(c) for c in C]).buffer(10)
  from shapely.ops import voronoi_diagram
  vd=voronoi_diagram(MultiPoint([tuple(c) for c in C]),envelope=g.buffer(1).envelope)
  out=[]
  for cell in vd.geoms:
    i=min(range(k),key=lambda j:cell.distance(Point(*C[j])) if True else 0)
    x=g.intersection(cell)
    if x.is_empty: return None
    if x.geom_type!='Polygon':
      ps=[y for y in getattr(x,'geoms',[]) if y.geom_type=='Polygon' and y.area>1e-9]
      if len(ps)!=1: return None
      x=ps[0]
    out.append(x)
  V=ring(g); fixed=[]
  for x in out:
    r=[]
    for p in ring(x):
      if not any(math.dist(p,v)<1e-9 for v in V):
        near=[v for v in V if math.dist(p,v)<0.011]
        if near: p=min(near,key=lambda v:math.dist(p,v))
      if not r or math.dist(r[-1],p)>1e-9: r.append(p)
    if len(r)>1 and math.dist(r[0],r[-1])<1e-9: r.pop()
    if len(r)<3: return None
    q=Polygon(r)
    if not q.is_valid or q.area<1e-7: return None
    fixed.append(q)
  return fixed
def insert_pts(poly,pts,tol=2e-6):
  r=ring(poly); out=[]
  for i,a in enumerate(r):
    b=r[(i+1)%len(r)]; out.append(a); ins=[]
    for p in pts:
      if math.dist(p,a)<tol or math.dist(p,b)<tol: continue
      ab=(b[0]-a[0],b[1]-a[1]); L2=ab[0]**2+ab[1]**2
      if L2==0: continue
      t=((p[0]-a[0])*ab[0]+(p[1]-a[1])*ab[1])/L2
      if 0<t<1 and math.dist(p,(a[0]+t*ab[0],a[1]+t*ab[1]))<tol: ins.append((t,p))
    out+=[p for _,p in sorted(ins)]
  return Polygon(out)
FAIL={'parts':0,'check':0,'angle':0,'aspect':0}
def main(a,b,maxaspect=3.0,seed=0):
  maxaspect=float(maxaspect)
  lv=json.load(open(a)); G=[Polygon(p['p']) for p in lv['pieces']]; sol=list(lv['sol']); skip=set(lv.get('gift',[]))|set(lv.get('detail',[])); rnd=random.Random(int(seed))
  A=1/lv.get('aspect',1); freeglass3.set_frame(1.0,A)
  ok0,nb0,v0=check(G); print('before',len(G),v0)
  done=0; tried=0; bad=set()
  for asp,i in [x for _p in range(3) for x in sorted([(metrics(g)[0],i) for i,g in enumerate(G) if i not in skip and i not in bad],reverse=True)[:400] if x[0]>maxaspect]:
    if asp<=maxaspect or i in bad or i>=len(G): continue
    asp=metrics(G[i])[0]
    if asp<=maxaspect: continue
    tried+=1; g=G[i]; cut=False
    for k in range(int(math.ceil(asp/maxaspect)),int(math.ceil(asp/maxaspect))+3):
      ps=parts(g,k,rnd)
      if not ps or len(ps)<2: FAIL['parts']+=1; continue
      pts=[tuple(c) for p in ps for c in ring(p)]
      H=list(G); H[i]=ps[0]; H+=ps[1:]
      for j in range(len(G)):
        if j!=i and G[j].distance(g)<1e-5: H[j]=insert_pts(G[j],pts)
      try: H2,_=export(H)
      except Exception: FAIL['check']+=1; continue
      ok,nb,v=check(H2)
      if not ok or any(not x for x in nb):
        FAIL['check']+=1
        if FAIL['check']<6: print('  fail',i,round(asp,1),k,{kk:vv for kk,vv in v.items() if kk in('ambiguous_contacts','spikes','invalid_polys','coverage_err')},[j for j,x in enumerate(nb) if not x])
      elif v['min_angle_deg']<min(10.0,v0['min_angle_deg']): FAIL['angle']+=1
      elif max(metrics(p)[0] for p in H2[-(len(ps)-1):]+[H2[i]])>maxaspect*1.6: FAIL['aspect']+=1
      if ok and not any(not x for x in nb) and v['min_angle_deg']>=min(10.0,v0['min_angle_deg']) and max(metrics(p)[0] for p in H2[-(len(ps)-1):]+[H2[i]])<=maxaspect*1.6:
        G=H2; sol+= [sol[i]]*(len(ps)-1); done+=1; cut=True; break
    if not cut: bad.add(i)
  ok,nb,v=check(G); print('fail reasons',FAIL);print('cut',done,'of',tried,'thin panes ->',len(G),'panes',v,'worst aspect',round(max(metrics(g)[0] for k,g in enumerate(G) if k not in skip),2))
  old=lv['pieces']; P=[]
  for i,g in enumerate(G):
    p=dict(old[i]) if i<len(old) and 'detail' in old[i] else {}
    r=ring(g); p['p']=[list(x) for x in r]
    pp=g.representative_point(); 
    from shapely.ops import polylabel
    pl=polylabel(g,1e-4); p['pole']=[round(pl.x,5),round(pl.y,5)]; p['rin']=round(g.exterior.distance(pl),5); P.append(p)
  lv['pieces']=P; lv['sol']=sol; lv['nb']=nb
  for k in ('auto',): lv.pop(k,None)
  lv['metrics']=dict(lv.get('metrics',{}),pieces=len(G),min_angle_deg=v['min_angle_deg'],spikes=v['spikes'],ambiguous_contacts=v['ambiguous_contacts'],corner_touches=v['corner_touches'],min_shared_border=v['min_shared_border'])
  json.dump(lv,open(b,'w'))
if __name__=='__main__': main(sys.argv[1],sys.argv[2],*sys.argv[3:5])
