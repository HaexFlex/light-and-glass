"""Hand touch-ups of a preprocessed level source (keep features readable as panes).
  touchup.py cat   in.jpg out.jpg            -> blue eyes
  touchup.py fish  in.jpg out.jpg            -> black eye
  touchup.py frog  in.jpg out.jpg mask.npy   -> belly + toes/fingers light green"""
import sys,numpy as np,cv2
kind,inp,out=sys.argv[1:4];bgr=cv2.imread(inp);h,w=bgr.shape[:2]
if kind=='cat':
  for cx,cy,rx,ry in ((503,168,25,19),(567,175,25,19)):
    cv2.ellipse(bgr,(cx,cy),(rx,ry),-8,0,360,(232,143,47),-1,cv2.LINE_AA)   # BGR of #2f8fe8
elif kind=='fish':
  cv2.circle(bgr,(103,136),17,(18,12,10),-1,cv2.LINE_AA)
elif kind=='frog':
  m=np.load(sys.argv[4]).astype(bool);hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV).astype(int);H,S,V=hsv[...,0]*2,hsv[...,1]/255,hsv[...,2]/255
  yy,xx=np.mgrid[0:h,0:w]
  belly=m&(S<.5)&(V>.5)&(yy>.28*h)&(xx<.75*w)&~((H>70)&(H<170)&(S>.35))
  toes=m&((H>5)&(H<40)&(S>.55)&(V>.62)&(yy>.4*h))
  sel=(belly|toes).astype(np.uint8);sel=cv2.morphologyEx(sel,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8));sel=cv2.morphologyEx(sel,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)&m
  bgr[sel]=(90,225,170)   # BGR of light green #aae15a
cv2.imwrite(out,bgr,[cv2.IMWRITE_JPEG_QUALITY,94])
