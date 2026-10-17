"""Lead-line style natural panes (idea 3): natural.py's pipeline, but big regions are cut by CURVED lines instead of straight bisections.
 * cut curves are streamlines of the fur-direction field (structure tensor of the photo, orthogonal to the gradient), blended with the
   cross-the-long-axis direction for elongated regions, plus a gentle constant turning rate so every cut is a smooth arc;
 * strong long image edges (Canny on the photo) inside a region become cuts too: edge pixels as the core, extended along their end tangents
   until they leave the region so they really divide it;
 * a cut is a thick-1 8-connected curve rasterised into the pane-id image; vectorise() later smooths and simplifies it with shared borders.
usage: natural_c.py cfg.json   (natural.py options plus: nat_px, flow_blend, edge_len, canny, turn, cut_seed)"""
import sys, os, json
import numpy as np, cv2
from scipy import ndimage
from skimage.draw import line as skline
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import natural
from natural import log

def flow_field(gray,sg=1.2,st=7.0):
  g=ndimage.gaussian_filter(gray,sg); gy,gx=np.gradient(g)
  jxx=ndimage.gaussian_filter(gx*gx,st); jyy=ndimage.gaussian_filter(gy*gy,st); jxy=ndimage.gaussian_filter(gx*gy,st)
  th=0.5*np.arctan2(2*jxy,jxx-jyy)+np.pi/2
  coh=np.sqrt((jxx-jyy)**2+4*jxy**2)/(jxx+jyy+1e-6)
  return np.cos(th),np.sin(th),coh
def unit(v): n=np.hypot(*v); return v/n if n>1e-9 else v
def stream(p0,d0,mask,F,turn,blend,maxn=900):
  """trace from p0 along d0 until leaving mask; direction = persistence + field (sign aligned) + constant turning"""
  H,W=mask.shape; p=np.array(p0,float); d=unit(np.array(d0,float)); pts=[p.copy()]; ang=0.0
  for _ in range(maxn):
    x,y=int(round(p[0])),int(round(p[1]))
    if not(0<=x<W and 0<=y<H): break
    f=np.array([F[0][y,x],F[1][y,x]]); 
    if f@d<0: f=-f
    d=unit((1-blend)*d+blend*f*(0.5+F[2][y,x])); c,s=np.cos(turn),np.sin(turn); d=np.array([c*d[0]-s*d[1],s*d[0]+c*d[1]])
    p=p+d; pts.append(p.copy())
    if not mask[min(max(int(round(p[1])),0),H-1),min(max(int(round(p[0])),0),W-1)]: break
  return pts
def draw(pts,shape):
  B=np.zeros(shape,bool); H,W=shape
  q=[(min(max(int(round(a)),0),W-1),min(max(int(round(b)),0),H-1)) for a,b in pts]
  for (x0,y0),(x1,y1) in zip(q[:-1],q[1:]):
    rr,cc=skline(y0,x0,y1,x1); B[rr,cc]=True
  return B
def apply_cut(piece,B,minfrac):
  """split the piece (bool mask) by barrier B; returns list of masks or None"""
  rest=piece&~B; lab,n=ndimage.label(rest)
  if n<2: return None
  ar=ndimage.sum(rest,lab,range(1,n+1)); tot=ar.sum()
  if np.sort(ar)[-2]<minfrac*tot: return None
  idx=ndimage.distance_transform_edt(lab==0,return_distances=False,return_indices=True)
  full=lab[idx[0],idx[1]]; full[~piece]=0
  return [full==k for k in range(1,n+1)]
def curved_cut(piece,F,rng,cfg):
  ys,xs=np.nonzero(piece); P=np.stack([xs,ys],1).astype(float); c=P.mean(0); w,v=np.linalg.eigh(np.cov((P-c).T)+1e-9*np.eye(2)); major=v[:,1]; minor=v[:,0]
  asp=np.sqrt(w[1]/max(w[0],1e-9)); ext=np.sqrt(w[1])*3.4
  for att in range(10):
    t=(P-c)@major; q=0.5+rng.uniform(-.08,.08)*(att>0); s0=np.quantile(t,q)
    sel=np.abs(t-s0)<1.5; cand=P[sel] if sel.any() else P
    p0=cand[np.argmin(np.abs((cand-c)@minor))]
    x,y=int(p0[0]),int(p0[1]); fu=np.array([F[0][y,x],F[1][y,x]]); coh=F[2][y,x]
    if fu@minor<0: fu=-fu
    wf=cfg.get('flow_blend',0.65)*min(1,coh*2+0.3)*(0.5 if asp>2.2 else 1)*(1 if att<7 else 0)
    d0=unit(wf*fu+(1-wf)*minor)
    turn=rng.choice([-1,1])*rng.uniform(.5,1.0)*cfg.get('turn',1.1)/max(ext,10)
    a=stream(p0,d0,piece,F,turn,cfg.get('stream_blend',0.15)); b=stream(p0,-d0,piece,F,-turn,cfg.get('stream_blend',0.15))
    pts=b[::-1]+a[1:]; B=draw(pts,piece.shape)
    r=apply_cut(piece,B,cfg.get('min_frac',0.22))
    if r: return r
  return None
def edge_cuts(piece,E,F,cfg,t):
  """strong long edges inside the piece, extended along their end tangents until they leave the piece"""
  lab,n=ndimage.label(E&piece,structure=np.ones((3,3)))
  best=None
  for k in range(1,n+1):
    ys,xs=np.nonzero(lab==k)
    if len(ys)<cfg.get('edge_len',28): continue
    P=np.stack([xs,ys],1).astype(float); c=P.mean(0); w,v=np.linalg.eigh(np.cov((P-c).T)); ax=v[:,1]
    if np.sqrt(w[1])*3.4<cfg.get('edge_len',28)*0.8: continue
    o=np.argsort((P-c)@ax); core=P[o][::3]; 
    if len(core)<4: continue
    e0=unit(core[0]-core[min(3,len(core)-1)]); e1=unit(core[-1]-core[max(-4,-len(core))])
    a=stream(core[-1],e1,piece,F,0,0.1,300); b=stream(core[0],e0,piece,F,0,0.1,300)
    pts=b[::-1]+[tuple(p) for p in core]+a[1:]; B=draw(pts,piece.shape)
    r=apply_cut(piece,B,cfg.get('edge_min_frac',0.18))
    if r:
      sc=len(ys)
      if best is None or sc>best[0]: best=(sc,r)
  return best[1] if best else None
def split_big_curved(I,col,target,gray,cut_across=True,cfg=None):
  cfg=cfg or CFG; rng=np.random.RandomState(cfg.get('cut_seed',1)); F=flow_field(gray,st=cfg.get('flow_sigma',7.0))
  g8=np.clip(ndimage.gaussian_filter(gray,1.5),0,255).astype(np.uint8); E=cv2.Canny(g8,cfg.get('canny_lo',30),cfg.get('canny',70))>0
  I=I.copy(); col=list(col); nxt=I.max()+1; ncut=[0,0,0]
  work=list(range(len(col)))
  while work:
    p=work.pop(); m=I==p; a=int(m.sum()); t=target(col[p])
    if a<=1.5*t: continue
    r=None
    if cfg.get('use_edges',True) and a>=1.2*t:
      r=edge_cuts(m,E,F,cfg,t)
      if r: ncut[0]+=1
    if r is None:
      r=curved_cut(m,F,rng,cfg)
      if r: ncut[1]+=1
    if r is None:
      ncut[2]+=1; continue
    for k,mm in enumerate(r):
      if k==0: I[mm]=p; work.append(p)
      else: I[mm]=nxt; col.append(col[p]); work.append(nxt); nxt+=1
  log('cuts edge/curved/failed',ncut)
  return I,np.array(col)
CFG={}
def main(cfgp):
  global CFG
  CFG=json.load(open(cfgp)); natural.split_big=lambda I,col,target,gray,cut_across=True: split_big_curved(I,col,target,gray,cut_across,CFG)
  natural.main(cfgp)
if __name__=='__main__': main(sys.argv[1])
