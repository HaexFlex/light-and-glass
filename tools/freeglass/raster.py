"""Raster picture -> Free Glass level (reusable pipeline).

  python raster.py levels/source/<name>.json [--quant-only]

Config keys (see levels/source/mountains.json):
  id, name, image, crop [x0,y0,x1,y1] (optional), grid (raster width in px; height follows the image aspect, no distortion)
  palette: [{name, hex (glass colour shown in game), anchors [hex,...] (typical source colours)}]
  min_de: minimum OKLab distance (x100) required between every pair of glass colours (fails otherwise)
  overrides: [{from,to,box:[x0,y0,x1,y1] in 0..1 picture coords}]  e.g. sky-coloured pixels low in the picture = lake
  median, mode_sizes, min_region_px: speckle clean-up;  simplify_px, smooth_iter: lead smoothing
  spacing (pane size), rmin (min pane inradius), max_seeds, start_seeds, max_starts, min_starts, out_prefix

Steps: crop -> resize (aspect kept) -> nearest-anchor quantisation in OKLab to a FIXED palette -> spatial overrides ->
median + mode filter + minimum region size (speckle) -> exact region polygons (rasterio) -> shared smoothed lead network ->
per-region Voronoi panes -> merge_small -> freeglass3 snap/despike/validate (frame W=1 x H=1/aspect) -> cascade start search.
Window coordinates: width 1, height 1/aspect, y down, picture stored upside down (floor reveal flips it back)."""
import json, sys, time, random, itertools, os
import numpy as np
from PIL import Image
from scipy import ndimage
from shapely.geometry import shape, Polygon, LineString, box
from shapely.ops import unary_union, linemerge, polygonize, polylabel
from shapely import STRtree
import rasterio.features
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass import segment, merge_small, rin
from freeglass2 import solve, choose_start, norm
import freeglass3
from freeglass3 import snap, export, check, ring
def log(*a): print(f"[{time.strftime('%H:%M:%S')}]",*a,flush=True)
def srgb2lin(c): c=c/255.0; return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def oklab(rgb):
  l=srgb2lin(np.asarray(rgb).astype(float)); r,g,b=l[...,0],l[...,1],l[...,2]
  L=np.cbrt(0.4122214708*r+0.5363325363*g+0.0514459929*b); M=np.cbrt(0.2119034982*r+0.6806995451*g+0.1073969566*b); S=np.cbrt(0.0883024619*r+0.2817188376*g+0.6299787005*b)
  return np.stack([0.2104542553*L+0.7936177850*M-0.0040720468*S,1.9779984951*L-2.4285922050*M+0.4505937099*S,0.0259040371*L+0.7827717662*M-0.8086757660*S],-1)
def h2rgb(h): return [int(h[i:i+2],16) for i in (1,3,5)]
def de(a,b): return 100*float(np.linalg.norm(oklab(h2rgb(a))-oklab(h2rgb(b))))
def palette_report(pal,min_de):
  rows=[];worst=(1e9,None)
  for a,b in itertools.combinations(pal,2):
    d=de(a['hex'],b['hex']); worst=min(worst,(d,(a['name'],b['name'])))
  log(f"palette: {len(pal)} colours, min pairwise OKLab dE={worst[0]:.1f} ({worst[1][0]} / {worst[1][1]}), required >= {min_de}")
  if worst[0]<min_de: raise SystemExit("palette colours too similar")
  return round(worst[0],1),worst[1]
def quantise(rgb,pal,overrides):
  lab=oklab(rgb); A=[];own=[]
  for k,p in enumerate(pal):
    for h in p['anchors']: A.append(oklab(h2rgb(h))); own.append(k)
  A=np.array(A); own=np.array(own)
  d=((lab[...,None,:]-A)**2).sum(-1); L=own[d.argmin(-1)]
  H,W=L.shape; names=[p['name'] for p in pal]
  for o in overrides or []:
    x0,y0,x1,y1=o['box']; m=np.zeros_like(L,bool); m[int(y0*H):int(y1*H),int(x0*W):int(x1*W)]=True
    L[m&(L==names.index(o['from']))]=names.index(o['to'])
  return L
def mode_filter(L,K,size):
  best=np.zeros(L.shape); out=L.copy()
  for k in range(K):
    f=ndimage.uniform_filter((L==k).astype(float),size,mode='nearest'); m=f>best; out[m]=k; best[m]=f[m]
  return out
def remove_small(L,K,minpix):
  for _ in range(30):
    changed=False
    for k in range(K):
      comp,n=ndimage.label(L==k)
      if n==0: continue
      sizes=ndimage.sum(np.ones_like(L),comp,range(1,n+1))
      for ci in np.where(sizes<minpix)[0]+1:
        m=comp==ci; ring_=ndimage.binary_dilation(m)&~m; nbv=L[ring_]
        if len(nbv)==0: continue
        L[m]=np.bincount(nbv,minlength=K).argmax(); changed=True
    if not changed: break
  return L
def chaikin(coords,it=2):
  pts=np.array(coords)
  for _ in range(it):
    if len(pts)<3: break
    q=[pts[0]]
    for a,b in zip(pts[:-1],pts[1:]): q+=[0.75*a+0.25*b,0.25*a+0.75*b]
    q.append(pts[-1]); pts=np.array(q)
  return [tuple(p) for p in pts]
def vectorise(L,simp_px,smooth_it):
  """label raster -> coloured polygons in window coords (x/W, y/W; y down). Every border is simplified/smoothed once
  as a shared segment, so neighbouring regions keep identical borders."""
  Hh,W=L.shape; Hn=Hh/W
  polys=[(int(v),shape(s)) for s,v in rasterio.features.shapes(L.astype(np.int32),connectivity=4)]
  tf=lambda g:Polygon([(x/W,y/W) for x,y in g.exterior.coords],[[(x/W,y/W) for x,y in r.coords] for r in g.interiors])
  polys=[(v,tf(g)) for v,g in polys]
  frame=box(0,0,1,Hn).exterior
  onf=lambda x,y:abs(x)<1e-9 or abs(x-1)<1e-9 or abs(y)<1e-9 or abs(y-Hn)<1e-9
  lines=linemerge(unary_union([g.exterior for _,g in polys]+[r for _,g in polys for r in g.interiors]+[frame]))
  segs=[]
  for s in getattr(lines,'geoms',[lines]):
    s=s.simplify(simp_px/W,preserve_topology=False); c=list(s.coords)
    if len(c)>=2 and all(onf(x,y) for x,y in c): segs.append(LineString(c)); continue
    segs.append(LineString(chaikin(c,smooth_it) if not s.is_ring else c))
  faces=[f for f in polygonize(unary_union(segs)) if f.area>1e-9]
  P=[g for _,g in polys]; tree=STRtree(P); lab=[]
  for f in faces:
    hit=[(P[int(k)].intersection(f).area,int(k)) for k in tree.query(f)]
    lab.append(polys[max(hit)[1]][0] if hit else None)
  reg={}
  for f,v in zip(faces,lab):
    if v is not None: reg.setdefault(v,[]).append(f)
  out=[]
  for v,fs in reg.items():
    u=unary_union(fs)
    for g in getattr(u,'geoms',[u]):
      if g.geom_type=='Polygon' and g.area>1e-6: out.append((v,g))
  return out
def quant_stage(cfg,base):
  im=Image.open(os.path.join(base,cfg['image'])).convert('RGB')
  if cfg.get('crop'): im=im.crop(tuple(cfg['crop']))
  W=cfg.get('grid',300); Hh=round(W*im.height/im.width); asp=W/Hh
  rgb=np.array(im.resize((W,Hh),Image.LANCZOS)); pal=cfg['palette']; K=len(pal)
  L=quantise(rgb,pal,cfg.get('overrides'))
  if cfg.get('median'): L=ndimage.median_filter(L,cfg['median'],mode='nearest')
  for s in cfg.get('mode_sizes',[3,3]): L=mode_filter(L,K,s)
  L=remove_small(L,K,cfg.get('min_region_px',60))
  share={p['name']:round(float((L==k).mean())*100,1) for k,p in enumerate(pal)}
  log('colour shares %',share)
  used=[k for k in range(K) if (L==k).any()]
  if len(used)<K: log('WARNING unused colours dropped:',[pal[k]['name'] for k in range(K) if k not in used])
  remap=np.full(K,-1); remap[used]=range(len(used)); L=remap[L]; pal=[pal[k] for k in used]
  q=np.array([h2rgb(p['hex']) for p in pal],np.uint8)[L]
  big=Image.fromarray(q).resize((im.width//2,im.height//2),Image.NEAREST); big.save(cfg['out_prefix']+'_quant.png')
  orig=im.resize(big.size,Image.LANCZOS); sbs=Image.new('RGB',(big.width,big.height*2+12),(20,17,15)); sbs.paste(orig,(0,0)); sbs.paste(big,(0,big.height+12))
  sbs.save(cfg['out_prefix']+'_compare.png')
  return L,pal,asp,share
def main(cfgp,quant_only=False):
  t0=time.time(); cfg=json.load(open(cfgp)); base=os.path.dirname(os.path.abspath(cfgp))
  dmin=palette_report(cfg['palette'],cfg.get('min_de',12))
  L,pal,asp,share=quant_stage(cfg,base); K=len(pal); Hn=1/asp
  log('quantised',L.shape,'colours',K,'aspect',round(asp,4))
  if quant_only: return
  freeglass3.set_frame(1.0,Hn)
  log('vectorising'); R=vectorise(L,cfg.get('simplify_px',0.8),cfg.get('smooth_iter',2)); log('regions',len(R))
  sp=cfg.get('spacing',0.06); reg=[(v,g,sp) for v,g in R]
  for seed in range(1,cfg.get('max_seeds',8)+1):
    rnd=random.Random(seed*7919+cfg.get('seed',0))
    log('segment seed',seed); P=merge_small(segment(reg,rnd),cfg.get('rmin',0.016)); P=[(c,g) for c,g0 in P for g in norm(g0)]
    log('panes before snap',len(P)); P,ncol=snap(P,post=True)
    sol=[c for c,_ in P]; Gs,fixed=export([g for _,g in P]); ok,nb,val=check(Gs)
    log('check',ok,val)
    if not ok: continue
    if any(not x for x in nb): log('isolated pane'); continue
    log('choosing start'); start,st=choose_start(sol,nb,K,seeds=cfg.get('start_seeds',4))
    log('starts',len(start),st)
    if not (cfg.get('min_starts',1)<=len(start)<=cfg.get('max_starts',4)) or solve(sol,nb,K,start): continue
    break
  else: raise SystemExit('no valid seed')
  rins=[rin(g) for g in Gs]; deg=[len(x) for x in nb]
  metrics=dict(pieces=len(Gs),colours=K,starts=len(start),**st,mono_share=round(st['mono']/max(1,st['determined']),2),combined_share=round(st['combined']/max(1,st['determined']),2),
    snapped_edges=ncol,pinch_repairs=fixed,**val,min_inradius=round(min(rins),4),degree_min=min(deg),degree_max=max(deg),degree_mean=round(sum(deg)/len(deg),2),
    max_badges=max(len({sol[j] for j in x}) for x in nb),palette_min_de=dmin[0],seed=seed,gen_seconds=round(time.time()-t0))
  pieces=[]
  for g,r in zip(Gs,rins):   # flip vertically: the window shows the picture upside down
    pl=polylabel(g,1e-4); pieces.append(dict(p=[[x,round(Hn-y,5)] for x,y in ring(g)],pole=[round(pl.x,4),round(Hn-pl.y,4)],rin=round(r,4)))
  lv=dict(id=cfg['id'],name=cfg['name'],mode='free',aspect=round(asp,6),colors=[p['hex'] for p in pal],cnames=[p['name'] for p in pal],
          sol=sol,nb=nb,start=sorted(start),pieces=pieces,metrics=metrics)
  json.dump(lv,open(cfg['out_prefix']+'.json','w')); log('done',json.dumps(metrics))
if __name__=='__main__': main(sys.argv[1],'--quant-only' in sys.argv)
