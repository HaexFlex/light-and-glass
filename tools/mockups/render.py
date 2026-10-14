"""Render UI mockups (390x844 @2x). Static screens from mockups.html; HUD + win screens use the real game (index.html) with restyle CSS injected."""
import os,json
from playwright.sync_api import sync_playwright
H=os.path.dirname(os.path.abspath(__file__));R=os.path.abspath(H+"/../..");OUT=R+"/docs/mockups/"
lv=json.load(open(R+"/levels/levels_free.json"))
html=open(H+"/mockups.html").read().replace("__COMMON__",open(H+"/common.js").read()).replace("__LV__",json.dumps(lv))
open(H+"/_built.html","w").write(html)
HUD=open(H+"/hud.css").read()
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  c=b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True);pg=c.new_page()
  for s,name in [("tA","1a_title_cathedral"),("tB","1b_title_cottage"),("col","2_collection")]:
    pg.goto(f"file://{H}/_built.html#{s}");pg.reload();pg.wait_for_timeout(400);pg.screenshot(path=OUT+name+".png")
  # 3: in-game HUD restyle on the real Autumn Fox board, ~45% solved
  pg.goto(f"file://{R}/index.html#lvl=3");pg.reload();pg.wait_for_timeout(400);pg.add_style_tag(content=HUD)
  pg.evaluate("""()=>{const order=[...L.pieces.keys()].sort((a,b)=>L.pieces[a].pole[1]-L.pieces[b].pole[1]);
   order.slice(0,Math.round(order.length*.45)).forEach(i=>{grid[0][i]=L.sol[0][i];lock.add(i)});sel=2;
   render();
   document.getElementById('lvname').innerHTML='Autumn Fox<small>62 / 144</small>';hlNeighbours(order[40]);}""")
  pg.wait_for_timeout(300);pg.screenshot(path=OUT+"3_hud.png")
  # 4: win screen with the projection
  pg.goto(f"file://{R}/index.html#lvl=1&solve");pg.reload();pg.add_style_tag(content=HUD);pg.wait_for_timeout(7000)
  pg.evaluate("""()=>{document.getElementById('winBar').innerHTML='<div class=wc><div class=wt>Koi Pond</div><div class=ws>revealed in light · flawless ✦</div><div class=wb><button class=g>Collection</button><button class=p>Next window</button></div></div>'}""")
  pg.wait_for_timeout(300);pg.screenshot(path=OUT+"4_win.png")
  b.close()
