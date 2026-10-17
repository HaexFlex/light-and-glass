"""Natural-shape panes for photo levels (experiment).
Instead of Poisson/Voronoi blobs inside colour regions, build the pane partition in the raster domain:
 1. colour regions = connected components of the quantised label image; tiny ones merge into the neighbour sharing the
    longest border (gift colours keep a lower size threshold so eyes/nose survive);
 2. big regions are cut by straight lines (across the long axis for elongated regions, along the local fur direction for
    compact ones) into equal-area pieces; flat background colours get a bigger target size;
 3. regions enclosing another region get a straight through-cut so no pane has a hole;
 4. the pane-id raster is vectorised once with shared simplified/smoothed borders (raster.vectorise), then the existing
    snap/check/export/start/autofill steps run unchanged.
usage: natural.py cfg.json   (cfg = raster.py config + natural options: nat_px, bg_mult, min_px, gift_px, aspect_cut)"""
import json, sys, os, time, random
import numpy as np
from scipy import ndimage
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import raster
from raster import quant_stage, vectorise, log
from freeglass import rin
from freeglass2 import solve, choose_start, norm
import freeglass3
from freeglass3 import snap, export, check, ring
from shapely.ops import polylabel
from PIL import Image

def components(C):
  out=np.zeros(C.shape,int); n=0
  for k in np.unique(C):
    lab,m=ndimage.label(C==k)   # 4-connectivity
    out[lab>0]=lab[lab>0]+n; n+=m
  return out-1,n
def borders(I):
  a=np.concatenate([np.stack([I[:,:-1].ravel(),I[:,1:].ravel()],1),np.stack([I[:-1].ravel(),I[1:].ravel()],1)])
  a=a[a[:,0]!=a[:,1]]; return a
def merge_small(I,col,thr,same_bonus=3.0):
  """merge panes smaller than thr[colour] into the neighbour with the longest shared border (same colour preferred)"""
  while True:
    ar=np.bincount(I.ravel(),minlength=len(col)); cand=[(ar[i],i) for i in range(len(col)) if 0<ar[i]<thr(col[i])]
    if not cand: return I
    _,p=min(cand); b=borders(I); b=b[(b[:,0]==p)|(b[:,1]==p)]
    if not len(b): return I
    o=np.where(b[:,0]==p,b[:,1],b[:,0]); sc={}
    for q in o: sc[q]=sc.get(q,0)+(same_bonus if col[q]==col[p] else 1)
    q=max(sc,key=sc.get); I[I==p]=q
def fur_dir(gray,mask):
  gy,gx=np.gradient(ndimage.gaussian_filter(gray,1.5)); jxx=(gx*gx)[mask].sum(); jyy=(gy*gy)[mask].sum(); jxy=(gx*gy)[mask].sum()
  th=0.5*np.arctan2(2*jxy,jxx-jyy)+np.pi/2   # direction along the fur (perpendicular to the mean gradient)
  return np.array([np.cos(th),np.sin(th)])
def bisect(ys,xs,n,d,out,cut_across,gray_mask_dir):
  """recursively cut the pixel set into n equal pieces; cut_across=True: lines perpendicular to the long axis"""
  if n<=1: out.append((ys,xs)); return
  P=np.stack([xs,ys],1).astype(float); c=P.mean(0); w,v=np.linalg.eigh(np.cov((P-c).T)+1e-9*np.eye(2)); major=v[:,1]
  asp=np.sqrt(w[1]/max(w[0],1e-9))
  if asp>1.6 or not cut_across: axis=major            # elongated: cut across the long axis (normal = major)
  else:
    f=gray_mask_dir(ys,xs); axis=np.array([-f[1],f[0]])   # compact: cut line runs along the fur, normal = perpendicular
  t=(P-c)@axis; n1=n//2; thr=np.quantile(t,n1/n); m=t<=thr
  bisect(ys[m],xs[m],n1,d,out,cut_across,gray_mask_dir); bisect(ys[~m],xs[~m],n-n1,d,out,cut_across,gray_mask_dir)
def split_big(I,col,target,gray,cut_across=True):
  nxt=I.max()+1; col=list(col); ar=np.bincount(I.ravel())
  for p in range(len(ar)):
    t=target(col[p]); n=int(round(ar[p]/t)) if ar[p]>1.5*t else 1
    if n<=1: continue
    ys,xs=np.nonzero(I==p); pieces=[]
    msk=np.zeros(I.shape,bool); msk[ys,xs]=True
    f=fur_dir(gray,msk)
    bisect(ys,xs,n,None,pieces,cut_across,lambda y,x:f)
    for ys2,xs2 in pieces[1:]: I[ys2,xs2]=nxt; col.append(col[p]); nxt+=1
  return I,np.array(col)
def cut_holes(I,col):
  nxt=I.max()+1; col=list(col)
  for _ in range(200):
    done=True
    for p in range(len(col)):
      m=I==p
      if not m.any(): continue
      h=ndimage.binary_fill_holes(m)&~m
      if h.any():
        ys,xs=np.nonzero(h); cx=int(xs.mean()); mm=m&(np.arange(I.shape[1])[None,:]>cx); I[mm]=nxt; col.append(col[p]); nxt+=1; done=False; break
    if done: break
  return I,np.array(col)
def merge_tiny(P,amin,gift_amin=0):
  """vector slivers/fragments below amin are unioned into the neighbouring pane sharing the longest border"""
  from shapely.ops import unary_union
  from shapely import STRtree
  P=list(P)
  while True:
    ar=[(g.area,i) for i,(c,g) in enumerate(P) if g.area<(gift_amin if c in GIFT else amin)]
    if not ar: return P
    a,i=min(ar); g=P[i][1]; best=None
    for j,(c2,g2) in enumerate(P):
      if j==i or g.distance(g2)>1e-6: continue
      L=g.boundary.intersection(g2.buffer(1e-6)).length
      if best is None or L>best[0]: best=(L,j)
    if best is None or best[0]<1e-6: P.pop(i); continue
    j=best[1]; u=unary_union([P[j][1],g.buffer(1e-6)]).buffer(-1e-6) if False else unary_union([P[j][1],g])
    if u.geom_type!='Polygon' : P.pop(i); continue
    P[j]=(P[j][0],u); P.pop(i)
GIFT=set()
def relabel(I,col):
  u,inv=np.unique(I,return_inverse=True); return inv.reshape(I.shape),np.array(col)[u]
def build(cfg,base):
  L,pal,asp,share=quant_stage(cfg,base); K=len(pal); H,W=L.shape
  gnames=set(cfg.get('gift_colors',[])); gci={k for k,p in enumerate(pal) if p['name'] in gnames or p['hex'] in gnames}
  bgi={k for k,p in enumerate(pal) if p['name'].startswith('background')}
  I,n=components(L); col=np.zeros(n,int)
  for k in range(K): col[np.unique(I[L==k])]=k
  mp=cfg.get('min_px',90); gp=cfg.get('gift_px',14)
  I=merge_small(I,col,lambda c:gp if c in gci else mp)
  I,col=relabel(I,col); colr=col[I]; I,n=components(colr); col=np.zeros(n,int)
  for k in range(K): col[np.unique(I[colr==k])]=k
  log('colour regions after merge',n)
  im=Image.open(os.path.join(base,cfg['image'])).convert('L').resize((W,H),Image.LANCZOS); gray=np.array(im,float)
  t=cfg.get('nat_px',700); bm=cfg.get('bg_mult',3.0)
  I,col=split_big(I,col,lambda c:t*(bm if c in bgi else 1),gray,cfg.get('aspect_cut',True))
  I=merge_small(I,col,lambda c:gp if c in gci else cfg.get('frag_px',60)); I,col=relabel(I,col)
  I,col=cut_holes(I,col); I,col=relabel(I,col)
  log('panes in raster',len(col))
  return I,col,pal,asp
def main(cfgp):
  t0=time.time(); cfg=json.load(open(cfgp)); base=os.path.dirname(os.path.abspath(cfgp))
  I,col,pal,asp=build(cfg,base); K=len(pal); Hn=1/asp; freeglass3.set_frame(1.0,Hn)
  q=np.array([[int(p['hex'][i:i+2],16) for i in (1,3,5)] for p in pal],np.uint8)[col[I]]
  Image.fromarray(q).resize((I.shape[1]*2,I.shape[0]*2),Image.NEAREST).save(cfg['out_prefix']+'_rast.png')
  R=vectorise(I,cfg.get('simplify_px',0.8),cfg.get('smooth_iter',1)); log('vector regions',len(R))
  global GIFT
  GIFT={k for k,p in enumerate(pal) if p['name'] in set(cfg.get('gift_colors',[])) or p['hex'] in set(cfg.get('gift_colors',[]))}
  P=[(int(col[v]),g2) for v,g in R for g2 in norm(g)]; log('raw',len(P)); P=merge_tiny(P,cfg.get('tiny_area',2e-4),cfg.get('gift_area',6e-5)); log('panes before snap',len(P))
  import pickle; pickle.dump(P,open(cfg['out_prefix']+'_pre.pkl','wb'))
  P,ncol=snap(P,post=True); pickle.dump(P,open(cfg['out_prefix']+'_post.pkl','wb')); sol=[c for c,_ in P]
  gnames=set(cfg.get('gift_colors',[])); gci={k for k,p in enumerate(pal) if p['name'] in gnames or p['hex'] in gnames}; gift=[i for i,c in enumerate(sol) if c in gci]
  Gs,fixed=export([g for _,g in P]); ok,nb,val=check(Gs); log('check',ok,val)
  for it in range(6):   # leftover ambiguous contacts: merge the smaller pane of each offending pair into the other, re-snap
    if ok: break
    from freeglass3 import adjacency
    from shapely.ops import unary_union
    _,amb,_,_=adjacency(Gs); drop=set()
    for i,j,L in amb:
      if i in drop or j in drop: continue
      a,b=(i,j) if Gs[i].area<Gs[j].area else (j,i); u=unary_union([Gs[b],Gs[a]])
      if u.geom_type=='Polygon': P[b]=(P[b][0],u); drop.add(a); log('merged pane',a,'->',b,'colours',P[a][0],P[b][0])
    P=[p for k,p in enumerate(P) if k not in drop]; P,ncol=snap(P,post=True); sol=[c for c,_ in P]; gift=[i for i,c in enumerate(sol) if c in gci]
    Gs,fixed=export([g for _,g in P]); ok,nb,val=check(Gs); log('check',ok,val)
  if not ok or any(not x for x in nb): raise SystemExit('geometry check failed')
  if not ok or any(not x for x in nb): raise SystemExit('geometry check failed')
  start,st=choose_start(sol,nb,K,seeds=cfg.get('start_seeds',4),gift=gift); log('starts',len(start),st)
  from autofill import simulate
  afc=cfg.get('autofill_budget',40); af=[]
  for x in list(start):
    tt=[y for y in start if y!=x]
    if not tt: continue
    f,u=simulate(sol,nb,K,tt,cap=afc+1,gift=gift)
    if u==0 and len(f)<=afc: start=tt; af=f
  log('starts',len(start),'autofills',len(af))
  rins=[rin(g) for g in Gs]; deg=[len(x) for x in nb]
  metrics=dict(pieces=len(Gs),colours=K,starts=len(start),**st,snapped_edges=ncol,pinch_repairs=fixed,**val,min_inradius=round(min(rins),4),degree_min=min(deg),degree_max=max(deg),
    degree_mean=round(sum(deg)/len(deg),2),autofills=len(af),gift=len(gift),max_badges=max(len({sol[j] for j in x}) for x in nb),gen_seconds=round(time.time()-t0))
  pieces=[]
  for g,r in zip(Gs,rins):
    pl=polylabel(g,1e-4); pieces.append(dict(p=[[x,round(Hn-y,5)] for x,y in ring(g)],pole=[round(pl.x,4),round(Hn-pl.y,4)],rin=round(r,4)))
  lv=dict(id=cfg['id'],name=cfg['name'],mode='free',aspect=round(asp,6),colors=[p['hex'] for p in pal],cnames=[p['name'] for p in pal],sol=sol,nb=nb,start=sorted(start),pieces=pieces,metrics=metrics)
  if gift: lv['gift']=gift
  json.dump(lv,open(cfg['out_prefix']+'.json','w')); log('done',json.dumps(metrics))
if __name__=='__main__': main(sys.argv[1])
