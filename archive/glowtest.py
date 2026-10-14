"""Glow mode: real touch taps (Playwright mobile emulation) + screenshots for the 12x12 Lighthouse."""
import json
from playwright.sync_api import sync_playwright
U="file:///workspace/puzzle-studio/light-glass/index.html"; D="/workspace/puzzle-studio/light-glass/"
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  ctx=b.new_context(**{**p.devices["iPhone 13"],"device_scale_factor":2}); pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
  pg.goto(U); pg.wait_for_timeout(300); pg.screenshot(path=D+"shot_menu.png")
  pg.locator('.card').nth(5).tap(); pg.wait_for_timeout(500)
  print("opened",pg.evaluate("[L.name,L.mode,L.start.length,Z.z,cs]"))
  pg.screenshot(path=D+"shot_glow_lighthouse_start.png")
  def tap_cell(r,c):
    x,y=pg.evaluate(f"(()=>{{const b=cells[{r}*L.n+{c}].getBoundingClientRect();return[b.x+b.width/2,b.y+b.height/2]}})()")
    pg.touchscreen.tap(x,y); pg.wait_for_timeout(40)
  def visible(r,c): return pg.evaluate(f"(()=>{{const v=document.querySelector('#bv').getBoundingClientRect(),b=cells[{r}*L.n+{c}].getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;return x>v.x+4&&x<v.right-4&&y>v.y+4&&y<v.bottom-4&&document.elementFromPoint(x,y)===cells[{r}*L.n+{c}]}})()")
  sol=pg.evaluate("L.sol"); n=len(sol)
  # wrong tap -> crack + revert
  r0,c0=next((r,c) for r in range(n) for c in range(n) if visible(r,c) and pg.evaluate(f"grid[{r}][{c}]")<0)
  wrong=(sol[r0][c0]+1)%5; pg.locator('.sw').nth(wrong).tap(); tap_cell(r0,c0)
  st=pg.evaluate(f"[grid[{r0}][{c0}],cracks]"); pg.wait_for_timeout(800); st2=pg.evaluate(f"[grid[{r0}][{c0}],cracks,lock.size]")
  print("wrong tap: during",st,"after",st2)
  # play the cascade order a deducer would follow: repeatedly place panes adjacent to lit panes (correct colours, via real taps)
  placed=0
  for rnd in range(40):
    if placed>=55: break
    lit=pg.evaluate("[...lock]")
    front=[(r,c) for r in range(n) for c in range(n) if r*n+c not in lit and any((rr*n+cc) in lit for rr in (r-1,r,r+1) for cc in (c-1,c,c+1))]
    front=[x for x in front if visible(*x)]
    if not front: break
    for r,c in front[:6]:
      pg.locator('.sw').nth(sol[r][c]).tap(); tap_cell(r,c); placed+=1
  print("placed by taps:",placed,"locked:",pg.evaluate("lock.size"),"cracks:",pg.evaluate("cracks"))
  pg.locator('.sw').nth((sol[r0][c0]+2)%5).tap()
  r1,c1=next((r,c) for r in range(n) for c in range(n) if visible(r,c) and pg.evaluate(f"grid[{r}][{c}]")<0)
  pg.locator('.sw').nth((sol[r1][c1]+1)%5).tap(); tap_cell(r1,c1); pg.wait_for_timeout(120)
  pg.screenshot(path=D+"shot_glow_lighthouse_mid.png")
  pg.wait_for_timeout(800)
  # finish (by taps on remaining panes, panning via zoom-out first)
  pg.locator('#ztog').tap(); pg.wait_for_timeout(500)
  for r in range(n):
    for c in range(n):
      if pg.evaluate(f"grid[{r}][{c}]")<0: pg.locator('.sw').nth(sol[r][c]).tap(); tap_cell(r,c)
  pg.wait_for_timeout(300); print("won:",pg.evaluate("won"),"cracks",pg.evaluate("cracks"))
  pg.evaluate("document.body.classList.add('instant')"); pg.wait_for_timeout(5500)
  pg.screenshot(path=D+"shot_glow_lighthouse_win.png"); print("errors",errs)
