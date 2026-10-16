"""Per-level start / solved-window / upright-picture PNGs (iPhone 13, dark) + labelled sheets of 3 levels each. usage: puzzlesheets.py out_dir id:Label ..."""
import os,sys,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));OUT=sys.argv[1];os.makedirs(OUT,exist_ok=True)
items=[a.split(':',1) for a in sys.argv[2:]]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for lid,label in items:
    c=b.new_context(**p.devices["iPhone 13"],color_scheme="dark");pg=c.new_page();pg.goto(f"file://{R}/index.html#levels");pg.wait_for_timeout(400)
    i=pg.evaluate(f"LEVELS.findIndex(l=>l.id=='{lid}')"); assert i>=0,lid
    pg.goto(f"file://{R}/index.html#lvl={i}");pg.reload();pg.wait_for_timeout(900);pg.screenshot(path=f"{OUT}/{lid}_start.png")
    pg.goto(f"file://{R}/index.html#lvl={i}&solve");pg.reload();pg.wait_for_timeout(1100);pg.screenshot(path=f"{OUT}/{lid}_solved_window.png")
    pg.wait_for_timeout(5700);pg.screenshot(path=f"{OUT}/{lid}_upright.png");c.close();print(lid,flush=True)
  b.close()
W=330
def fit(path):
  im=Image.open(path).convert("RGB");return im.resize((W,round(im.height*W/im.width)),Image.LANCZOS)
for n in range(0,len(items),3):
  grp=items[n:n+3];ims=[[fit(f"{OUT}/{l}_{k}.png") for k in ("start","solved_window","upright")] for l,_ in grp]
  h=ims[0][0].height;sh=Image.new("RGB",(len(grp)*(3*W+40),h+40),(14,14,18));d=ImageDraw.Draw(sh)
  for j,((l,lab),row) in enumerate(zip(grp,ims)):
    x0=j*(3*W+40)
    d.text((x0+6,6),f"{lab}",fill=(255,220,140))
    for k,(im,cap) in enumerate(zip(row,("start (as played)","solved window","upright picture"))):
      sh.paste(im,(x0+k*(W+6),30));d.text((x0+k*(W+6)+4,h+32 if False else 18),cap,fill=(190,190,200))
  sh.save(f"/workspace/puzzles_c{n//3+1}.png");print(sh.size)
