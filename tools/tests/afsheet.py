"""Candidate sheet: source | reduced colours | finished screen for out_<id>.json candidates (appended to a temp build, never to levels_free.json).
usage: afsheet.py out.png name:source_image:out_json ..."""
import sys,os,json,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));S=R+"/levels/source/"
args=sys.argv[2:];sys.path.insert(0,R+"/tools/freeglass");import levelstore;L=levelstore.load_all();ids=[];ex=[]
for a in args:
  n,img,oj=a.split(":");lv=json.load(open(S+oj));lv['tier']=3;lv['id']='cand_'+n.replace(' ','_');lv['name']=n;ex.append(lv);ids.append(len(L)+len(ex)-1)
L=L+ex;os.makedirs("/tmp/afb",exist_ok=True);levelstore.build_page("/tmp/afb",ex)
rows=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  for a,i in zip(args,ids):
    n,img,oj=a.split(":");c=b.new_context(**p.devices["iPhone 13"],color_scheme="dark");pg=c.new_page()
    pg.goto(f"file:///tmp/afb/index.html#lvl={i}&solve");pg.reload();pg.wait_for_timeout(7800)
    im=Image.open(io.BytesIO(pg.screenshot())).convert("RGB");w,h=im.size;fin=im.crop((0,int(.03*h),w,int(.74*h)));c.close()
    q=Image.open(S+oj.replace('.json','_quant.png')).convert("RGB");src=Image.open(S+img).convert("RGB")
    lv=L[i];rows.append((n,src,q,fin,f"{len(lv['pieces'])} panes, {len(lv['colors'])} colours, {len(lv['start'])} start(s), {lv['metrics'].get('autofills',0)} autofill(s)"))
  b.close()
H=560;W=0;sh=None;y=0;ims=[]
for n,s,q,f,t in rows:
  r=[x.resize((round(x.width*H/x.height),H)) for x in (s,q,f)];ims.append((n,r,t));W=max(W,sum(x.width for x in r)+40)
sh=Image.new("RGB",(W,len(ims)*(H+34)),(14,14,18));d=ImageDraw.Draw(sh)
for n,r,t in ims:
  x=10;d.text((10,y+4),f"{n} - {t}   |   source  |  reduced colours  |  finished screen",fill=(255,220,140))
  for im in r: sh.paste(im,(x,y+24));x+=im.width+10
  y+=H+34
sh.save(sys.argv[1]);print(sh.size)
