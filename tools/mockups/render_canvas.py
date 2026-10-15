"""Render Canvas (pane collectible) mockups, iPhone 13 390x844 @3x, dark+light, into docs/mockups/."""
import os,json,subprocess,sys
from playwright.sync_api import sync_playwright
H=os.path.dirname(os.path.abspath(__file__));R=os.path.abspath(H+"/../..");OUT=R+"/docs/mockups/"
subprocess.check_call([sys.executable,H+"/gen_landscape.py"],stdout=subprocess.DEVNULL)
pn=json.load(open(H+"/landscape30.json"))
open(H+"/_cv_built.html","w").write(open(H+"/canvas.html").read().replace("__PANES__",json.dumps(pn)))
SC=[("empty","10a_canvas_empty"),("partial","10b_canvas_partial"),("done","10c_canvas_complete"),("reward","10d_reward_pane"),("coll","10e_collection_canvas")]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for s,name in SC:
    for t in("dark","light"):
      c=b.new_context(viewport={"width":390,"height":844},device_scale_factor=3,is_mobile=True,has_touch=True);pg=c.new_page()
      pg.goto(f"file://{H}/_cv_built.html?s={s}&t={t}");pg.wait_for_timeout(400)
      pg.screenshot(path=f"{OUT}{name}_{t}.png");c.close()
  b.close()
