"""Readability preprocessing of a source photo before quantising: subject mask (rembg u2net), vibrant+contrasty edge-preserving smoothing,
and for subject pictures a clean contrasting 2-band background. usage: preprocess.py <in> <out> <mode subject|scene> [bg_hex]"""
import sys,colorsys
import numpy as np,cv2
from PIL import Image
MAXW=800
def enhance(bgr,sat=1.32,clahe=2.2,ms=(7,20)):
  lab=cv2.cvtColor(bgr,cv2.COLOR_BGR2LAB);l,a,b=cv2.split(lab)
  l=cv2.createCLAHE(clipLimit=clahe,tileGridSize=(6,6)).apply(l);bgr=cv2.cvtColor(cv2.merge([l,a,b]),cv2.COLOR_LAB2BGR)
  hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV).astype(np.float32);hsv[...,1]=np.clip(hsv[...,1]*sat,0,255);bgr=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR)
  for _ in range(2): bgr=cv2.bilateralFilter(bgr,9,40,7)
  return cv2.pyrMeanShiftFiltering(bgr,*ms)
def subject_mask(img):
  from rembg import remove,new_session
  m=np.array(remove(img,session=new_session(__import__('os').environ.get('REMBG_MODEL','u2net')),only_mask=True))
  m=(m>128).astype(np.uint8)
  sm=int(__import__('os').environ.get('MASK_SMOOTH','0'))
  if sm: m=(cv2.GaussianBlur(m.astype(np.float32),(0,0),sm)>0.5).astype(np.uint8)
  k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5));m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,k);m=cv2.morphologyEx(m,cv2.MORPH_OPEN,k)
  n,lab,st,_=cv2.connectedComponentsWithStats(m);keep=np.zeros_like(m);tot=m.sum()
  for i in range(1,n):
    if st[i,4]>=0.04*tot: keep[lab==i]=1
  # fill holes
  inv=1-keep;n,lab,st,_=cv2.connectedComponentsWithStats(inv)
  for i in range(1,n):
    x,y,w,h,a=st[i]
    if a<0.03*keep.size and not (x==0 or y==0 or x+w==keep.shape[1] or y+h==keep.shape[0]): keep[lab==i]=1
  if __import__('os').environ.get('MASK_HULL'): # subject made of separated parts (e.g. white stripes read as background): use the convex hull
    pts=cv2.findNonZero(keep);hull=cv2.convexHull(pts);keep=np.zeros_like(keep);cv2.fillConvexPoly(keep,hull,1)
  return keep
def pick_bg(rgb,m):
  px=rgb[m>0].astype(float)/255;mean=px.mean(0);h,l,s=colorsys.rgb_to_hls(*mean)
  # dominant hue of the saturated subject pixels
  hs=[colorsys.rgb_to_hls(*p) for p in px[::7]];sat=[x for x in hs if x[2]>.3 and .15<x[1]<.85]
  if sat: h=float(np.median([x[0] for x in sat]))
  hb=(h+.45)%1.0;dark=l>.5  # bright subject -> dark background and vice versa
  t=colorsys.hls_to_rgb(hb,.22 if dark else .86,.55);b=colorsys.hls_to_rgb(hb,.34 if dark else .74,.5)
  return [int(255*c) for c in t],[int(255*c) for c in b]
def main(inp,out,mode,bg=None):
  im=Image.open(inp).convert('RGB')
  if im.width>MAXW: im=im.resize((MAXW,round(im.height*MAXW/im.width)),Image.LANCZOS)
  rgb=np.array(im);bgr=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
  if mode=='scene':
    res=enhance(bgr,1.25,2.0,(8,22))
  else:
    m=subject_mask(im);fg=enhance(bgr);h,w=m.shape
    top,bot=pick_bg(rgb,m)
    if bg: top=bot=[int(bg[i:i+2],16) for i in (1,3,5)]
    g=np.linspace(0,1,h)[:,None,None];bgc=(np.array(top)[None,None,:]*(1-g)+np.array(bot)[None,None,:]*g)*np.ones((1,w,1))
    bgc=bgc[...,::-1].astype(np.uint8)  # to BGR
    soft=cv2.GaussianBlur(m.astype(np.float32),(0,0),1.1)[...,None]
    res=(fg*soft+bgc*(1-soft)).astype(np.uint8)
  if mode!='scene': # crop to the subject box (+margin) so the clean background does not swamp the picture
    ys,xs=np.where(m>0);pad=int(.07*max(xs.max()-xs.min(),ys.max()-ys.min()))
    res=res[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
  if mode!='scene' and __import__('os').environ.get('MASK_OUT'): np.save(__import__('os').environ['MASK_OUT'],m[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad])
  Image.fromarray(cv2.cvtColor(res,cv2.COLOR_BGR2RGB)).save(out,quality=94)
if __name__=='__main__': main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4] if len(sys.argv)>4 else None)
