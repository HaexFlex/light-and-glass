"""Free Glass: arbitrary stained-glass pane graphs.
Pipeline: vector picture (coloured shapely regions, painter's order) -> per-region Poisson seeds + clipped Lloyd/Voronoi
-> merge too-small pieces -> geometric adjacency (shared border length >= LMIN) -> cascade solver -> start-pane search.
Coordinates: unit square, upright, y down. Output is flipped vertically for the window (floor flips back)."""
import json, math, random, sys
import numpy as np
from shapely.geometry import Point, Polygon, MultiPoint, LineString, box
from shapely.ops import unary_union, polylabel
from shapely import affinity
from shapely.ops import voronoi_diagram
sys.path.insert(0,'.')
from solver2 import line_poss
UNIT=box(0,0,1,1); LMIN=0.006
def ell(cx,cy,rx,ry,rot=0): return affinity.rotate(affinity.scale(Point(cx,cy).buffer(1,resolution=48),rx,ry),rot,origin=(cx,cy))
def wavy_below(y0,amp,freq,ph=0):  # region below a wavy line
  xs=np.linspace(-.01,1.01,120); top=[(x,y0+amp*math.sin(freq*x*6.283+ph)) for x in xs]
  return Polygon(top+[(1.01,1.01),(-.01,1.01)])
# ---------------- designs ----------------
def flower():
  C={"B":"#2f5f9e","P":"#f08db0","R":"#c8325e","Y":"#ffd45e","G":"#4f9a5a"}
  cx,cy=.5,.43
  outer=unary_union([ell(cx+.2*math.cos(a),cy+.2*math.sin(a),.17,.11,math.degrees(a)) for a in [i*2*math.pi/5-math.pi/2 for i in range(5)]])
  inner=unary_union([ell(cx+.1*math.cos(a),cy+.1*math.sin(a),.09,.055,math.degrees(a)) for a in [i*2*math.pi/5-math.pi/2+math.pi/5 for i in range(5)]])
  stem=LineString([(cx,cy+.2),(cx-.02,.75),(cx+.01,1.02)]).buffer(.028)
  leaves=unary_union([ell(.36,.78,.13,.05,-30),ell(.64,.72,.13,.05,30)])
  layers=[("B",UNIT,.16),("G",unary_union([stem,leaves]),.09),("P",outer,.095),("R",inner,.07),("Y",Point(cx,cy).buffer(.075),.2)]
  return "freeflower","Glass Blossom",C,layers
def swan():
  C={"P":"#7a5aa6","K":"#e9739a","O":"#f39a4b","Y":"#ffd45e","W":"#f6f1ea","D":"#24476e"}
  water=wavy_below(.66,.008,2.2)
  sun=Point(.72,.5).buffer(.12)
  pink=wavy_below(.24,.025,1.3,.5); orange=wavy_below(.42,.02,1.6,2)
  body=unary_union([ell(.42,.68,.2,.075,-4),ell(.58,.62,.08,.06,-35)])            # body + raised tail feathers
  neck_pts=[(.3,.66),(.24,.58),(.25,.47),(.31,.38),(.32,.30),(.27,.25)]
  neck=LineString(neck_pts).buffer(.03,cap_style=1); head=ell(.25,.245,.05,.035,-10)
  beak=Polygon([(.215,.225),(.13,.265),(.215,.275)])
  ripples=unary_union([ell(.2,.87,.13,.026),ell(.6,.92,.15,.026),ell(.88,.8,.09,.024)])
  refl=unary_union([ell(.72,.735,.1,.024),ell(.73,.81,.06,.022)])
  layers=[("P",UNIT,.13),("K",pink,.11),("O",orange,.11),("Y",sun,.08),("D",water,.12),("P",ripples,1),("Y",refl,1),
          ("W",unary_union([body,neck,head]),.07),("O",beak,1)]
  return "freeswan","Swan at Dusk",C,layers
# ---------------- segmentation ----------------
def regions(layers):
  out=[]
  for i,(col,g,sp) in enumerate(layers):
    g=g.intersection(UNIT)
    later=unary_union([l[1] for l in layers[i+1:]]) if i+1<len(layers) else None
    if later is not None: g=g.difference(later)
    for part in getattr(g,'geoms',[g]):
      if part.area>1e-5: out.append((col,part,sp))
  return out
def poisson(poly,r,rnd,k=40):
  minx,miny,maxx,maxy=poly.bounds; pts=[]
  for _ in range(4000):
    p=(rnd.uniform(minx,maxx),rnd.uniform(miny,maxy))
    if poly.contains(Point(p)) and all((p[0]-q[0])**2+(p[1]-q[1])**2>=r*r for q in pts): pts.append(p)
  return pts
def segment(reg,rnd):
  pieces=[]
  for col,poly,sp in reg:
    if poly.area<sp*sp*1.6: pieces.append((col,poly)); continue
    seeds=poisson(poly,sp,rnd)
    if len(seeds)<2: pieces.append((col,poly)); continue
    for it in range(6):
      cells=voronoi_diagram(MultiPoint(seeds),envelope=box(-1,-1,2,2))
      clipped=[c.intersection(poly) for c in cells.geoms]
      ns=[]
      for c in clipped:
        if c.is_empty: continue
        c=max(getattr(c,'geoms',[c]),key=lambda q:q.area); ns.append((c.centroid.x,c.centroid.y))
      seeds=ns
    for c in clipped:
      for part in getattr(c,'geoms',[c]):
        if part.area>1e-6 and part.geom_type=='Polygon': pieces.append((col,part))
  return pieces
def shared(a,b): 
  if not a.buffer(1e-7).intersects(b): return 0.0
  return a.boundary.intersection(b.buffer(1e-6)).length
def rin(p): return polylabel(p,1e-4).distance(p.exterior)
def merge_small(pieces,rmin):
  changed=True
  while changed:
    changed=False
    pieces.sort(key=lambda q:rin(q[1]))
    for i,(col,p) in enumerate(pieces):
      if rin(p)>=rmin: break
      cand=[(shared(p,q),j) for j,(c2,q) in enumerate(pieces) if j!=i and c2==col]
      cand=[x for x in cand if x[0]>1e-4]
      if not cand and p.area<0.0015:  # tiny orphan pocket: give it to the neighbour it shares most border with
        cand=[(shared(p,q),j) for j,(c2,q) in enumerate(pieces) if j!=i];cand=[x for x in cand if x[0]>1e-4]
      if not cand: continue
      _,j=max(cand); m=unary_union([p,pieces[j][1]])
      if m.geom_type!='Polygon': continue
      pieces[j]=(col,m.buffer(0)); pieces.pop(i); changed=True; break
  return pieces
def graph(pieces):
  N=len(pieces); nb=[[] for _ in range(N)]; ambiguous=0
  for i in range(N):
    for j in range(i+1,N):
      L=shared(pieces[i][1],pieces[j][1])
      if L>=LMIN: nb[i].append(j); nb[j].append(i)
      elif L>1e-4: ambiguous+=1   # visible but very short shared border (<LMIN): not neighbours
  return nb,ambiguous
# ---------------- solver ----------------
def solve(sol,nb,K,start,stats=False):
  N=len(sol); D=[set(range(K)) for _ in range(N)]; lit=set(start)
  for s in start: D[s]={sol[s]}
  how={}; rounds=0
  while True:
    ch=False; rounds+=1
    for p in list(lit):
      cnt=[0]*K
      for q in nb[p]: cnt[sol[q]]+=1
      P=line_poss([D[q] for q in nb[p]],cnt)
      for i,q in enumerate(nb[p]):
        if P[i]!=D[q]:
          D[q]=P[i]
          if len(P[i])==1 and q not in how:
            mono=sum(1 for v in cnt if v)==1
            if mono: how[q]='mono'
            else:
              full=[D[x] if len(D[x])==1 and x!=q else set(range(K)) for x in nb[p]]
              how[q]='direct' if len(line_poss(full,cnt)[i])==1 else 'combined'
            how[q]=(how[q],rounds)
          ch=True
    for q in range(N):
      if len(D[q])==1 and q not in lit: lit.add(q); ch=True
    if not ch: break
  unk=sum(len(d)>1 for d in D)
  if not stats: return unk
  kinds={'mono':0,'direct':0,'combined':0}
  for v in how.values(): kinds[v[0]]+=1
  return unk,dict(kinds,rounds=rounds-1,pieces=N,determined=len(how))
def choose_start(sol,nb,K,seeds=6,max_mono=.45):
  N=len(sol); best=None
  for sd in range(seeds):
    rnd=random.Random(sd); start=[]
    while solve(sol,nb,K,start):
      cand=[i for i in range(N) if i not in start]; rnd.shuffle(cand)
      # prefer starts that are not mono-colour (their numbers say more than 'all the same')
      def key(i):
        mono=len({sol[q] for q in nb[i]}|{sol[i]})==1
        return (solve(sol,nb,K,start+[i]),mono,rnd.random())
      start.append(min(cand[:60],key=key))
    for x in list(start):
      t=[y for y in start if y!=x]
      if not solve(sol,nb,K,t): start=t
    _,st=solve(sol,nb,K,start,True); monoshare=st['mono']/max(1,st['determined'])
    score=(monoshare>max_mono,len(start),monoshare)
    print("  seed",sd,"starts",len(start),st,flush=True)
    if best is None or score<best[0]: best=(score,start,st)
  return best[1],best[2]
def build(design,seed=1,rmin=.024):
  key,name,C,layers=design(); rnd=random.Random(seed)
  pieces=merge_small(segment(regions(layers),rnd),rmin)
  keys=list(C); sol=[keys.index(c) for c,_ in pieces]
  nb,amb=graph(pieces); K=len(keys)
  start,st=choose_start(sol,nb,K)
  rins=[rin(p) for _,p in pieces]; deg=[len(x) for x in nb]
  metrics=dict(st,starts=len(start),short_border_contacts=amb,min_inradius=round(min(rins),4),
    degree_min=min(deg),degree_max=max(deg),degree_mean=round(sum(deg)/len(deg),2),
    mono_share=round(st['mono']/max(1,st['determined']),2),combined_share=round(st['combined']/max(1,st['determined']),2))
  out=[]
  for (col,p),r in zip(pieces,rins):
    q=p.simplify(.0012,preserve_topology=True); pl=polylabel(p,1e-4)
    out.append(dict(p=[[round(x,4),round(1-y,4)] for x,y in list(q.exterior.coords)[:-1]],  # flipped for the window
      pole=[round(pl.x,4),round(1-pl.y,4)],rin=round(r,4)))
  return dict(id=key,name=name,mode="free",colors=[C[k] for k in keys],sol=sol,nb=nb,start=sorted(start),pieces=out,metrics=metrics)
if __name__=="__main__":
  levels=[]
  for d in (flower,swan):
    lv=build(d); print(lv['id'],json.dumps(lv['metrics']),flush=True); levels.append(lv)
  json.dump(levels,open("levels_free_v1.json","w"))
