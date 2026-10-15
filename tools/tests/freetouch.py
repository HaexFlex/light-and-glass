"""Touch regression for Free Glass on 4 emulated phones (levels 1, 3 and the 3:2 Alpine Lake) (real touch events via Playwright/CDP)."""
import json
from playwright.sync_api import sync_playwright
import os; R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../..")); U="file://"+R+"/index.html"
def touch(cdp,typ,pts): cdp.send("Input.dispatchTouchEvent",{"type":typ,"touchPoints":[{"x":x,"y":y,"id":i} for i,(x,y) in enumerate(pts)]})
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  for dev in ["iPhone 13","iPhone SE","Pixel 7","Galaxy S9+"]:
    for lvl in (1,3,4,5,8):
      ctx=b.new_context(**p.devices[dev]); pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      pg.goto(U); pg.wait_for_timeout(300); pg.locator(f'.card[data-l="{lvl}"]').tap(); pg.wait_for_timeout(400); cdp=ctx.new_cdp_session(pg); R={}
      sol=pg.evaluate("L.sol[0]"); nb=pg.evaluate("L.nb")
      def pt(i): return pg.evaluate(f"(()=>{{const P=L.pieces[{i}],m=cells[{i}].getScreenCTM(),U=L.n*cs;const q=new DOMPoint(P.pole[0]*U,P.pole[1]*U).matrixTransform(m);return[q.x,q.y]}})()")
      def vis(i):
        x,y=pt(i); return pg.evaluate(f"(()=>{{const v=document.querySelector('#bv').getBoundingClientRect();return {x}>v.x+4&&{x}<v.right-4&&{y}>v.y+4&&{y}<v.bottom-4&&document.elementFromPoint({x},{y})===cells[{i}]}})()")
      def front(): 
        lit=set(pg.evaluate("[...lock]")); return [j for j in range(len(sol)) if j not in lit and any(k in lit for k in nb[j]) and vis(j)]
      f=front(); j=f[0]; pg.locator('.sw').nth(sol[j]).tap(); R['palette']=pg.evaluate("sel")==sol[j]
      x,y=pt(j); pg.touchscreen.tap(x,y); pg.wait_for_timeout(80); R['tap']=pg.evaluate(f"grid[0][{j}]")==sol[j]
      j=front()[0]; pg.locator('.sw').nth(sol[j]).tap(); x,y=pt(j)
      touch(cdp,"touchStart",[(x,y)]); pg.wait_for_timeout(30); touch(cdp,"touchMove",[(x+4,y+3)]); pg.wait_for_timeout(30); touch(cdp,"touchMove",[(x+6,y+6)]); pg.wait_for_timeout(30); touch(cdp,"touchEnd",[]); pg.wait_for_timeout(80)
      R['wobbly_tap']=pg.evaluate(f"grid[0][{j}]")==sol[j]
      cx,cy=pg.evaluate("(()=>{const b=document.querySelector('#bv').getBoundingClientRect();return[b.x+b.width/2,b.y+b.height/2]})()"); z0=pg.evaluate("Z.z")
      touch(cdp,"touchStart",[(cx-30,cy),(cx+30,cy)])
      for k in range(1,7): pg.wait_for_timeout(20); touch(cdp,"touchMove",[(cx-30-k*8,cy),(cx+30+k*8,cy)])
      touch(cdp,"touchEnd",[]); pg.wait_for_timeout(150); R['pinch']=pg.evaluate("Z.z")>z0
      t0=pg.evaluate("[Z.tx,Z.ty]"); touch(cdp,"touchStart",[(cx,cy)])
      for k in range(1,5): pg.wait_for_timeout(20); touch(cdp,"touchMove",[(cx+k*15,cy+k*10)])
      touch(cdp,"touchEnd",[]); pg.wait_for_timeout(100); R['pan']=pg.evaluate("[Z.tx,Z.ty]")!=t0
      f=front()
      if f: j=f[0]; pg.locator('.sw').nth(sol[j]).tap(); x,y=pt(j); pg.touchscreen.tap(x,y); pg.wait_for_timeout(80); R['tap_zoomed']=pg.evaluate(f"grid[0][{j}]")==sol[j]
      else: R['tap_zoomed']='no frontier visible'
      R['palette_rows']=pg.evaluate("(()=>{const s=[...document.querySelectorAll('.sw')];return new Set(s.map(e=>e.offsetTop)).size})()")
      R['palette_fits']=pg.evaluate("[...document.querySelectorAll('.sw')].every(e=>e.getBoundingClientRect().right<=innerWidth)")
      R['errors']=errs; print(dev,"lvl",lvl,json.dumps(R),flush=True); ctx.close()
