"""Feature-first cat: cut the full-colour photo along its features FIRST, reduce colours AFTER (palette chosen from panes, not pixels).
 1. denoise lightly, subject mask (rembg), SLIC superpixels split by the mask, greedy Ward-like merging by Lab colour with an edge-contrast penalty
    (cat/background never merge; regions in the feature boxes are protected) down to N fur / N background regions;
 2. natural_c's curved flow/edge cuts for big regions, hole cuts, merge fragments, one shared-border vectorisation (raster.vectorise), snap/check;
 3. each pane gets its mean original colour (Lab); fur panes are clustered into k_fur colours, background panes into exactly 2;
 4. feature tiles (small panes whose colour is far from every palette colour: eyes, pupils, nose...) are removed from the clustering and become gift
    panes that keep (clusters of) their own colours; the rest runs through the usual start/autofill search.
usage: feature_first.py cfg.json"""
import sys, os, json, time, heapq
import numpy as np, cv2
from scipy import ndimage
from PIL import Image, ImageDraw
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import natural, natural_c, raster
from natural import log, components, borders, relabel
from freeglass import rin
from freeglass2 import choose_start, norm
import freeglass3
from freeglass3 import snap, export, check, ring, adjacency
from skimage.segmentation import slic
from skimage.color import rgb2lab, lab2rgb
import rasterio.features
from shapely.geometry import Polygon
from shapely.ops import polylabel, unary_union
BOXES=[(941,374,992,412),(1049,388,1107,424),(1008,452,1068,522)]   # eyes and nose in the original photo (px), as in cat_labels.py
def prep(cfg,base):
  im=Image.open(os.path.join(base,cfg['image'])).convert('RGB'); W=cfg.get('grid',480); H=round(W*im.height/im.width)
  rgb=np.array(im.resize((W,H),Image.LANCZOS)); den=cv2.fastNlMeansDenoisingColored(rgb,None,cfg.get('denoise',4),cfg.get('denoise',4),5,15)
  mp=os.path.join(base,cfg.get('mask','cat_mask.npy'))
  if os.path.exists(mp): m=np.load(mp)
  else:
    from rembg import remove,new_session
    mm=np.array(remove(im.resize((W*2,H*2),Image.LANCZOS),session=new_session('isnet-general-use'),only_mask=True)).astype(float)/255
    mm=cv2.resize(mm,(W,H),interpolation=cv2.INTER_AREA)>0.5; lab_,n=ndimage.label(mm); sz=ndimage.sum(mm,lab_,range(1,n+1)); mm=lab_==(1+int(np.argmax(sz)))
    mm=ndimage.binary_fill_holes(mm); m=cv2.medianBlur(mm.astype(np.uint8)*255,5)>127; np.save(mp,m)
  sc=W/im.width; boxes=[(int(a*sc)-cfg.get('box_pad',5),int(b*sc)-cfg.get('box_pad',5),int(c*sc)+cfg.get('box_pad',5),int(d*sc)+cfg.get('box_pad',5)) for a,b,c,d in BOXES]
  return den,m,boxes
def merge_regions(I,lab,mask,boxes,cfg):
  """greedy agglomeration on the region adjacency graph"""
  n=I.max()+1; area=np.bincount(I.ravel(),minlength=n).astype(float); S=np.stack([np.bincount(I.ravel(),weights=lab[...,k].ravel(),minlength=n) for k in range(3)],1)
  role=np.array([int(mask[I==k][0]) for k in range(n)]) if False else np.zeros(n,int)
  ys,xs=np.indices(I.shape); role=(np.bincount(I.ravel(),weights=mask.ravel().astype(float),minlength=n)/np.maximum(area,1)>0.5).astype(int)
  cx=np.bincount(I.ravel(),weights=xs.ravel(),minlength=n)/np.maximum(area,1); cy=np.bincount(I.ravel(),weights=ys.ravel(),minlength=n)/np.maximum(area,1)
  prot=np.array([any(b[0]<=cx[k]<=b[2] and b[1]<=cy[k]<=b[3] for b in boxes) for k in range(n)])
  nbr=[dict() for _ in range(n)]
  for dx,dy in ((1,0),(0,1)):
    a=I[:I.shape[0]-dy,:I.shape[1]-dx]; b=I[dy:,dx:]; c=np.linalg.norm(lab[:I.shape[0]-dy,:I.shape[1]-dx]-lab[dy:,dx:],axis=2); m=a!=b
    for p,q,cc in zip(a[m],b[m],c[m]):
      for u,v in ((p,q),(q,p)):
        s=nbr[u].get(v,(0.0,0)); nbr[u][v]=(s[0]+cc,s[1]+1)
  parent=np.arange(n); alive=np.ones(n,bool); ver=np.zeros(n,int); cnt={0:int((role==0).sum()),1:int((role==1).sum())}; tgt={0:cfg.get('n_bg',40),1:cfg.get('n_fur',130)}
  def cost(p,q):
    if role[p]!=role[q]: return None
    mp=S[p]/area[p]; mq=S[q]/area[q]; dE=np.linalg.norm(mp-mq); s,c=nbr[p][q]; bc=s/c
    w=np.sqrt(2*area[p]*area[q]/(area[p]+area[q])); k=w*(dE+cfg.get('edge_w',1.0)*bc)
    if prot[p] or prot[q]:
      if dE>cfg.get('prot_de',9) or prot[p]!=prot[q]: k*=cfg.get('prot_mult',6.0)
    return k
  hp=[]
  for p in range(n):
    for q in nbr[p]:
      if p<q:
        k=cost(p,q)
        if k is not None: heapq.heappush(hp,(k,p,q,0,0))
  while hp:
    k,p,q,vp,vq=heapq.heappop(hp)
    if not(alive[p] and alive[q]) or ver[p]!=vp or ver[q]!=vq: continue
    r=role[p]
    if cnt[r]<=tgt[r]: continue
    # merge q into p
    alive[q]=False; parent[q]=p; cnt[r]-=1; area_p=area[p]; S[p]+=S[q]; area[p]+=area[q]; prot[p]=prot[p] and prot[q] if area[p]>cfg.get('prot_max',450) else (prot[p] or prot[q]); ver[p]+=1
    for v,(s,c) in nbr[q].items():
      if v==p: continue
      o=nbr[p].get(v,(0.0,0)); nbr[p][v]=(o[0]+s,o[1]+c); nbr[v][p]=nbr[p][v]; nbr[v].pop(q,None)
    nbr[p].pop(q,None)
    for v in nbr[p]:
      if alive[v]:
        kk=cost(p,v)
        if kk is not None: heapq.heappush(hp,(kk,min(p,v),max(p,v),ver[min(p,v)],ver[max(p,v)]))
  root=parent.copy()
  for k in range(n):
    while root[k]!=root[root[k]]: root[k]=root[root[k]]
  J=root[I]; u,inv=np.unique(J,return_inverse=True); J=inv.reshape(J.shape)
  return J,role[u],prot[u]
def blunt(P,minang=10.0,d=0.012,rounds=40):
  """cut off sharp pane tips (angle < minang) at interior vertices of a lead segment: v -> v1,v2 on the two edges (shared by both panes, tiling kept)"""
  import math
  from freeglass3 import lead, faces_to_panes, angles
  from shapely.geometry import LineString
  done=0; skip=set()
  for _ in range(rounds):
    hit=None
    for _,g in P:
      r=ring(g); A=angles(r); n=len(r)
      for k in range(n):
        if A[k]<minang and (round(r[k][0],6),round(r[k][1],6)) not in skip: hit=(r[k],r[k-1],r[(k+1)%n]); break
      if hit: break
    if not hit: break
    v,a,b=hit; key=(round(v[0],6),round(v[1],6)); skip.add(key); segs=lead(P); new=[]; ok=False
    for sg in segs:
      c=list(sg.coords)
      for t in range(1,len(c)-1):
        if math.dist(c[t],v)<1e-9:
          la,lb=math.dist(v,a),math.dist(v,b); da=min(d,.4*la); db=min(d,.4*lb)
          v1=(v[0]+(a[0]-v[0])/la*da,v[1]+(a[1]-v[1])/la*da); v2=(v[0]+(b[0]-v[0])/lb*db,v[1]+(b[1]-v[1])/lb*db)
          # keep orientation along the segment
          if math.dist(c[t-1],a)<1e-9 or math.dist(c[t-1],v1)<math.dist(c[t-1],v2) and math.dist(c[t-1],a)<math.dist(c[t-1],b): c=c[:t]+[v1,v2]+c[t+1:]
          else: c=c[:t]+[v2,v1]+c[t+1:]
          ok=True; break
      new.append(LineString(c))
    if not ok: continue
    Q=faces_to_panes(new,P)
    if Q and all(g.is_valid for _,g in Q) and len(Q)==len(P): P=Q; done+=1
  return P,done
def smooth_labels(J,region,sigma):
  """majority-style label smoothing inside `region` (bool mask): every pixel takes the label with the largest gaussian-weighted share; region borders stay fixed"""
  if sigma<=0: return J
  ids=np.unique(J[region]); best=np.full(J.shape,-1.0); out=J.copy()
  for k in ids:
    g=ndimage.gaussian_filter((J==k)&region.astype(bool)*1.0,sigma) if False else ndimage.gaussian_filter(((J==k)&region).astype(float),sigma)
    up=(g>best)&region; best[up]=g[up]; out[up]=k
  return out
def lab_means(J,lab,n):
  ar=np.bincount(J.ravel(),minlength=n).astype(float); return np.stack([np.bincount(J.ravel(),weights=lab[...,k].ravel(),minlength=n)/np.maximum(ar,1) for k in range(3)],1),ar
def wkmeans(X,w,k,seed=0,iters=60,restarts=6):
  rs=np.random.RandomState(seed); best=None
  for _ in range(restarts):
    C=[X[rs.choice(len(X),p=w/w.sum())]]
    for _ in range(k-1):
      d=np.min([((X-c)**2).sum(1) for c in C],0)*w; C.append(X[rs.choice(len(X),p=d/d.sum())])
    C=np.array(C)
    for _ in range(iters):
      a=np.argmin(((X[:,None]-C[None])**2).sum(2),1)
      for j in range(k):
        if (a==j).any(): C[j]=np.average(X[a==j],axis=0,weights=w[a==j])
    a=np.argmin(((X[:,None]-C[None])**2).sum(2),1); inert=(w*((X-C[a])**2).sum(1)).sum()
    if best is None or inert<best[0]: best=(inert,C.copy(),a.copy())
  return best[1],best[2]
def hexl(l): 
  c=np.clip(lab2rgb(np.array(l,float).reshape(1,1,3))[0,0],0,1); return '#%02x%02x%02x'%tuple(int(round(v*255)) for v in c)
def segment_stage(cfg,base):
  den,m,boxes=prep(cfg,base); lab=rgb2lab(den); H,W=m.shape
  sl=slic(den,n_segments=cfg.get('n_sp',1600),compactness=cfg.get('compact',6),start_label=0,enforce_connectivity=True,channel_axis=2,sigma=1.0)
  I,n=components(sl*2+m.astype(int)); I=I.astype(int)
  log('superpixels',n); J,role,prot=merge_regions(I,lab,m,boxes,cfg); log('merged regions',J.max()+1,'fur',int(role.sum()),'bg',int((role==0).sum()))
  return den,lab,m,boxes,J,role,prot
def main(cfgp):
  t0=time.time(); cfg=json.load(open(cfgp)); base=os.path.dirname(os.path.abspath(cfgp))
  den,lab,m,boxes,J,role,prot=segment_stage(cfg,base); H,W=m.shape; Hn=H/W; freeglass3.set_frame(1.0,Hn)
  if cfg.get('smooth_bg',0) or cfg.get('smooth_fur',0):
    J=smooth_labels(J,~m.astype(bool),cfg.get('smooth_bg',0)); J=smooth_labels(J,m.astype(bool),cfg.get('smooth_fur',0))
    J,nn=components(J); J=J.astype(int); fr=np.bincount(J.ravel(),weights=m.ravel().astype(float),minlength=nn)/np.maximum(np.bincount(J.ravel(),minlength=nn),1)
    role=(fr>0.5).astype(int); prot=np.zeros(nn,bool); log('after label smoothing',nn)
  col=np.where(prot&(np.bincount(J.ravel())<cfg.get('prot_max',450)),3,np.where(role==1,2,0)); gray=np.array(Image.fromarray(den).convert('L'),float)
  Image.fromarray((np.stack([ (J*37)%255,(J*91)%255,(J*53)%255],2)).astype(np.uint8)).resize((W*2,H*2),Image.NEAREST).save(cfg['out_prefix']+'_regions.png')
  natural_c.CFG=cfg; I,col=natural_c.split_big_curved(J,col,lambda c:cfg.get('nat_px',600)*(cfg.get('bg_mult',3.5) if c==0 else 1),gray,True,cfg)
  gp=cfg.get('gift_px',14); I=natural.merge_small(I,col,lambda c:gp if c==3 else cfg.get('frag_px',60)); I,col=relabel(I,col); I,col=natural.cut_holes(I,col); I,col=relabel(I,col)
  natural.GIFT={3}; log('panes in raster',len(col))
  R=raster.vectorise(I,cfg.get('simplify_px',0.8),cfg.get('smooth_iter',1)); log('vector regions',len(R))
  P=[(int(col[v]),g2) for v,g in R for g2 in norm(g)]; P=natural.merge_tiny(P,cfg.get('tiny_area',2e-4),cfg.get('gift_area',6e-5)); log('panes before snap',len(P))
  EP=[]
  if cfg.get('eyes'):
    import eye_close
    from shapely.geometry import LineString
    from shapely.ops import split as shsplit
    EP=eye_close.eye_pieces(os.path.join(base,cfg['image']),cfg); F=unary_union([e['poly'] for e in EP]); log('eye/nose pieces',len(EP),'footprint area',round(F.area,5))
    Q=[]
    for c,g in P:
      if not g.intersects(F): Q.append((c,g)); continue
      stack=[x for x in getattr(g.difference(F),'geoms',[g.difference(F)]) if x.geom_type=='Polygon']
      while stack:
        x=stack.pop()
        if x.area<1e-10: continue
        if x.interiors:   # a pane around an eye keeps a hole: cut it through the hole (vertical line) so panes stay hole-free
          hc=Polygon(x.interiors[0]).centroid; parts=shsplit(x,LineString([(hc.x,-1),(hc.x,3)]))
          stack+=[p for p in parts.geoms if p.geom_type=='Polygon']
        else: Q.append((c,x))
    for e in EP: Q.append((3,e['poly']))
    P=natural.merge_tiny(Q,cfg.get('tiny_area',2e-4),cfg.get('gift_area',6e-5)); log('panes with eye pieces',len(P))
  P,ncol=snap(P,post=True); Gs,fixed=export([g for _,g in P]); ok,nb,val=check(Gs); log('check',ok,val)
  for it in range(6):
    if ok: break
    from freeglass3 import adjacency
    _,amb,_,_=adjacency(Gs); drop=set()
    for i,j,L in amb:
      if i in drop or j in drop: continue
      a,b=(i,j) if Gs[i].area<Gs[j].area else (j,i); u=unary_union([Gs[b],Gs[a]])
      if u.geom_type=='Polygon': P[b]=(P[b][0],u); drop.add(a)
    log('merged',len(drop)); P=[p for k,p in enumerate(P) if k not in drop]; P,ncol=snap(P,post=True); Gs,fixed=export([g for _,g in P]); ok,nb,val=check(Gs); log('check',ok,val)
  if not ok or any(not x for x in nb): raise SystemExit('geometry check failed')
  if cfg.get('blunt',10.0):
    P2,nb_=blunt([(c,g) for (c,_),g in zip(P,Gs)],cfg.get('blunt',10.0)); log('blunted tips',nb_)
    if nb_:
      G2,_=export([g for _,g in P2]); ok2,nb2,val2=check(G2)
      if ok2 and not any(not x for x in nb2): P,Gs,nb,val=P2,G2,nb2,val2; log('check after blunt',val)
      else: log('blunt rejected',val2)
  N=len(Gs)
  # ---- colours: mean original colour per pane, then cluster
  mean=np.zeros((N,3)); fur=np.zeros(N,bool); area=np.zeros(N); inbox=np.zeros(N,bool)
  for i,g in enumerate(Gs):
    pg=Polygon([(x*W,y*W) for x,y in ring(g)]); mk=rasterio.features.rasterize([(pg,1)],out_shape=(H,W)).astype(bool)
    if not mk.any(): ys,xs=int(pg.centroid.y),int(pg.centroid.x); mk=np.zeros((H,W),bool); mk[min(ys,H-1),min(xs,W-1)]=True
    mean[i]=lab[mk].mean(0); fur[i]=m[mk].mean()>0.5; area[i]=g.area; c=pg.centroid; inbox[i]=any(b[0]<=c.x<=b[2] and b[1]<=c.y<=b[3] for b in boxes)
  def de(a,b): return np.linalg.norm(a-b,axis=-1)
  cand=np.zeros(N,bool)
  def palette(excl):
    C=[];asg=np.full(N,-1)
    cb,ab=wkmeans(mean[~fur&~excl],area[~fur&~excl],2,seed=1); C+=list(cb); 
    ca,aa=wkmeans(mean[fur&~excl],area[fur&~excl],cfg.get('k_fur',5),seed=2); o=np.argsort(ca[:,0]); ca=ca[o]; C+=list(ca); C=np.array(C); C[:,1:]*=cfg.get('sat',1.0); return C
  eyeg=np.zeros(N,bool); eyelab={}
  if EP:
    for i,g in enumerate(Gs):
      best=None
      for j,e in enumerate(EP):
        a=g.intersection(e['poly']).area
        if a>0.5*g.area and (best is None or a>best[0]): best=(a,j)
      if best: eyeg[i]=True; eyelab[i]=EP[best[1]]['lab']
    for i,l in eyelab.items(): mean[i]=l
    log('eye/nose gift panes',int(eyeg.sum()))
  C0=palette(eyeg); dn=np.array([de(mean[i],C0[(0 if not fur[i] else 2):(2 if not fur[i] else len(C0))]).min() for i in range(N)])
  gift=eyeg.copy() if EP else (area<cfg.get('gift_max_area',2.5e-3))&(((inbox)&(dn>cfg.get('gift_de_box',12)))|(dn>cfg.get('gift_de',24))&(area<cfg.get('gift_max_area2',9e-4)))&fur if not EP else gift
  log('feature-tile candidates',int(gift.sum()))
  C=palette(gift); nbg=2; kf=len(C)-2
  sol=np.zeros(N,int)
  for i in range(N):
    if gift[i]: continue
    r=range(2,len(C)) if fur[i] else range(0,2); sol[i]=min(r,key=lambda k:de(mean[i],C[k]))
  gi=np.nonzero(gift)[0]; gcols=[]
  if len(gi):
    ng=min(cfg.get('n_gift',5),len(gi)); cg,ag=wkmeans(mean[gi],np.maximum(area[gi],1e-6),ng,seed=3); 
    for j,i in enumerate(gi): sol[i]=len(C)+ag[j]
    C=np.vstack([C,cg]); 
    # drop unused gift colours
  used=sorted(set(sol.tolist())); remap={k:j for j,k in enumerate(used)}; sol=[remap[int(c)] for c in sol]; C=C[used]
  names=[];nf=0;ng_=0
  for k in used:
    if k<2: names.append('background %d'%(k+1))
    elif k<2+kf: nf+=1; names.append('fur %d'%nf)
    else: ng_+=1; names.append('gift %d'%ng_)
  gift_idx=[i for i in range(N) if gift[i]]; K=len(C)
  log('palette',K,'colours; gift panes',len(gift_idx))
  if any(len(set(sol[j] for j in x))==0 for x in nb): raise SystemExit('bad nb')
  start,st=choose_start(sol,nb,K,seeds=cfg.get('start_seeds',4),gift=gift_idx); log('starts',len(start),st)
  from autofill import simulate
  afc=cfg.get('autofill_budget',60); af=[]
  for x in list(start):
    tt=[y for y in start if y!=x]
    if not tt: continue
    f,u=simulate(sol,nb,K,tt,cap=afc+1,gift=gift_idx)
    if u==0 and len(f)<=afc: start=tt; af=f
  log('starts',len(start),'autofills',len(af))
  rins=[rin(g) for g in Gs]; deg=[len(x) for x in nb]
  metrics=dict(pieces=N,colours=K,starts=len(start),**st,snapped_edges=ncol,**val,min_inradius=round(min(rins),4),degree_min=min(deg),degree_max=max(deg),degree_mean=round(sum(deg)/len(deg),2),
    autofills=len(af),gift=len(gift_idx),max_badges=max(len({sol[j] for j in x}) for x in nb),gen_seconds=round(time.time()-t0))
  pieces=[]
  for g,r in zip(Gs,rins):
    pl=polylabel(g,1e-4); pieces.append(dict(p=[[x,round(Hn-y,5)] for x,y in ring(g)],pole=[round(pl.x,4),round(Hn-pl.y,5)],rin=round(r,4)))
  hexes=[hexl(c) for c in C]
  lv=dict(id=cfg['id'],name=cfg['name'],mode='free',aspect=round(W/H,6),colors=hexes,cnames=names,sol=sol,nb=nb,start=sorted(start),pieces=pieces,metrics=metrics)
  if gift_idx: lv['gift']=gift_idx
  json.dump(lv,open(cfg['out_prefix']+'.json','w')); log('done',json.dumps(metrics))
  q=Image.new('RGB',(W*2,H*2),(0,0,0)); d=ImageDraw.Draw(q)
  for g,c in zip(Gs,sol): d.polygon([(x*W*2,y*W*2) for x,y in ring(g)],fill=hexes[c])
  q.save(cfg['out_prefix']+'_quant.png')
if __name__=='__main__': main(sys.argv[1])
