"""Fresh level start in portrait (iPhone SE, Galaxy S9+), no resize/rotation: after the page settles (hint/power-up bars shown), zooming out to the minimum
shows the whole picture inside the board view, and at a higher zoom panning to the bottom reaches the picture's bottom edge (camera bounds match the real
board-view size), also when the page layout changes after start without any window resize (late bar/font settling). No page errors."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
import os,sys
sys.path.insert(0,os.path.dirname(__file__))
from openlevel import open_level
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8813","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
M="""()=>{const v=document.querySelector('#bv').getBoundingClientRect(),f=document.querySelector('#board svg').getBoundingClientRect();return {v:[v.top,v.bottom,v.left,v.right],f:[f.top,f.bottom,f.left,f.right],BV:[BV.w,BV.h],vw:[v.width,v.height],pad:padF*Z.z/Z.rz}}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for dev in ("iPhone SE","Galaxy S9+"):
      for lid,late in (("lion",0),("macaw",0),("redapple",0),("redapple",1)):
        c=b.new_context(**p.devices[dev]);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
        pg.goto("http://localhost:8813/index.html#preload&levels");pg.wait_for_timeout(400);open_level(pg,lid,400)
        if late: pg.evaluate("()=>{document.querySelector('#top').style.paddingBottom='48px'}");pg.wait_for_timeout(500)   # late in-page layout change (bar/font settling), no window resize
        k=f"{dev}_{lid}{'_latelayout' if late else ''}_"
        r=pg.evaluate(M);ok[k+"camera_matches_board_view"]=abs(r['BV'][0]-r['vw'][0])<2 and abs(r['BV'][1]-r['vw'][1])<2
        pg.evaluate("zoomTo(1,BV.w/2,BV.h/2)");pg.wait_for_timeout(600);r=pg.evaluate(M)
        ok[k+"min_zoom_whole_picture_fits"]=r['f'][0]>=r['v'][0]-2 and r['f'][1]<=r['v'][1]+2 and r['f'][2]>=r['v'][2]-2 and r['f'][3]<=r['v'][3]+2
        pg.evaluate("zoomTo(4,BV.w/2,BV.h/2)");pg.wait_for_timeout(600)
        bv=pg.locator('#bv').bounding_box();x=bv['x']+bv['width']/2
        for _ in range(12):
          pg.mouse.move(x,bv['y']+bv['height']-20);pg.mouse.down();pg.mouse.move(x,bv['y']+20,steps=6);pg.mouse.up();pg.wait_for_timeout(80)
        r=pg.evaluate(M);ok[k+"pan_reaches_bottom_edge"]=abs(r['f'][1]-r['v'][1])<=r['pad']+3   # svg sits padF inside the frame
        print(dev,lid,r,flush=True);c.close()
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
