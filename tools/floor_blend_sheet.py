from PIL import Image,ImageDraw,ImageFont
W=690;ft=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
rows=[("Orange Cat: finished screen",'fb_cat','finished.png',(0,0,1170,1560)),("Orange Cat: floor, face crop",'fb_cat','face_floor.png',None),("Red Rose: finished screen",'fb_rose','finished.png',(0,0,1170,1560)),("Red Rose: floor crop",'fb_rose','face_floor.png',None)]
def fit(p,c):
  im=Image.open(p).convert('RGB')
  if c: im=im.crop(c)
  return im.resize((W,round(im.height*W/im.width)),Image.LANCZOS)
ims=[(t,fit(f'/tmp/{d}_b/{f}',c),fit(f'/tmp/{d}_a/{f}',c)) for t,d,f,c in rows]
H=34+sum(34+max(x.height,y.height) for _,x,y in ims)
S=Image.new('RGB',(2*W+20,H),(24,20,18));d=ImageDraw.Draw(S)
d.text((8,6),'BEFORE (blur sd = 0.4% of floor width)',fill=(255,150,130),font=ft);d.text((W+28,6),'AFTER (floor 0.24%, detail art 0.14%)',fill=(150,255,150),font=ft);y=34
for t,x,z in ims:
  d.text((8,y+6),t,fill=(240,225,190),font=ft);S.paste(x,(0,y+34));S.paste(z,(W+20,y+34));y+=34+max(x.height,z.height)
S.save('/workspace/cat_floor_blend.jpg',quality=86);print(S.size)
