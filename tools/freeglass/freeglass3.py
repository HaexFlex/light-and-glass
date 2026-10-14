"""Free Glass v3: natural Voronoi-like panes (no notch carving).
Adjacency rule: two panes are neighbours iff they share a visible border segment (length > 0).
A point / corner contact is NOT adjacency. The only clean-up is vertex snapping: a border between two
junctions shorter than LSNAP is collapsed to an exact point (so a tiny ambiguous edge becomes a clean corner
touch; that point may join 4+ panes). No polygon spikes are created.
Validator: valid simple polygons, partition covers the window, no ambiguous contacts (0 < shared < LSNAP),
no spike angles (< MIN_ANGLE deg), neighbour lists = geometry.
Export fixes rounding pinches (koi) in the generator itself."""
import json, math, random, sys
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union, polylabel
from shapely import STRtree, set_precision
from freeglass import regions, segment, merge_small, rin
from freeglass2 import DESIGNS, split_by, norm, solve, choose_start
LSNAP=0.009; MIN_ANGLE=12.0; EPS=1e-6
def shared(a,b): return a.boundary.intersection(b.buffer(2e-6)).length
def ring(g): return [tuple(c) for c in list(g.exterior.coords)[:-1]]
def angles(pts):
  n=len(pts); out=[]
  for k in range(n):
    a,b,c=pts[k-1],pts[k],pts[(k+1)%n]
    v1=(a[0]-b[0],a[1]-b[1]); v2=(c[0]-b[0],c[1]-b[1]); m=math.hypot(*v1)*math.hypot(*v2)
    if m<1e-18: out.append(0.0); continue
    out.append(math.degrees(math.acos(max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/m)))))
  return out
FRAME=box(0,0,1,1).exterior; AREA=1.0
def set_frame(w=1.0,h=1.0):
  """non-square windows (raster levels): frame w x h, width normally 1. Default unit square = original behaviour."""
  global FRAME,AREA; FRAME=box(0,0,w,h).exterior; AREA=w*h
JAG_EDGE=0.012
def spikes_of(pts):
  n=len(pts);A=angles(pts)
  return sum(1 for k in range(n) if A[k]<MIN_ANGLE and min(math.dist(pts[k],pts[k-1]),math.dist(pts[k],pts[(k+1)%n]))<JAG_EDGE)
def deslit(pts):
  pts=list(pts);ch=True
  while ch and len(pts)>3:
    ch=False;A=angles(pts)
    for k in range(len(pts)):
      if A[k]<0.5: pts.pop(k);ch=True;break
  return pts
def noded(P):
  """Rebuild as an exact planar partition (shared vertices, no gaps/overlaps) by polygonizing all lead lines."""
  from shapely.ops import polygonize
  G=[g for _,g in P]; lines=unary_union([g.exterior for g in G]+[FRAME]); faces=[f for f in polygonize(lines) if f.area>1e-12]
  tree=STRtree(G); own=[[] for _ in G]; orphan=[]
  for f in faces:
    rp=f.representative_point(); hit=[int(k) for k in tree.query(rp) if G[int(k)].contains(rp)]
    if hit: own[max(hit,key=lambda k:G[k].intersection(f).area)].append(f)
    else: orphan.append(f)
  for f in orphan:
    cand=[(shared(f,unary_union(own[k]) if own[k] else G[k]),k) for k in range(len(G)) if G[k].distance(f)<1e-6]
    own[max(cand)[1]].append(f)
  out=[]
  for (c,_),fs in zip(P,own):
    u=unary_union(fs)
    for g in getattr(u,'geoms',[u]):
      if g.geom_type=='Polygon' and g.area>1e-9: out.append((c,Polygon(deslit(ring(g)))))
  return out
SIMPLIFY=0.0012
def faces_to_panes(segs,P):
  """polygonize the lead network; each face goes to the current pane it overlaps most; a pane's faces are unioned.
  Returns None if a pane vanishes or becomes non-polygonal."""
  from shapely.ops import polygonize
  faces=[f for f in polygonize(unary_union(segs)) if f.area>1e-14]
  G=[g for _,g in P]; tree=STRtree(G); own=[[] for _ in P]
  tiny=[]
  for f in faces:
    if f.area<2e-6: tiny.append(f); continue
    hit=[(G[int(k)].intersection(f).area,int(k)) for k in tree.query(f)]
    hit=[h for h in hit if h[0]>f.area*.5]
    if not hit: tiny.append(f); continue   # gap in the source pieces: fill from the neighbour
    own[max(hit)[1]].append(f)
  U=[unary_union(fs) if fs else None for fs in own]
  for f in tiny:   # micro slivers along a border join the pane they share most boundary with
    cand=[(shared(f,U[k]),k) for k in range(len(U)) if U[k] is not None and U[k].distance(f)<1e-7]
    if cand: k=max(cand)[1]; own[k].append(f); U[k]=unary_union(own[k])
  out=[]
  for (c,_),fs in zip(P,own):
    if not fs: return None
    u=unary_union(fs)
    if u.geom_type!='Polygon' or u.interiors: return None
    out.append((c,u))
  return out
def lead(P):
  """lead network = all pane borders (shared once), merged into segments between junctions."""
  from shapely.ops import linemerge
  u=unary_union([g.exterior for _,g in P]+[FRAME]); m=linemerge(u)
  return [LineString(l.coords) for l in getattr(m,'geoms',[m])]
def snap(P,post=False):
  """Contract lead segments shorter than LSNAP (a border between two junctions) into a point; then lightly
  simplify every segment (endpoints fixed) so both sides of a border stay identical and tiny jaggies vanish."""
  P=[(c,set_precision(g,1e-7)) for c,g in P]
  from shapely import set_precision as _sp
  Q=faces_to_panes(lead(P),P)
  if Q: P=Q
  def collapse(P,strict=True):
    n=0; bad=set()
    for _ in range(600):
      segs=lead(P)
      key=lambda s:(round(s.coords[0][0],6),round(s.coords[0][1],6),round(s.coords[-1][0],6),round(s.coords[-1][1],6))
      short=sorted([(x.length,k) for k,x in enumerate(segs) if x.length<LSNAP and not x.is_ring and key(x) not in bad])
      done=False
      for L,k in short:
        x=segs[k]; a,b=x.coords[0],x.coords[-1]
        fa,fb=FRAME.distance(Point(a))<EPS,FRAME.distance(Point(b))<EPS
        if fa and fb and L>1e-5: bad.add(key(x)); continue
        if post and L<1e-7: bad.add(key(x)); continue   # degenerate zero-length piece: collapsing it changes nothing (would loop)
        for m in ([a] if fa else [b] if fb else [((a[0]+b[0])/2,(a[1]+b[1])/2),a,b]):
          new=[]
          for t,y in enumerate(segs):
            if t==k: continue
            c=[m if (math.dist(v,a)<EPS or math.dist(v,b)<EPS) else v for v in y.coords]
            d=[]
            for v in c:
              if not d or math.dist(d[-1],v)>1e-9: d.append(v)
            if len(d)>=2: new.append(LineString(d))
          Q=faces_to_panes(new,P)
          if Q and all(g.is_valid for _,g in Q) and (not strict or sum(spikes_of(ring(g)) for _,g in Q)<=sum(spikes_of(ring(g)) for _,g in P)):
            P=Q; n+=1; done=True; break
        if done: break
        bad.add(key(x))
      if not done: break
    return P,n
  P,collapsed=collapse(P)
  Q=faces_to_panes([x.simplify(SIMPLIFY,preserve_topology=True) for x in lead(P)],P)
  if Q: P=Q
  # despike: a jaggy vertex in the middle of a lead segment is dropped from that (shared) segment
  tried=set()
  for _ in range(100):
    hit=None
    for _,g in P:
      r=ring(g);n=len(r);A=angles(r)
      for k in range(n):
        if A[k]<MIN_ANGLE and min(math.dist(r[k],r[k-1]),math.dist(r[k],r[(k+1)%n]))<JAG_EDGE:
          for v in (r[k],r[k-1] if math.dist(r[k],r[k-1])<JAG_EDGE else r[(k+1)%n]):
            if v not in tried: hit=v;break
          if hit: break
      if hit:break
    if not hit:break
    tried.add(hit);segs=lead(P);new=[]
    for y in segs:
      c=list(y.coords)
      if len(c)>2: c=[c[0]]+[v for v in c[1:-1] if math.dist(v,hit)>EPS]+[c[-1]]
      new.append(LineString(c))
    Q=faces_to_panes(new,P)
    if Q and all(g.is_valid for _,g in Q) and sum(spikes_of(ring(g)) for _,g in Q)<sum(spikes_of(ring(g)) for _,g in P): P=Q;collapsed+=1
  if post:   # raster levels: simplify/despike shorten dense smoothed borders below LSNAP -> collapse those too
    P,n2=collapse(P,True); collapsed+=n2
  return [(c,Polygon(deslit(ring(g)))) for c,g in P],collapsed
def adjacency(G,lo=1e-4):
  tree=STRtree(G); nb=[[] for _ in G]; amb=[]; corner=0; minL=9
  for i,g in enumerate(G):
    for j in tree.query(g.buffer(1e-5)):
      j=int(j)
      if j<=i or g.distance(G[j])>1e-5: continue
      L=shared(g,G[j])
      if L>=LSNAP*.95: nb[i].append(j); nb[j].append(i); minL=min(minL,L)
      elif L>lo: amb.append((i,j,round(L,5)))
      else: corner+=1
  return [sorted(x) for x in nb],amb,corner,minL
def check(G):
  invalid=sum(not g.is_valid or g.geom_type!='Polygon' for g in G)
  cover=abs(unary_union(G).area-AREA)
  overlap=sum(g.area for g in G)-AREA
  nb,amb,corner,minL=adjacency(G)
  mina=min(min(angles(ring(g))) for g in G)
  spikes=sum(spikes_of(ring(g)) for g in G)
  maxv=0
  tree=STRtree(G)
  for g in G:
    for v in ring(g):
      pt=Point(v); maxv=max(maxv,sum(1 for k in tree.query(pt.buffer(1e-5)) if G[int(k)].distance(pt)<1e-5))
  ok=not invalid and cover<1e-4 and abs(overlap)<1e-4 and not amb and not spikes
  return ok,nb,dict(invalid_polys=invalid,coverage_err=round(cover,6),ambiguous_contacts=len(amb),corner_touches=corner,
    min_shared_border=round(minL,4),min_angle_deg=round(mina,1),spikes=spikes,max_point_valence=maxv)
def export(G):
  """round to 5 decimals; repair any rounding pinch (self-touch) in place."""
  out=[];fixed=0
  for g in G:
    q=[(round(x,5),round(y,5)) for x,y in ring(g)]
    d=[]
    for v in q:
      if not d or d[-1]!=v: d.append(v)
    if d[0]==d[-1]: d.pop()
    p=Polygon(d)
    if not p.is_valid:
      b=p.buffer(0); assert b.geom_type=='Polygon',"pinch repair failed"
      p=Polygon([(round(x,5),round(y,5)) for x,y in list(b.exterior.coords)[:-1]]); fixed+=1
    assert p.is_valid
    out.append(p)
  return out,fixed
def build(design,seed=1,rmin=.024):
  key,name,C,layers,decoys=design(); rnd=random.Random(seed)
  reg=split_by(regions(layers),decoys)
  P=merge_small(segment(reg,rnd),rmin); P=[(c,g) for c,g0 in P for g in norm(g0)]
  P,ncol=snap(P)
  keys=list(C); sol=[keys.index(c) for c,_ in P]; K=len(keys)
  G,fixed=export([g for _,g in P])
  ok,nb,val=check(G)
  if not ok: raise SystemExit(f"{key}: VALIDATION FAILED {val}")
  N=len(G); start,st=choose_start(sol,nb,K)
  assert not solve(sol,nb,K,start)
  rins=[rin(g) for g in G]; deg=[len(x) for x in nb]
  metrics=dict(pieces=N,colours=K,starts=len(start),**st,mono_share=round(st['mono']/max(1,st['determined']),2),
    combined_share=round(st['combined']/max(1,st['determined']),2),snapped_edges=ncol,pinch_repairs=fixed,**val,
    min_inradius=round(min(rins),4),degree_min=min(deg),degree_max=max(deg),degree_mean=round(sum(deg)/N,2),decoy_lines=len(decoys))
  pieces=[]
  for g,r in zip(G,rins):
    pl=polylabel(g,1e-4)
    pieces.append(dict(p=[[x,round(1-y,5)] for x,y in ring(g)],pole=[round(pl.x,4),round(1-pl.y,4)],rin=round(r,4)))
  return dict(id=key,name=name,mode="free",colors=[C[k] for k in keys],sol=sol,nb=nb,start=sorted(start),pieces=pieces,metrics=metrics)
if __name__=="__main__":
  only=sys.argv[1:]
  for d in DESIGNS:
    k=d()[0]
    if only and k not in only: continue
    for seed in range(1,13):
      try: lv=build(d,seed); break
      except SystemExit as e: print(k,'seed',seed,e,flush=True)
    else: raise SystemExit(k+': all seeds failed')
    lv['metrics']['seed']=seed; print(k,json.dumps(lv['metrics']),flush=True)
    json.dump(lv,open(f"lv3_{k}.json","w"))
