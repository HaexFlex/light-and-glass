"""Candidate sheet with a face close-up: source | reduced colours | finished screen | face zoom (window, flipped upright, DPR 3).
usage: afsheet2.py out.jpg name:source_image:out_json ...   (out_json relative to levels/source; needs out_*_quant.png)"""
import sys,os,json,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw,ImageOps
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));S=R+"/levels/source/"
args=sys.argv[2:];L=json.load(open(R+"/levels/levels_free.json"));ids=[]
for a in args:
  n,img,oj=a.split(":");lv=json.load(open(S+oj));lv['tier']=3;lv['id']='cand_'+n;lv['name']=n;L.append(lv);ids.append(len(L)-1)
os.makedirs("/tmp/afb",exist_ok=True);open("/tmp/afb/index.html","w").write(open(R+"/src/template.html").read().replace('__FREE__',json.dumps(L,separators=(',',':'))))
rows=[]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for a,i in zip(args,ids):
    n,img,oj=a.split(":");dev=dict(p.devices["iPhone 13"]);dev['device_scale_factor']=3;c=b.new_context(**dev,color_scheme="dark");pg=c.new_page()
    pg.goto(f"file:///tmp/afb/index.html#lvl={i}&solve");pg.reload();pg.wait_for_timeout(7800)
    im=Image.open(io.BytesIO(pg.screenshot())).convert("RGB");w,h=im.size;fin=im.crop((0,int(.03*h),w,int(.74*h)))
    r=pg.evaluate("(()=>{const s=Array.from(document.querySelectorAll('svg')).map(e=>e.getBoundingClientRect()).filter(r=>r.width>300&&r.height>200)[0];return [s.x,s.y,s.width,s.height]})()")
    x,y,ww,hh=222,115,726,510;   # the framed window as laid out in the 'solve' screenshot (DPR 3)
    face=ImageOps.flip(im.crop((int(x+.60*ww),int(y+.08*hh),int(x+.92*ww),int(y+.66*hh)))) if False else ImageOps.flip(im.crop((int(x+.58*ww),int(y+.30*hh),int(x+.94*ww),int(y+.92*hh))))
    c.close()
    q=Image.open(S+oj.replace('.json','_quant.png')).convert("RGB");src=Image.open(S+img).convert("RGB");lv=L[i]
    rows.append((n,[src,q,fin,face],f"{len(lv['pieces'])} panes, {len(lv['colors'])} colours, {len(lv.get('gift',[]))} gift, {lv['metrics'].get('autofills',0)} autofill(s), min angle {lv['metrics'].get('min_angle_deg')}"))
  b.close()
H=400;ims=[];W=0
for n,r,t in rows:
  r=[x.resize((round(x.width*H/x.height),H),Image.LANCZOS) for x in r];ims.append((n,r,t));W=max(W,sum(x.width for x in r)+50)
sh=Image.new("RGB",(W,len(ims)*(H+30)),(14,14,18));d=ImageDraw.Draw(sh);y=0
for n,r,t in ims:
  d.text((10,y+4),f"{n} - {t}   |  source | reduced colours | finished screen | face zoom",fill=(255,220,140));x=10
  for im in r: sh.paste(im,(x,y+24));x+=im.width+10
  y+=H+30
sh=sh.resize((1600,round(sh.height*1600/sh.width)),Image.LANCZOS) if sh.width>1600 else sh
for q in (88,82,76,70):
  sh.save(sys.argv[1],quality=q,optimize=True)
  if os.path.getsize(sys.argv[1])<1.5e6: break
print(sh.size,os.path.getsize(sys.argv[1]))
