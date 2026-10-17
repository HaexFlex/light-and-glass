"""Free Glass v2: clean, unambiguous stained-glass pane graphs.
Adds to freeglass.py:
 * decoy lead lines (gentle arcs crossing the picture) so contours are not the only lead lines,
 * geometric clean-up: every touching pair must share a border >= LMIN; short borders / point contacts / 4-way
   junctions are resolved by an "edge flip" (a small disk around the contact is handed to the two panes on the
   other axis, which then share a clear border instead), then merges/explodes, repeated until clean,
 * validator: fails if any touching pair shares < LMIN or any vertex joins >= 4 panes,
 * start search with non-trivial starts (a start pane must see >= 2 colours).
"""
import json, math, random, sys
from shapely.geometry import Point, Polygon, MultiPoint, LineString, MultiLineString, box
from shapely.ops import unary_union, polylabel, polygonize
from shapely import affinity, set_precision, STRtree
from freeglass import ell, wavy_below, regions, segment, merge_small, rin, UNIT, flower, swan
sys.path.insert(0,'.')
from solver2 import line_poss
LMIN=0.022
PREC=1e-7
NEAR=5e-4
def norm(g):
  g=set_precision(g.buffer(0),PREC)
  return [p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' and p.area>1e-7]
def shared(a,b): return a.boundary.intersection(b.buffer(2e-6)).length
# ---------------- new designs ----------------
def koi():
  C={"T":"#2f8f9d","G":"#4f9a5a","O":"#f08a3c","W":"#f6f1ea","P":"#f08db0","Y":"#ffd45e"}
  def fish(cx,cy,ang,s):
    body=ell(cx,cy,.13*s,.05*s,0); tail=Polygon([(cx+.11*s,cy),(cx+.2*s,cy-.06*s),(cx+.18*s,cy),(cx+.2*s,cy+.06*s)])
    fins=unary_union([ell(cx-.02*s,cy-.055*s,.035*s,.018*s,-30),ell(cx-.02*s,cy+.055*s,.035*s,.018*s,30)])
    return affinity.rotate(unary_union([body,tail,fins]),ang,origin=(cx,cy))
  f1=fish(.36,.33,-25,1.25); f2=fish(.63,.72,160,1.15)
  sp1=affinity.rotate(unary_union([ell(.33,.31,.045,.03),ell(.43,.37,.03,.022)]),-25,origin=(.36,.33))
  sp2=affinity.rotate(unary_union([ell(.62,.72,.05,.03)]),160,origin=(.63,.72))
  pads=unary_union([Point(.78,.25).buffer(.13).difference(Polygon([(.78,.25),(.95,.18),(.95,.3)])),Point(.18,.8).buffer(.12).difference(Polygon([(.18,.8),(.02,.72),(.05,.86)])),Point(.9,.62).buffer(.08)])
  lotus=unary_union([ell(.78+.06*math.cos(a),.25+.06*math.sin(a),.06,.03,math.degrees(a)) for a in [i*math.pi/3 for i in range(6)]])
  layers=[("T",UNIT,.13),("G",pads,.09),("P",lotus,.06),("Y",Point(.78,.25).buffer(.035),1),("O",unary_union([f1,f2]),.07),("W",sp1,1),("W",sp2,1)]
  decoys=[LineString([(.5+1.1*math.cos(a),1.5+1.1*math.sin(a)) for a in [math.pi+i*math.pi/60 for i in range(61)]]),
          LineString([(x,.12+.6*x+.03*math.sin(x*9)) for x in [i/60 for i in range(61)]])]
  return "freekoi","Koi Pond",C,layers,decoys
def fox():
  C={"S":"#9cc9e8","Y":"#f2c14e","R":"#c8442e","O":"#ee7d2b","B":"#6b4226","W":"#f6f1ea","G":"#5f8f4e","K":"#2b2a33"}
  trunks=unary_union([LineString([(.1,1),(.12,.6),(.08,.3),(.1,0)]).buffer(.045),LineString([(.9,1),(.88,.55),(.92,.2),(.9,0)]).buffer(.05),
    LineString([(.11,.5),(.25,.38)]).buffer(.02),LineString([(.89,.45),(.75,.33)]).buffer(.02)])
  canopyR=unary_union([Point(.15,.12).buffer(.16),Point(.35,.05).buffer(.12),Point(.85,.1).buffer(.15)])
  canopyY=unary_union([Point(.6,.04).buffer(.14),Point(.27,.22).buffer(.08),Point(.72,.2).buffer(.09)])
  ground=wavy_below(.82,.02,1.3,.3)
  leaves=unary_union([ell(.3,.62,.03,.016,30),ell(.7,.5,.03,.016,-40),ell(.22,.9,.04,.02,10),ell(.5,.95,.04,.02,-20),ell(.78,.92,.035,.018,40)])
  leavesY=unary_union([ell(.42,.55,.03,.016,-20),ell(.35,.92,.04,.02,25),ell(.66,.97,.035,.018,0)])
  body=unary_union([ell(.56,.68,.11,.13,8),ell(.5,.5,.075,.07),Polygon([(.45,.47),(.43,.37),(.5,.44)]),Polygon([(.53,.44),(.57,.36),(.57,.47)]),
    Polygon([(.44,.5),(.35,.535),(.44,.555)])])
  tail=LineString([(.62,.8),(.75,.8),(.82,.72),(.83,.62)]).buffer(.055,cap_style=1)
  tip=Point(.83,.6).buffer(.05); chest=ell(.5,.64,.045,.08,5)
  legs=unary_union([LineString([(.5,.74),(.5,.84)]).buffer(.018),LineString([(.6,.76),(.61,.84)]).buffer(.018)])
  nose=Point(.355,.54).buffer(.017)
  layers=[("S",UNIT,.092),("R",canopyR,.08),("Y",canopyY,.072),("B",trunks,.08),("G",ground,.085),("R",leaves,1),("Y",leavesY,1),
          ("O",unary_union([body,tail]),.055),("W",unary_union([tip,chest]),.06),("K",legs,1)]
  decoys=[LineString([(.5+.95*math.cos(a),1.35+.95*math.sin(a)) for a in [math.pi+i*math.pi/60 for i in range(61)]]),
          LineString([(.5+.62*math.cos(a),1.35+.62*math.sin(a)) for a in [math.pi+i*math.pi/60 for i in range(61)]])]
  return "freefox","Autumn Fox",C,layers,decoys
def with_decoys(d,decoys):
  def f():
    k,n,C,L=d(); return k,n,C,L,decoys
  return f
def split_by(reg,decoys):
  if not decoys: return reg
  lines=unary_union(decoys); out=[]
  for col,poly,sp in reg:
    cut=lines.intersection(poly)
    if cut.is_empty: out.append((col,poly,sp)); continue
    faces=list(polygonize(unary_union([poly.exterior,*poly.interiors,cut])))
    faces=[f for f in faces if poly.contains(f.representative_point())]
    small=[f for f in faces if f.area<sp*sp*.5]
    if len(faces)<2 or small: out.append((col,poly,sp)); continue   # skip cuts that would make slivers
    out+= [(col,f,sp) for f in faces]
  return out
# ---------------- clean-up ----------------
def issues(P):
  geoms=[g for _,g in P]; tree=STRtree(geoms); bad=[]; minL=9
  for i,g in enumerate(geoms):
    for j in tree.query(g.buffer(NEAR)):
      j=int(j)
      if j<=i or geoms[i].distance(geoms[j])>NEAR: continue   # near-contacts (visually touching) count as contacts
      L=shared(geoms[i],geoms[j])
      if L<LMIN: bad.append((L,i,j))
      else: minL=min(minL,L)
  return sorted(bad),minL
def halfplane(c,u,sign):
  n=(-u[1],u[0]); big=10
  p0=(c[0]-u[0]*big,c[1]-u[1]*big); p1=(c[0]+u[0]*big,c[1]+u[1]*big)
  return Polygon([p0,p1,(p1[0]+sign*n[0]*big,p1[1]+sign*n[1]*big),(p0[0]+sign*n[0]*big,p0[1]+sign*n[1]*big)])
def flip(P,i,j,L):
  A=P[i][1]; B=P[j][1]
  ct=A.boundary.intersection(B.buffer(2e-6))
  if ct.is_empty or ct.length<1e-6:
    from shapely.ops import nearest_points
    a,b=nearest_points(A,B); c=Point((a.x+b.x)/2,(a.y+b.y)/2)
  else: c=ct.centroid
  r=max(LMIN*.75,L/2+LMIN*.45); disk=Point(c.x,c.y).buffer(r,resolution=2)
  others=sorted([(P[k][1].intersection(disk).area,k) for k in range(len(P)) if k not in (i,j) and P[k][1].distance(disk)<1e-9],reverse=True)
  others=[k for a,k in others if a>1e-9][:2]
  if not others: return False
  pa=A.intersection(disk); pb=B.intersection(disk)
  if pa.is_empty or pb.is_empty: return False
  u=(pb.centroid.x-pa.centroid.x,pb.centroid.y-pa.centroid.y); m=math.hypot(*u) or 1; u=(u[0]/m,u[1]/m)
  give={k:[] for k in others}
  if len(others)==1: give[others[0]]=[pa,pb]
  else:
    kc,kd=others; cc=P[kc][1].intersection(disk).centroid
    s=(u[0]*(cc.y-c.y)-u[1]*(cc.x-c.x))>0; hc=halfplane((c.x,c.y),u,1 if s else -1); hd=halfplane((c.x,c.y),u,-1 if s else 1)
    give[kc]=[pa.intersection(hc),pb.intersection(hc)]; give[kd]=[pa.intersection(hd),pb.intersection(hd)]
  newP=list(P); newP[i]=(P[i][0],A.difference(disk)); newP[j]=(P[j][0],B.difference(disk))
  for k,parts in give.items(): newP[k]=(P[k][0],unary_union([P[k][1]]+parts))
  out=[]
  for col,g in newP:
    for p in norm(g): out.append([col,p])
  changed=True
  while changed:
    changed=False
    for idx,(col,p) in enumerate(out):
      if p.area<0.0008 or rin(p)<0.008:
        cand=[(shared(p,q),k) for k,(c2,q) in enumerate(out) if k!=idx and p.distance(q)<1e-6]
        cand=[x for x in cand if x[0]>0]
        if not cand: out.pop(idx); changed=True; break
        same=[x for x in cand if out[x[1]][0]==col]; _,k=max(same or cand)
        m=norm(unary_union([out[k][1],p]))
        if len(m)==1: out[k][1]=m[0]; out.pop(idx); changed=True; break
  P[:]=[(c,g) for c,g in out]; return True
def clean(P,maxit=400):
  for it in range(maxit):
    bad,minL=issues(P)
    if not bad: return it,minL
    done=False
    for L,i,j in bad:
      if flip(P,i,j,L): done=True; break
    if not done: return None,None
  return None,None
def validate(P):
  bad,minL=issues(P)
  geoms=[g for _,g in P]; tree=STRtree(geoms); maxv=0
  for g in geoms:
    for x,y in g.exterior.coords:
      pt=Point(x,y); v=sum(1 for k in tree.query(pt.buffer(1e-5)) if geoms[int(k)].distance(pt)<1e-5)
      maxv=max(maxv,v)
  return (not bad and maxv<=3),dict(short_borders=len(bad),min_shared_border=round(minL,4),max_junction_valence=maxv)
# ---------------- solver ----------------
def solve(sol,nb,K,start,stats=False,gift=()):
  # gift panes: colour known from the start (pre-filled by the game) but NOT lit, so they give no badges; they are never solved by the player
  N=len(sol); D=[set(range(K)) for _ in range(N)]; lit=set(start); gift=set(gift)
  for s in start: D[s]={sol[s]}
  for g in gift: D[g]={sol[g]}
  how={}; rounds=0
  while True:
    ch=False; rounds+=1
    for p in list(lit):
      cnt=[0]*K
      for q in nb[p]: cnt[sol[q]]+=1
      Pp=line_poss([D[q] for q in nb[p]],cnt)
      for ii,q in enumerate(nb[p]):
        if Pp[ii]!=D[q]:
          D[q]=Pp[ii]
          if len(Pp[ii])==1 and q not in how:
            if sum(1 for v in cnt if v)==1: kind='mono'
            else:
              full=[D[x] if len(D[x])==1 and x!=q else set(range(K)) for x in nb[p]]
              kind='direct' if len(line_poss(full,cnt)[ii])==1 else 'combined'
            how[q]=kind
          ch=True
    for q in range(N):
      if len(D[q])==1 and q not in lit and q not in gift: lit.add(q); ch=True
    if not ch: break
  unk=sum(len(d)>1 for q,d in enumerate(D) if q not in gift)
  if not stats: return unk
  kinds={'mono':0,'direct':0,'combined':0}
  for v in how.values(): kinds[v]+=1
  return unk,dict(kinds,rounds=rounds-1,determined=len(how))
def choose_start(sol,nb,K,seeds=6,gift=()):
  N=len(sol); best=None; gset=set(gift)
  ok=[i for i in range(N) if len({sol[q] for q in nb[i]})>=2 and i not in gset]
  for sd in range(seeds):
    rnd=random.Random(sd); start=[]
    while solve(sol,nb,K,start,gift=gift):
      cand=[i for i in ok if i not in start]; rnd.shuffle(cand)
      start.append(min(cand[:50],key=lambda i:(solve(sol,nb,K,start+[i],gift=gift),rnd.random())))
    for x in list(start):
      t=[y for y in start if y!=x]
      if t and not solve(sol,nb,K,t,gift=gift): start=t
    _,st=solve(sol,nb,K,start,True,gift=gift); mono=st['mono']/max(1,st['determined'])
    score=(len(start),mono,-st['combined'])
    if best is None or score<best[0]: best=(score,start,st)
  return best[1],best[2]
def build(design,seed=1,rmin=.024):
  key,name,C,layers,decoys=design(); rnd=random.Random(seed)
  reg=split_by(regions(layers),decoys)
  P=merge_small(segment(reg,rnd),rmin); P=[(c,g) for c,g0 in P for g in norm(g0)]
  it,_=clean(P)
  if it is None: raise SystemExit(f"{key}: clean-up failed")
  P=merge_small(P,rmin); it2,_=clean(P)
  if it2 is None: raise SystemExit(f"{key}: clean-up failed (2)")
  ok,val=validate(P)
  if not ok: raise SystemExit(f"{key}: VALIDATION FAILED {val}")
  keys=list(C); sol=[keys.index(c) for c,_ in P]; K=len(keys); N=len(P)
  geoms=[g for _,g in P]; tree=STRtree(geoms); nb=[[] for _ in range(N)]
  for i,g in enumerate(geoms):
    for j in tree.query(g.buffer(1e-6)):
      j=int(j)
      if j!=i and g.distance(geoms[j])<1e-6: nb[i].append(j)
  start,st=choose_start(sol,nb,K)
  rins=[rin(g) for g in geoms]; deg=[len(x) for x in nb]
  metrics=dict(pieces=N,colours=K,starts=len(start),**st,mono_share=round(st['mono']/max(1,st['determined']),2),
    combined_share=round(st['combined']/max(1,st['determined']),2),cleanup_flips=it+it2,**val,
    min_inradius=round(min(rins),4),degree_min=min(deg),degree_max=max(deg),degree_mean=round(sum(deg)/N,2),decoy_lines=len(decoys))
  assert not solve(sol,nb,K,start)
  out=[]
  for g,r in zip(geoms,rins):
    pl=polylabel(g,1e-4)
    out.append(dict(p=[[round(x,5),round(1-y,5)] for x,y in list(g.exterior.coords)[:-1]],pole=[round(pl.x,4),round(1-pl.y,4)],rin=round(r,4)))
  return dict(id=key,name=name,mode="free",colors=[C[k] for k in keys],sol=sol,nb=nb,start=sorted(start),pieces=out,metrics=metrics)
ARCS=[LineString([(.5+.9*math.cos(a),1.3+.9*math.sin(a)) for a in [math.pi+i*math.pi/60 for i in range(61)]])]
SWANARC=[LineString([(.5+.75*math.cos(a),-.35+.75*math.sin(a)) for a in [i*math.pi/60 for i in range(61)]])]
DESIGNS=[with_decoys(flower,ARCS),koi,with_decoys(swan,SWANARC),fox]
if __name__=="__main__":
  only=sys.argv[1:]
  for d in DESIGNS:
    k=d()[0]
    if only and k not in only: continue
    lv=build(d); print(k,json.dumps(lv['metrics']),flush=True)
    json.dump(lv,open(f"lv_{k}.json","w"))
