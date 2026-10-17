"""Finished screen (window + floor picture after the reveal) of every level in menu order, iPhone 13 dark -> /workspace/finished/<id>.png + /workspace/finished_N.png (6 per sheet, 3x2)."""
import os,io,sys
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));OUT="/workspace/finished";os.makedirs(OUT,exist_ok=True)
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  c=b.new_context(**p.devices["iPhone 13"],color_scheme="dark");pg=c.new_page();pg.goto(f"file://{R}/index.html#levels");pg.wait_for_timeout(500)
  info=pg.evaluate("()=>menuOrder().filter(o=>!o.sect).map(o=>[o.i,LEVELS[o.i].id,LEVELS[o.i].name,LEVELS[o.i].tier,LEVELS[o.i].pieces.length,LEVELS[o.i].colors.length])");c.close()
  for i,lid,name,tier,n,k in info:
    if os.path.exists(f"{OUT}/{lid}.png") and '--force' not in sys.argv: continue
    c=b.new_context(**p.devices["iPhone 13"],color_scheme="dark");pg=c.new_page()
    pg.goto(f"file://{R}/index.html#lvl={i}&solve");pg.reload();pg.wait_for_timeout(7800)
    im=Image.open(io.BytesIO(pg.screenshot())).convert("RGB");w,h=im.size;im.crop((0,int(.03*h),w,int(.74*h))).save(f"{OUT}/{lid}.png");c.close();print(lid,flush=True)
  b.close()
T=['','Clear','Tinted','Stained','Jewel'];W=430
for s in range(0,len(info),6):
  grp=info[s:s+6];ims=[Image.open(f"{OUT}/{g[1]}.png") for g in grp];ims=[im.resize((W,round(im.height*W/im.width))) for im in ims];h=ims[0].height
  sh=Image.new("RGB",(3*(W+10),2*(h+34)),(14,14,18));d=ImageDraw.Draw(sh)
  for k,(g,im) in enumerate(zip(grp,ims)):
    x=(k%3)*(W+10);y=(k//3)*(h+34);sh.paste(im,(x,y+30));d.text((x+4,y+4),f"{g[2]}",fill=(255,220,140));d.text((x+4,y+16),f"{T[g[3]]} - {g[4]} panes, {g[5]} colours",fill=(190,190,200))
  sh.save(f"/workspace/finished_{s//6+1}.png");print("sheet",s//6+1,sh.size,flush=True)
