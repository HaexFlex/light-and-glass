import sys
from PIL import Image,ImageDraw,ImageFont
sh=sys.argv[1]; photo,quant,out=sys.argv[2],sys.argv[3],sys.argv[4]
def fit(p,w,crop=None):
  im=Image.open(p).convert('RGB')
  if crop: im=im.crop(crop)
  return im.resize((w,round(im.height*w/im.width)),Image.LANCZOS)
W=800;a=fit(photo,W);b=fit(quant,W);c=fit(sh+'/face.png',W);f=fit(sh+'/finished.png',W,(0,0,1170,1560))
H=max(f.height,a.height+b.height+c.height+3*34)+34
S=Image.new('RGB',(2*W,H),(24,20,18));d=ImageDraw.Draw(S)
try: ft=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
except: ft=None
def put(im,x,y,t): d.text((x+8,y+6),t,fill=(240,225,190),font=ft); S.paste(im,(x,y+34)); return y+34+im.height
put(f,0,0,'finished screen (window top, floor projection below)')
y=put(a,W,0,'source photo'); y=put(b,W,y,'reduced colours (logic colours; detail panes show their logic colour)'); put(c,W,y,'finished window, face zoom (flipped upright): detail-pane eyes + nose revealed')
S.save(out,quality=86); print(S.size)
