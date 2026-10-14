"""Free Glass: real touch taps (Playwright iPhone 13 emulation) + screenshots for the showpiece."""
import sys
from playwright.sync_api import sync_playwright
import os; R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../..")); U="file://"+R+"/index.html"; D=R+"/docs/screenshots/"
LV=int(sys.argv[1]) if len(sys.argv)>1 else 7; NAME=sys.argv[2] if len(sys.argv)>2 else "free_swan"
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  ctx=b.new_context(**{**p.devices["iPhone 13"],"device_scale_factor":2}); pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
  pg.goto(U); pg.wait_for_timeout(300); pg.screenshot(path=D+"shot_menu.png")
  pg.locator('.card').nth(LV).tap(); pg.wait_for_timeout(500)
  print("opened",pg.evaluate("[L.name,L.mode,L.pieces.length,L.start,Z.z,cs]"))
  pg.screenshot(path=D+f"shot_{NAME}_start.png")
  sol=pg.evaluate("L.sol[0]"); nb=pg.evaluate("L.nb"); N=len(sol)
  def pt(i): return pg.evaluate(f"(()=>{{const P=L.pieces[{i}],b=cells[{i}].getBoundingClientRect(),m=cells[{i}].getScreenCTM(),U=L.n*cs;const q=new DOMPoint(P.pole[0]*U,P.pole[1]*U).matrixTransform(m);return[q.x,q.y]}})()")
  def visible(i):
    x,y=pt(i); return pg.evaluate(f"(()=>{{const v=document.querySelector('#bv').getBoundingClientRect();return {x}>v.x+4&&{x}<v.right-4&&{y}>v.y+4&&{y}<v.bottom-4&&document.elementFromPoint({x},{y})===cells[{i}]}})()")
  def tap(i,col): pg.locator('.sw').nth(col).tap(); x,y=pt(i); pg.touchscreen.tap(x,y); pg.wait_for_timeout(40)
  # a wrong colour on a neighbour of the start pane -> crack + falls out
  s0=pg.evaluate("L.start[0]"); x,y=pt(s0); pg.touchscreen.tap(x,y); pg.wait_for_timeout(100)
  print("highlight on tapping lit pane:",pg.evaluate("document.querySelectorAll('.cell.nbhl').length"),"of",len(nb[s0]),"neighbours")
  pg.wait_for_timeout(1400)
  w=next(j for j in nb[s0] if j not in pg.evaluate("L.start") and visible(j)); tap(w,(sol[w]+1)%len(pg.evaluate("L.colors")))
  print("wrong tap: cracks",pg.evaluate("cracks"),"pane value during",pg.evaluate(f"grid[0][{w}]")); pg.wait_for_timeout(800)
  print("after: value",pg.evaluate(f"grid[0][{w}]"),"locked",pg.evaluate("lock.size"))
  placed=0
  for rnd in range(30):
    if placed>=40: break
    lit=set(pg.evaluate("[...lock]")); front=[j for j in range(N) if j not in lit and any(k in lit for k in nb[j]) and visible(j)]
    if not front: break
    for j in front[:5]: tap(j,sol[j]); placed+=1
  print("placed",placed,"locked",pg.evaluate("lock.size"),"/",N)
  pg.wait_for_timeout(900); pg.screenshot(path=D+f"shot_{NAME}_mid.png")
  pg.locator('#ztog').tap(); pg.wait_for_timeout(500)
  for j in range(N):
    if pg.evaluate(f"grid[0][{j}]")<0: tap(j,sol[j])
  pg.wait_for_timeout(300); print("won",pg.evaluate("won"),"cracks",pg.evaluate("cracks"),"unfilled",pg.evaluate("grid[0].filter(v=>v<0).length"))
  pg.evaluate("document.body.classList.add('instant')"); pg.wait_for_timeout(5500); pg.screenshot(path=D+f"shot_{NAME}_win.png"); print("errors",errs)
