"""Hand touch-ups of a preprocessed level source (keep features readable as panes).
  touchup.py cat   in.jpg out.jpg            -> blue eyes
  touchup.py cat2  in.jpg out.jpg            -> blue eyes with oval dark-brown pupil + rose nose accent (autofill era, more panes)
  touchup.py fish  in.jpg out.jpg            -> black eye
  touchup.py fox    in.jpg out.jpg            -> white chin piece next to the nose -> 2nd-lightest brown (was background blue)
  touchup.py macaw  in.jpg out.jpg            -> pale face patch -> lightest non-background blue
  touchup.py frog  in.jpg out.jpg mask.npy   -> belly + toes/fingers light green"""
import sys,numpy as np,cv2
kind,inp,out=sys.argv[1:4];bgr=cv2.imread(inp);h,w=bgr.shape[:2]
if kind in('cat','cat2'):
  # lighten the muzzle around the nose so it stands out (soft cream ellipse, blended)
  ov=bgr.copy();cv2.ellipse(ov,(535,222),(46,34),0,0,360,(200,235,252),-1,cv2.LINE_AA);msk=np.zeros((h,w),np.float32);cv2.ellipse(msk,(535,222),(46,34),0,0,360,1,-1,cv2.LINE_AA)
  msk=cv2.GaussianBlur(msk,(0,0),6)[...,None]*0.85;bgr=(bgr*(1-msk)+ov*msk).astype(np.uint8)
  # cat eyes: blue almond with a dark brown outline and a dark brown vertical slit pupil
  es=1 if kind=='cat' else float(__import__('os').environ.get('EYE_SCALE','.9'))   # cat2: natural, smaller eyes
  for cx,cy in ((503,168),(567,175)):
    cv2.ellipse(bgr,(cx,cy),(round(34*es),round(26*es)),-8,0,360,(14,26,42),-1,cv2.LINE_AA)           # outline  (BGR of #2a1a0e)
    cv2.ellipse(bgr,(cx,cy),(round(29*es),round(21*es)),-8,0,360,(232,143,47),-1,cv2.LINE_AA)          # blue iris (#2f8fe8)
    cv2.ellipse(bgr,(cx,cy),(5,19) if kind=='cat' else (7,12),0,0,360,(14,26,42),-1,cv2.LINE_AA)              # slit pupil (cat) / oval pupil (cat2)
  if kind=='cat2': cv2.ellipse(bgr,(535,205),(12,8),0,0,360,(138,92,196),-1,cv2.LINE_AA)   # nose: rose-brown accent (BGR of #c45c8a)
elif kind=='fish':
  cv2.circle(bgr,(103,136),17,(18,12,10),-1,cv2.LINE_AA)
elif kind in('fox','macaw'):
  hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV).astype(int);H,S,V=hsv[...,0]*2,hsv[...,1]/255,hsv[...,2]/255;yy,xx=np.mgrid[0:h,0:w]
  if kind=='fox': sel=(xx>=160)&(xx<=330)&(yy>=330)&(yy<=378)&(S<.16)&(V>.7);col=(87,132,169)        # BGR of #a98457
  else: sel=(xx>=295)&(xx<=445)&(yy>=285)&(yy<=392)&(V>.62)&((S<.14)|(H>250)|(H<40));col=(250,175,69)  # BGR of #45affa
  sel=cv2.morphologyEx(sel.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)).astype(bool);bgr[sel]=col;print(kind,'pixels painted',int(sel.sum()))
elif kind=='frog':
  m=np.load(sys.argv[4]).astype(bool);hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV).astype(int);H,S,V=hsv[...,0]*2,hsv[...,1]/255,hsv[...,2]/255
  yy,xx=np.mgrid[0:h,0:w]
  box=lambda x0,y0,x1,y1:(xx>=x0*w/430)&(xx<=x1*w/430)&(yy>=y0*h/394)&(yy<=y1*h/394)   # coordinates on the 430x394 processed frog
  # only the small circled regions: belly just under the head, and the toes / fingers (orange) -- the branch and the rest stay as they were
  belly=m&box(125,135,275,215)&(S<.5)&(V>.5)&~((H>70)&(H<170)&(S>.35))
  toes=m&(box(25,225,160,325)|box(150,195,235,300)|box(245,245,345,325))&((H>5)&(H<40)&(S>.55)&(V>.62))
  sel=(belly|toes).astype(np.uint8);sel=cv2.morphologyEx(sel,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8));sel=cv2.morphologyEx(sel,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)&m
  bgr[sel]=(90,225,170)   # BGR of light green #aae15a
cv2.imwrite(out,bgr,[cv2.IMWRITE_JPEG_QUALITY,94])
