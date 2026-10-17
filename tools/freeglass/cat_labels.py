"""Label image for the Ginger Cat from the ORIGINAL photo (no touch-ups, no background replacement): the photo's own background reduced to exactly 2 colours,
the cat to K_FUR fur colours, plus gift colours (dark details, iris) for tiny features.   usage: cat_labels.py <photo> <out_prefix> [grid_w] [k_fur]
writes <out_prefix>.npy (labels) and <out_prefix>_pal.json (palette entries incl. gift flags)."""
import sys,json,colorsys
import numpy as np,cv2
from PIL import Image
from scipy import ndimage
from scipy.cluster.vq import kmeans2
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from raster import oklab
from quant_cfg import boost,hexs,name
src,pref=sys.argv[1:3];W=int(sys.argv[3]) if len(sys.argv)>3 else 380;KF=int(sys.argv[4]) if len(sys.argv)>4 else 5
im=Image.open(src).convert('RGB');H=round(W*im.height/im.width);rgb=np.array(im.resize((W,H),Image.LANCZOS))
from rembg import remove,new_session
m=np.array(remove(im.resize((W*2,H*2),Image.LANCZOS),session=new_session('isnet-general-use'),only_mask=True)).astype(float)/255
m=cv2.resize(m,(W,H),interpolation=cv2.INTER_AREA)>0.5
lab_,n=ndimage.label(m);sz=ndimage.sum(m,lab_,range(1,n+1));m=lab_==(1+int(np.argmax(sz)));m=ndimage.binary_fill_holes(m)
m=cv2.medianBlur(m.astype(np.uint8)*255,5)>127
rgb_raw=rgb.copy()
sm=cv2.pyrMeanShiftFiltering(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),7,16);sm=cv2.cvtColor(sm,cv2.COLOR_BGR2RGB)
bgs=cv2.medianBlur(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),7);bgs=cv2.cvtColor(bgs,cv2.COLOR_BGR2RGB)
rgb=np.where(m[...,None],sm,bgs)   # smoothing only: no replacement, the photo's own background is kept
lab=oklab(rgb.astype(float));Lm=lab[...,0]
flat=lab.reshape(-1,3);mf=m.reshape(-1)
# background: exactly 2 colours
bgx=flat[~mf];c2,l2=kmeans2(bgx,2,minit='++',seed=3,iter=40)
bg_rgb=[np.median(rgb.reshape(-1,3)[~mf][l2==k],axis=0) for k in range(2)]
# subject: dark details, iris (yellow-green, face area), fur
hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV).astype(float);Hh=hsv[...,0]*2;S=hsv[...,1]/255;V=hsv[...,2]/255
sc=W/im.width;box=lambda x0,y0,x1,y1:(slice(max(0,int(y0*sc)),int(y1*sc)+1),slice(max(0,int(x0*sc)),int(x1*sc)+1))
hsv0=cv2.cvtColor(rgb_raw,cv2.COLOR_RGB2HSV).astype(float);V0=hsv0[...,2]/255;H0=hsv0[...,0]*2;S0=hsv0[...,1]/255
dark=m&(V<.2)
iris=np.zeros_like(m);nose=np.zeros_like(m)
for bx in ((941,374,992,412),(1049,388,1107,424)):   # the two eyes in the original photo (pixels): olive iris, dark lids/pupil
  r=box(*bx);sub=np.zeros_like(m);sub[r]=True
  iris|=sub&m&(H0>=31)&(H0<110)&(S0>.40)&(V0>.38)&(V0<.85);dark|=sub&m&(V0<.42)
r=box(1008,452,1068,522);sub=np.zeros_like(m);sub[r]=True;nose=sub&m&(V0<.62)&(S0<.62)&~dark
dark&=~nose
iris=ndimage.binary_opening(iris,iterations=1)|(iris&ndimage.binary_dilation(dark))
fur=m&~dark&~iris&~nose
fx=flat[fur.reshape(-1)];cf,lf=kmeans2(fx,3*KF,minit='++',seed=1,iter=40)
from scipy.cluster.hierarchy import linkage,fcluster
Z=linkage(cf,'ward',);cl=fcluster(Z,KF,'maxclust')
fur_rgb=[];rgbf=rgb.reshape(-1,3)[fur.reshape(-1)]
Lf=np.zeros(len(fx),int)
for k in range(1,KF+1):
  idx=np.isin(lf,np.where(cl==k)[0]);Lf[idx]=k-1;fur_rgb.append(np.median(rgbf[idx],axis=0))
order=np.argsort([colorsys.rgb_to_hls(*(c/255))[1] for c in fur_rgb]);remap=np.zeros(KF,int);remap[order]=range(KF);Lf=remap[Lf];fur_rgb=[fur_rgb[i] for i in order]
labels=np.zeros((H,W),np.uint8)
bgl=l2.reshape(-1)
tmp=np.zeros(H*W,np.uint8);tmp[~mf]=bgl;bgmap=tmp.reshape(H,W).copy();bgmap=ndimage.median_filter(bgmap,size=7);tmp=np.where(mf,0,bgmap.reshape(-1)).astype(np.uint8);tmp[fur.reshape(-1)]=2+Lf;labels=tmp.reshape(H,W)
labels[dark]=2+KF;labels[iris]=3+KF;labels[nose]=4+KF
np.save(pref+'.npy',labels)
pal=[]
for k,c in enumerate(bg_rgb): pal.append(dict(name=['wall','plank'][k] if False else 'background '+str(k+1),hex=hexs(c),gift=False))
for k,c in enumerate(fur_rgb): pal.append(dict(name='fur '+str(k+1),hex=hexs(boost(c,1.12)),gift=False))
pal.append(dict(name='dark',hex='#241810',gift=True));pal.append(None);ir=np.median(rgb[iris],axis=0) if iris.any() else np.array([160,150,60]);pal[-1]=dict(name='iris',hex=hexs(boost(ir,1.3)),gift=True);nr=np.median(rgb_raw[nose],axis=0) if nose.any() else np.array([150,90,80]);pal.append(dict(name='nose',hex=hexs(boost(nr,1.2)),gift=True))
json.dump(pal,open(pref+'_pal.json','w'),indent=1)
print('nose px',int(nose.sum()));print('bg',[p['hex'] for p in pal[:2]],'fur',[p['hex'] for p in pal[2:2+KF]],'dark px',int(dark.sum()),'iris px',int(iris.sum()),'grid',W,H)
vis=np.array([[int(p['hex'][i:i+2],16) for i in (1,3,5)] for p in pal],np.uint8)[labels];Image.fromarray(vis).resize((W*2,H*2),Image.NEAREST).save(pref+'_prev.png')
