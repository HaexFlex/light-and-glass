"""Render power-up mockups (iPhone 13: 390x844 @3x) in dark and light into docs/mockups/."""
import os,json
from playwright.sync_api import sync_playwright
H=os.path.dirname(os.path.abspath(__file__));R=os.path.abspath(H+"/../..");OUT=R+"/docs/mockups/"
lv=json.load(open(R+"/levels/levels_free.json"))
open(H+"/_pu_built.html","w").write(open(H+"/powerups.html").read().replace("__LV__",json.dumps(lv)))
SC=[("hud","5_powerups_hud",1),("bolt","6_effect_lightning",3),("flare","7_effect_sunflare",3),("reward","8a_reward_win",1),("inv","8b_collection_powerups",1),("options","9_options_themes",1)]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for s,name,n in SC:
    for t in("dark","light"):
      c=b.new_context(viewport={"width":390*n,"height":844},device_scale_factor=3 if n==1 else 2,is_mobile=True,has_touch=True);pg=c.new_page()
      pg.goto(f"file://{H}/_pu_built.html?s={s}&t={t}");pg.wait_for_timeout(500)
      pg.screenshot(path=f"{OUT}{name}_{t}.png");c.close()
  b.close()
