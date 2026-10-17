"""Contact sheet of all levels: start and win (floor reveal) thumbnails on iPhone 13, ordered like the menu. -> docs/screenshots/levels_contact_sheet.png"""
import os,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
TW,TH=150,325
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  c0=b.new_context(**p.devices["iPhone 13"]);pg=c0.new_page();pg.goto(f"file://{R}/index.html#levels");pg.wait_for_timeout(500)
  info=pg.evaluate("()=>menuOrder().filter(o=>!o.sect).map(o=>[o.i,LEVELS[o.i].name,LEVELS[o.i].tier,LEVELS[o.i].pieces.length,LEVELS[o.i].colors.length])");c0.close()
  tiles=[]
  for i,name,tier,n,k in info:
    c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page()
    pg.goto(f"file://{R}/index.html#lvl={i}");pg.wait_for_timeout(700);a=Image.open(io.BytesIO(pg.screenshot()))
    pg.goto(f"file://{R}/index.html#lvl={i}&solve");pg.reload();pg.wait_for_timeout(6800);w=Image.open(io.BytesIO(pg.screenshot()));c.close()
    t=Image.new("RGB",(TW*2+6,TH+34),(18,18,22))
    for j,im in enumerate((a,w)):
      im=im.convert("RGB");im.thumbnail((TW,TH));t.paste(im,(j*(TW+6),0))
    d=ImageDraw.Draw(t);d.text((3,TH+4),f"{name}",fill=(255,255,255));d.text((3,TH+18),f"{['','Clear','Tinted','Stained','Jewel'][tier]} · {n} panes · {k} colours",fill=(190,190,200))
    tiles.append(t);print(name,flush=True)
  cols=5;rows=(len(tiles)+cols-1)//cols;cw=TW*2+16;ch=TH+44
  sh=Image.new("RGB",(cols*cw,rows*ch),(18,18,22))
  for k,t in enumerate(tiles):sh.paste(t,((k%cols)*cw,(k//cols)*ch))
  sh.save(D+"levels_contact_sheet.png");print(sh.size)
  b.close()
