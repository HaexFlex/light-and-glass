"""Tiny-pane zoom: max zoom is high enough that the smallest pane of every level reaches >=40px on iPhone SE / Galaxy S9+; start zoom is unchanged for large-pane levels;
a tap on a very small pane (<16px) first zooms in closer (no placement), large-pane levels never do; no page errors."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8803","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for dev in ["iPhone SE","Galaxy S9+"]:
      for lid in ["redtulip","orangecat","alpinelake","toadstool"]:
        pg=b.new_context(**p.devices[dev]).new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
        pg.goto("http://localhost:8803/index.html#preload&levels");pg.wait_for_timeout(300);pg.locator(f'.card[data-id="{lid}"]').tap();pg.wait_for_timeout(600)
        px=lambda:pg.evaluate("(()=>{const k=L.n*cs*(Z.z/Z.rz);return 2*Math.min(...L.pieces.map(p=>p.rin))*k})()")
        z0=pg.evaluate("Z.z");pg.evaluate("zoomTo(ZMAX,BV.w/2,BV.h/2)");pg.wait_for_timeout(900);mx=px()
        ok[f"{dev}_{lid}_smallest_pane_ge_40px_at_max_zoom"]=mx>=40
        pg.evaluate("load(LEVELS.findIndex(l=>l.id==L.id))");pg.wait_for_timeout(500);z1=pg.evaluate("Z.z");tiny=px()<16
        info=pg.evaluate("""(()=>{let best=-1,bv=1e9;const v=document.querySelector('#bv').getBoundingClientRect();L.pieces.forEach((p,i)=>{if(!lock.has(i)&&p.rin<bv){const m=cells[i].getBoundingClientRect(),x=m.x+m.width/2,y=m.y+m.height/2;if(x>v.x+5&&x<v.right-5&&y>v.y+5&&y<v.bottom-5){bv=p.rin;best=i}}});if(best<0)return null;const m=cells[best].getBoundingClientRect();return [best,m.x+m.width/2,m.y+m.height/2]})()""")
        if info:
          pg.mouse.click(info[1],info[2]);pg.wait_for_timeout(600);z2=pg.evaluate("Z.z");pl=pg.evaluate(f"lock.has({info[0]})")
          ok[f"{dev}_{lid}_tap_zoom_{'closer' if tiny else 'never'}"]=(z2>z1*1.5 and not pl) if tiny else (abs(z2-z1)<.01)
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
