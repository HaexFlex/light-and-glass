"""Distinct-palette quantiser: photo -> raster.py config.  python quant_cfg.py <id> "<Name>" <image> K panes [crop x0,y0,x1,y1 (fractions)] [extra_starts]
Clusters the (cropped, resized) picture in OKLab into 3K sub-clusters, merges them hierarchically into K glass colours, nudges the glass colours
apart until every pair is >= MIN_DE (OKLab x100) and adds a little chroma so they read as glass. Sub-cluster centres become the anchors."""
import sys,json,os,colorsys
import numpy as np
from PIL import Image
from scipy.cluster.vq import kmeans2
from scipy.cluster.hierarchy import linkage,fcluster
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from raster import oklab,h2rgb,de
MIN_DE=14
def hexs(rgb): return '#%02x%02x%02x'%tuple(int(max(0,min(255,round(v)))) for v in rgb)
def boost(rgb,s=1.18,v=1.0):
  h,l,sat=colorsys.rgb_to_hls(*[c/255 for c in rgb]); sat=min(1,sat*s); return [255*c for c in colorsys.hls_to_rgb(h,min(.95,l*v),sat)]
def name(rgb):
  h,l,s=colorsys.rgb_to_hls(*[c/255 for c in rgb]); h*=360
  if s<.12 or l>.93 or l<.1: return 'white' if l>.8 else ('black' if l<.2 else ('grey' if l>.5 else 'slate'))
  n=['red','orange','yellow','lime','green','green','cyan','sky','blue','violet','magenta','rose'][int(((h+15)%360)//30)]
  if n=='orange' and l<.35: n='brown'
  if n=='red' and l>.7: n='pink'
  return ('dark ' if l<.3 else 'pale ' if l>.75 else '')+n
def main(id_,nm,img,K,N,crop=None,extra=0,grid=None,seed=0):
  im=Image.open(img).convert('RGB')
  if crop: w,h=im.size;x0,y0,x1,y1=crop;im=im.crop((int(x0*w),int(y0*h),int(x1*w),int(y1*h)))
  asp=im.width/im.height; G=grid or (220 if N<150 else 300)
  sm=im.resize((G,round(G/asp)),Image.LANCZOS); px=np.array(sm).reshape(-1,3).astype(float); lab=oklab(px)
  np.random.seed(seed); sub=lab[np.random.choice(len(lab),min(len(lab),20000),replace=False)]
  C,_=kmeans2(sub,min(3*K,40),minit='++',seed=seed); lbl=np.argmin(((lab[:,None]-C)**2).sum(-1),1)
  keep=[i for i in range(len(C)) if (lbl==i).sum()>5]; C=C[keep]; lbl=np.argmin(((lab[:,None]-C)**2).sum(-1),1)
  cnt=np.array([(lbl==i).sum() for i in range(len(C))]); rgbc=np.array([px[lbl==i].mean(0) for i in range(len(C))])
  grp=fcluster(linkage(C,'ward'),K,'maxclust')
  groups=sorted(set(grp)); pal=[]
  for g in groups:
    m=grp==g; w=cnt[m]; mean=(rgbc[m]*w[:,None]).sum(0)/w.sum()
    pal.append(dict(rgb=mean,share=w.sum()/cnt.sum(),anchors=[hexs(r) for r in rgbc[m]]))
  # glass colours: boosted, then pushed apart if too close
  for p in pal: p['g']=boost(p['rgb'])
  for _ in range(40):
    moved=False
    for i in range(len(pal)):
      for j in range(i+1,len(pal)):
        d=de(hexs(pal[i]['g']),hexs(pal[j]['g']))
        if d<MIN_DE:
          moved=True;a,b=np.array(pal[i]['g']),np.array(pal[j]['g']);v=a-b
          v=v/(np.linalg.norm(v)+1e-9)*3; pal[i]['g']=list(np.clip(a+v,0,255)); pal[j]['g']=list(np.clip(b-v,0,255))
    if not moved: break
  pal.sort(key=lambda p:-p['share'])
  names={}
  for p in pal:
    n=name(p['g']);k=names.get(n,0);names[n]=k+1;p['name']=n if k==0 else f"{n} {k+1}"
  area=1/asp; sp=round((area/(1.13*N))**.5,4)
  cfg=dict(id=id_,name=nm,image=os.path.basename(img),grid=G,palette=[dict(name=p['name'],hex=hexs(p['g']),anchors=p['anchors']) for p in pal],
    crop=None,min_de=MIN_DE-2,median=3,mode_sizes=[3,3],min_region_px=max(25,int(G*G/asp/N/6)),simplify_px=0.9,smooth_iter=2,spacing=sp,rmin=round(.3*sp,4),
    max_seeds=10,start_seeds=4,min_starts=1,max_starts=4,extra_starts=extra,out_prefix=os.path.join(os.path.dirname(os.path.abspath(img)),'out_'+id_))
  if crop: # crop is applied here already (saved separately) so raster.py reads the cropped file
    p_=os.path.join(os.path.dirname(os.path.abspath(img)),id_+'.jpg'); im.save(p_,quality=92); cfg['image']=id_+'.jpg'
  del cfg['crop']
  json.dump(cfg,open(os.path.join(os.path.dirname(os.path.abspath(img)),id_+'.json'),'w'),indent=1)
  print(id_,'K',len(pal),'aspect',round(asp,3),'spacing',sp,[ (p['name'],round(p['share']*100)) for p in pal])
if __name__=='__main__':
  a=sys.argv; crop=[float(x) for x in a[6].split(',')] if len(a)>6 and a[6]!='-' else None
  main(a[1],a[2],a[3],int(a[4]),int(a[5]),crop,int(a[7]) if len(a)>7 else 0)
