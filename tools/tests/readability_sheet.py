"""Before/after sheets: original photo | processed source | quantised result, per level -> /workspace/readability_a.png, _b.png"""
import os,sys
from PIL import Image,ImageDraw
S=os.path.abspath(os.path.join(os.path.dirname(__file__),"../../levels/source"))
IDS="berries cat forest gardenflower kingfisher lakesunset lanterns macaw owl peacock penguin pumpkins redapple redfox rose sailboat skyline sunflower tulip".split()
import json
L={l['id']:l for l in json.load(open(S+"/../levels_free.json"))}
W,H=230,190
def tile(path):
  im=Image.open(path).convert('RGB');im.thumbnail((W,H));t=Image.new('RGB',(W,H),(30,30,34));t.paste(im,((W-im.width)//2,(H-im.height)//2));return t
for n,grp in enumerate([IDS[:10],IDS[10:]]):
  cols=2;rows=(len(grp)+1)//2;cw=3*W+30;ch=H+26
  sh=Image.new('RGB',(cols*cw,rows*ch+30),(14,14,18));d=ImageDraw.Draw(sh);d.text((6,8),"readability: ORIGINAL photo | PROCESSED source (subject mask, bg, vibrance, smoothing) | QUANTISED result",fill=(230,230,230))
  for k,i in enumerate(grp):
    o=f"{S}/src_{i}.jpg" if i!='redapple' else f"{S}/src_apple.jpg"
    c=(k%2)*cw;r=(k//2)*ch+30
    for j,pth in enumerate((o,f"{S}/{i}_p.jpg",f"{S}/out_{i}_quant.png")):sh.paste(tile(pth),(c+j*(W+10),r+16))
    l=L[i];d.text((c+2,r+2),f"{l['name']}  [{['','Clear','Tinted','Stained','Jewel'][l['tier']]}]  {len(l['pieces'])} panes, {len(l['colors'])} colours",fill=(255,220,140))
  sh.save(f"/workspace/readability_{'ab'[n]}.png");print(sh.size)
