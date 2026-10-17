"""Reveal sequence: solve a level instantly, capture 3 frames of the projection (phone portrait, iPhone 13)."""
import os,sys
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../..")); D=R+"/docs/screenshots/"
LV=[(int(a.split(':')[0]),a.split(':')[1]) for a in sys.argv[1:]] or [(1,'koi'),(3,'fox')]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  for lv,name in LV:
    for dev in ["iPhone 13","iPhone SE"]:
      c=b.new_context(**p.devices[dev]);pg=c.new_page();err=[];pg.on("pageerror",lambda e:err.append(str(e)))
      pg.goto(f"file://{R}/index.html#lvl={lv}&solve");t=[1100,2500,6500] if dev=="iPhone 13" else [6000]
      last=0
      for k,ms in enumerate(t):
        pg.wait_for_timeout(ms-last);last=ms
        tag=["1_window","2_beams","3_floor"][k] if dev=="iPhone 13" else "se_final"
        pg.screenshot(path=f"{D}reveal_{name}_{tag}.png")
      print(name,dev,"errors",err);c.close()
  b.close()
