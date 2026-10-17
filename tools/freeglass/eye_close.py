"""Eye/nose close-up: segment the eyes and nose from the full-resolution photo crop (upsampled x4) into small labelled regions
(dark lid/pupil, iris, catchlight, nose), vectorise them with shared borders and return them as polygons in window coordinates (x/photo_width, y/photo_width, y down)
together with their mean ORIGINAL colour (Lab).  The pieces tile their own footprint exactly; feature_first.py cuts that footprint out of the main pane map."""
import sys, os
import numpy as np, cv2
from scipy import ndimage
from PIL import Image
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import raster
from skimage.color import rgb2lab
from shapely.geometry import Polygon
from shapely.ops import unary_union
BOXES=[('eye',(941,374,992,412)),('eye',(1049,388,1107,424)),('nose',(1008,452,1068,522))]
UP=4
def comp_clean(L,minpx):
  out=L.copy()
  for k in np.unique(L):
    if k==0: continue
    lab,n=ndimage.label(L==k)
    for j in range(1,n+1):
      if (lab==j).sum()<minpx: out[lab==j]=0
  return out
def eye_pieces(photo,cfg):
  im=Image.open(photo).convert('RGB'); Wo=im.width; pad=cfg.get('eye_pad',12); minpx=cfg.get('eye_minpx',60)*UP*UP//4; out=[]
  for kind,(x0,y0,x1,y1) in BOXES:
    cx0,cy0,cx1,cy1=x0-pad,y0-pad,x1+pad,y1+pad; crop=im.crop((cx0,cy0,cx1,cy1)).resize(((cx1-cx0)*UP,(cy1-cy0)*UP),Image.BICUBIC)
    rgb=np.array(crop); hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV).astype(float); Hh=hsv[...,0]*2; S=hsv[...,1]/255; V=hsv[...,2]/255
    inner=np.zeros(V.shape,bool); m_=2*UP; inner[m_:-m_,m_:-m_]=True
    L=np.zeros(V.shape,np.uint8)
    if kind=='eye':
      dark=inner&(V<cfg.get('eye_dark_v',0.46)); iris=inner&(Hh>=cfg.get('iris_h0',32))&(Hh<110)&(S>cfg.get('iris_s',.38))&(V>.40)&(V<.86)
      iris=ndimage.binary_opening(iris,iterations=2)|(iris&ndimage.binary_dilation(dark,iterations=3)); iris&=~dark
      eyea=ndimage.binary_fill_holes(ndimage.binary_closing(dark|iris,iterations=UP*2)); iris=(iris|(eyea&~dark&(V>.40)&(V<.90)&(Hh>=28)))&~dark   # whole eye opening (olive iris + the pale rim of the slit) inside the dark lid
      L[dark]=1; L[iris]=2
    else:
      nose=inner&(V<cfg.get('nose_v',.66))&(S>cfg.get('nose_s',.32))&(Hh<35); nose=ndimage.binary_opening(ndimage.binary_closing(nose,iterations=UP),iterations=UP); lb,nn=ndimage.label(nose)
      if nn: sz=ndimage.sum(nose,lb,range(1,nn+1)); nose=lb==(1+int(np.argmax(sz)))
      L[nose]=4
    L=cv2.medianBlur(L,UP+1 if (UP+1)%2 else UP+1); L=comp_clean(L,minpx//2)
    # grow the footprint a little and fill holes: every pixel inside gets the nearest label
    F=L>0; F=ndimage.binary_fill_holes(F); F=ndimage.binary_dilation(F,iterations=cfg.get('eye_grow',UP)) if F.any() else F
    if not F.any(): continue
    idx=ndimage.distance_transform_edt(L==0,return_distances=False,return_indices=True); Lg=L[idx[0],idx[1]]; Lg[~F]=0
    if kind=='eye':   # catchlight: very bright pixels inside the footprint
      hl=F&(V>cfg.get('eye_hl_v',0.9))&ndimage.binary_dilation(Lg>0,iterations=0); hl=comp_clean(hl.astype(np.uint8)*3,minpx)>0
      Lg[hl]=3
    vec=raster.vectorise(Lg.astype(np.int32),cfg.get('eye_simp',1.2),cfg.get('eye_smooth',2)); Wc=Lg.shape[1]; lab=rgb2lab(rgb)
    pieces=[]
    for v,g in vec:
      if v==0: continue
      pg=Polygon([((cx0+x*Wc/UP)/Wo,(cy0+y*Wc/UP)/Wo) for x,y in g.exterior.coords],[[((cx0+x*Wc/UP)/Wo,(cy0+y*Wc/UP)/Wo) for x,y in r.coords] for r in g.interiors])
      m=(Lg==v); mean=lab[m].mean(0)
      if pg.area>cfg.get('eye_min_area',6e-5): pieces.append(dict(poly=pg,role={1:'dark',2:'iris',3:'light',4:'nose'}[v],lab=mean,kind=kind))
    out+=pieces
  return out
def debug(photo,cfg,out):
  pass
if __name__=='__main__':
  import json; cfg=json.load(open(sys.argv[1])); base=os.path.dirname(os.path.abspath(sys.argv[1]))
  ps=eye_pieces(os.path.join(base,cfg['image']),cfg); print(len(ps),[(p['kind'],p['role'],round(p['poly'].area*1e5)) for p in ps])
