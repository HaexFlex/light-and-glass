"""Detail panes: a pane may carry a small painted image (cut from the photo, reduced to a few colours) clipped to its shape.
LEVEL FORMAT
  level['detail'] = [pane indices]                      (sorted; like level['gift']; part of the fingerprint only when present)
  level['pieces'][i]['detail'] = {'s': 100000, 'pal': ['#rrggbb', ...], 'poly': [[colour index, [x0,y0,x1,y1,...]], ...]}
     polygons are painter-ordered, in the SAME coordinate space as pieces[i]['p'] (window coordinates as stored; the game draws them with the same
     transform as the pane), stored as integers = round(coordinate * s); each is already clipped to the pane outline, so the game only adds a clipPath
     as a safety net.  The logic colour of a detail pane is its normal level['sol'][i] (it counts as a neighbour for badges, is not in the player's palette
     unless another pane uses that colour, is never tapped/cracked and is not part of the win input).
  Reveal: a detail pane shows as plain unlit glass until at least one neighbour is locked (start / placed / autofilled), then it lights with a sparkle
  (plain fade with reduced motion). Solver/validator model: its colour is unknown until a neighbour is lit (freeglass2.solve(..., detail=)).
make_detail(photo, pane_polygon, crop=None, k=4, ...) builds the art dict; usage: detail_art.py level.json photo idx[,idx...] [--crop x0,y0,x1,y1] [--k 4] [--out file]"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy.cluster.vq import kmeans2
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import raster
from shapely.geometry import Polygon, box
from scipy import ndimage
S=100000
def make_detail(photo,pane,aspect,crop=None,k=4,grid=56,simp=0.7,smooth=1,min_frac=0.004,seed=0,dominant=False):
  """photo: path; pane: shapely Polygon in stored window coords (y flipped like pieces[i]['p']); aspect = window width/height.
  crop: (x0,y0,x1,y1) photo pixels painted onto the pane's bounding box (default: the photo area under the pane)."""
  im=Image.open(photo).convert('RGB'); Wp=im.width; Hn=1/aspect
  x0,y0,x1,y1=pane.bounds
  if crop is None: crop=(x0*Wp,(Hn-y1)*Wp,x1*Wp,(Hn-y0)*Wp)
  bw,bh=x1-x0,y1-y0; gh=max(8,round(grid*bh/bw)); rgb=np.array(im.crop(tuple(int(round(c)) for c in crop)).resize((grid,gh),Image.LANCZOS)).astype(float)
  rs=np.random.RandomState(seed); flat=rgb.reshape(-1,3); cen,lab=kmeans2(flat,k,minit='++',seed=seed,iter=30); lab=lab.reshape(gh,grid)
  lab=ndimage.median_filter(lab,3,mode='nearest')
  # drop unused clusters, order by luminance (dark first) for stable palettes
  used=sorted(set(lab.ravel().tolist())); cen=np.array([flat[lab.ravel()==u].mean(0) for u in used]); remap={u:i for i,u in enumerate(used)}; lab=np.vectorize(remap.get)(lab)
  order=np.argsort(cen@np.array([.3,.59,.11])); inv=np.empty(len(order),int); inv[order]=range(len(order)); lab=inv[lab]; cen=cen[order]
  vec=raster.vectorise(lab.astype(np.int32),simp,smooth)   # polygons in raster-normalised coords: x/grid, y/grid (y down)
  polys=[]
  for v,g in vec:
    pts=lambda c:[(x0+x*bw, y1-y*grid/gh*bh) for x,y in c]
    q=Polygon(pts(g.exterior.coords),[pts(r.coords) for r in g.interiors]).buffer(0).intersection(pane)
    for part in getattr(q,'geoms',[q]):
      if part.geom_type=='Polygon' and part.area>min_frac*pane.area: polys.append((int(v),part))
  # holes are filled by painting larger regions first
  polys.sort(key=lambda t:-t[1].area)
  out=[]
  for v,g in polys:
    for part in ([g] if not g.interiors else [g]):
      c=[round(v_*S) for xy in list(part.simplify(pane.length*0.004).exterior.coords)[:-1] for v_ in xy]
      out.append([v,c])
  hexes=['#%02x%02x%02x'%tuple(int(round(t)) for t in c) for c in cen]
  art=dict(s=S,pal=hexes,poly=out)
  if dominant: # colour (index into pal) covering the largest area of the pane = its logic colour
    ar=np.zeros(len(hexes))
    for v,c in out:
      pp=Polygon(list(zip(c[0::2],c[1::2]))); ar[v]+=pp.area
    # painter order covers earlier polygons, so use pixel shares instead: fraction of grid pixels per label
    art['dom']=int(np.bincount(lab.ravel(),minlength=len(hexes)).argmax())
  return art
def mark(level,idx,photo,**kw):
  """attach art to panes idx (list) of a level dict (in place) and update level['detail']"""
  for i in idx:
    pane=Polygon(level['pieces'][i]['p']); level['pieces'][i]['detail']=make_detail(photo,pane,level.get('aspect',1),**kw)
  level['detail']=sorted(set(level.get('detail',[]))|set(idx)); return level
if __name__=='__main__':
  a=sys.argv; lv=json.load(open(a[1])); idx=[int(x) for x in a[3].split(',')]
  kw={}
  if '--crop' in a: kw['crop']=tuple(float(x) for x in a[a.index('--crop')+1].split(','))
  if '--k' in a: kw['k']=int(a[a.index('--k')+1])
  mark(lv,idx,a[2],**kw); out=a[a.index('--out')+1] if '--out' in a else a[1]
  json.dump(lv,open(out,'w'),separators=(',',':')); print('detail panes',lv['detail'],'bytes',sum(len(json.dumps(lv['pieces'][i]['detail'])) for i in idx))
