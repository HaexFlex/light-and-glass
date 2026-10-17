"""Per-level start / solved-window / upright PNGs (iPhone 13, dark; first-run tip dismissed; window captured after the glide) + sheets of 3 levels.
usage: puzzlesheets2.py out_dir sheet_prefix id:Label ..."""
import os,sys
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));OUT,PRE=sys.argv[1],sys.argv[2];os.makedirs(OUT,exist_ok=True)
items=[a.split(':',1) for a in sys.argv[3:]]
NOTIP="()=>{try{PU.hint=1;puSave();document.querySelector('#puhint').classList.remove('on');document.querySelector('#pubar').classList.remove('hintpulse');relayout()}catch(e){}}"
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  for lid,label in items:
    c=b.new_context(**p.devices["iPhone 13"],color_scheme="dark");pg=c.new_page();pg.goto(f"file://{R}/index.html#levels");pg.wait_for_timeout(400)
    i=pg.evaluate(f"LEVELS.findIndex(l=>l.id=='{lid}')");assert i>=0,lid
    pg.evaluate(NOTIP)
    pg.goto(f"file://{R}/index.html#lvl={i}");pg.reload();pg.wait_for_timeout(900);pg.evaluate(NOTIP);pg.wait_for_timeout(400);pg.screenshot(path=f"{OUT}/{lid}_start.png")
    pg.goto(f"file://{R}/index.html#lvl={i}&solve");pg.reload();pg.wait_for_timeout(2000);pg.screenshot(path=f"{OUT}/{lid}_solved_window.png")
    pg.wait_for_timeout(4800);pg.screenshot(path=f"{OUT}/{lid}_upright.png");c.close();print(lid,flush=True)
  b.close()
W=400
def fit(path):
  im=Image.open(path).convert("RGB");return im.resize((W,round(im.height*W/im.width)),Image.LANCZOS)
for n in range(0,len(items),3):
  grp=items[n:n+3];rows=[[fit(f"{OUT}/{l}_{k}.png") for k in("start","solved_window","upright")] for l,_ in grp]
  h=rows[0][0].height;sh=Image.new("RGB",(3*W+20,len(grp)*(h+34)),(14,14,18));d=ImageDraw.Draw(sh)
  for r,((l,lab),row) in enumerate(zip(grp,rows)):
    y=r*(h+34);d.text((6,y+4),lab,fill=(255,220,140))
    for k,(im,cap) in enumerate(zip(row,("start (as played)","solved window","upright picture / floor reveal"))):
      sh.paste(im,(k*(W+10),y+22));d.text((k*(W+10)+90,y+4),cap,fill=(190,190,200))
  sh.save(f"/workspace/{PRE}{n//3+1}.png");print(sh.size,flush=True)
