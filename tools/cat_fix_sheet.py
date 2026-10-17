import sys
from PIL import Image,ImageDraw,ImageFont
b,a,out=sys.argv[1:4]
W=690
def fit(p,crop=None):
  im=Image.open(p).convert('RGB')
  if crop: im=im.crop(crop)
  return im.resize((W,round(im.height*W/im.width)),Image.LANCZOS)
rows=[("finished screen, iPhone 13",'finished.png',(0,0,1170,1560)),("face crop: window (flipped upright)",'face_window.png',None),("face crop: floor",'face_floor.png',None)]
ft=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
ims=[(t,fit(b+'/'+f,c),fit(a+'/'+f,c)) for t,f,c in rows]
H=sum(34+max(x.height,y.height) for _,x,y in ims)+34
S=Image.new('RGB',(2*W+20,H),(24,20,18));d=ImageDraw.Draw(S);y=0
d.text((8,6),'BEFORE',fill=(255,150,130),font=ft);d.text((W+28,6),'AFTER',fill=(150,255,150),font=ft);y=34
for t,x,z in ims:
  d.text((8,y+6),t,fill=(240,225,190),font=ft);S.paste(x,(0,y+34));S.paste(z,(W+20,y+34));y+=34+max(x.height,z.height)
S.save(out,quality=86);print(S.size)
