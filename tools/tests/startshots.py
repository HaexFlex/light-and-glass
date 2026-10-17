"""Start-of-level screenshots (iPhone 13) for given level indices: startshots.py <suffix> idx:name ..."""
import os,sys
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
suf=sys.argv[1]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  for a in sys.argv[2:]:
    i,n=a.split(':');c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page()
    pg.goto(f"file://{R}/index.html#lvl={i}");pg.reload();pg.wait_for_timeout(600)
    pg.evaluate("()=>{Z.z=1;commit();centre();apply()}");pg.wait_for_timeout(300)
    pg.screenshot(path=f"{D}start_{n}_{suf}.png");c.close()
  b.close()
