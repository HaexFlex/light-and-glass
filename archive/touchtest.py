"""Real touch tests (Playwright mobile emulation: isMobile+hasTouch, CDP touch events; no JS clicks)."""
import json
from playwright.sync_api import sync_playwright
U="file:///workspace/puzzle-studio/light-glass/index.html"
def vis_cell(pg,skip=()):
  return pg.evaluate("""(skip)=>{const v=document.querySelector('#bv').getBoundingClientRect();
   for(let r=0;r<L.n;r++)for(let c=0;c<L.n;c++){if(isClue(r,c)||grid[r][c]>=0||skip.some(s=>s[0]==r&&s[1]==c))continue;
    const b=cells[r*L.n+c].getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;
    if(x>v.x+8&&x<v.right-8&&y>v.y+8&&y<v.bottom-8&&document.elementFromPoint(x,y)===cells[r*L.n+c])return[r,c,x,y,Math.round(Math.min(b.width,b.height))]}}""",[list(s) for s in skip])
def touch(cdp,typ,pts): cdp.send("Input.dispatchTouchEvent",{"type":typ,"touchPoints":[{"x":x,"y":y,"id":i} for i,(x,y) in enumerate(pts)]})
def finger(pg,cdp,path,step=25):
  touch(cdp,"touchStart",[path[0]])
  for p in path[1:]: pg.wait_for_timeout(step); touch(cdp,"touchMove",[p])
  pg.wait_for_timeout(step); touch(cdp,"touchEnd",[]); pg.wait_for_timeout(80)
def run(dev,lvl):
  R={}
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    ctx=b.new_context(**p.devices[dev]); pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(U); pg.wait_for_timeout(300)
    pg.locator('.card').nth(lvl).tap(); pg.wait_for_timeout(400)        # level select by touch
    R['opened']=pg.evaluate("document.body.classList.contains('playing')&&L.name")
    cdp=ctx.new_cdp_session(pg)
    pg.locator('.sw').nth(1).tap(); pg.wait_for_timeout(60); R['palette_tap_sel']=pg.evaluate("sel")
    R['zoom_start']=round(pg.evaluate("Z.z"),2)
    r,c,x,y,w=vis_cell(pg); pg.touchscreen.tap(x,y); pg.wait_for_timeout(80)
    R['tap_place']=(pg.evaluate(f"grid[{r}][{c}]")==1, f"pane {r},{c} {w}px")
    r2,c2,x,y,_=vis_cell(pg); finger(pg,cdp,[(x,y),(x+3,y+2),(x+6,y+5)])   # wobbly finger (6-8px)
    R['wobbly_tap_place']=pg.evaluate(f"grid[{r2}][{c2}]")==1
    x,y=pg.evaluate(f"(()=>{{const b=cells[{r}*L.n+{c}].getBoundingClientRect();return[b.x+b.width/2,b.y+b.height/2]}})()")
    touch(cdp,"touchStart",[(x,y)]); pg.wait_for_timeout(600); touch(cdp,"touchEnd",[]); pg.wait_for_timeout(80)
    R['longpress_clear']=pg.evaluate(f"grid[{r}][{c}]")==-1
    R['undo_restores']=(pg.locator('#undo').tap(), pg.wait_for_timeout(60), pg.evaluate(f"grid[{r}][{c}]")==1)[2]
    # pinch zoom in
    bv=pg.evaluate("(()=>{const b=document.querySelector('#bv').getBoundingClientRect();return[b.x+b.width/2,b.y+b.height/2]})()")
    z0=pg.evaluate("Z.z"); cx,cy=bv
    touch(cdp,"touchStart",[(cx-30,cy),(cx+30,cy)])
    for k in range(1,9): pg.wait_for_timeout(20); touch(cdp,"touchMove",[(cx-30-k*8,cy),(cx+30+k*8,cy)])
    touch(cdp,"touchEnd",[]); pg.wait_for_timeout(150)
    z1=pg.evaluate("Z.z"); R['pinch_zoom']=(round(z0,2),round(z1,2),z1>z0, pg.evaluate("Math.abs(Z.rz-Z.z)<.01"))
    filled=pg.evaluate("grid.flat().filter(v=>v>=0).length")
    tx0=pg.evaluate("[Z.tx,Z.ty]"); finger(pg,cdp,[(cx,cy),(cx-20,cy-10),(cx-60,cy-40),(cx-90,cy-60)])
    tx1=pg.evaluate("[Z.tx,Z.ty]"); R['one_finger_pan']=(tx0!=tx1, pg.evaluate("grid.flat().filter(v=>v>=0).length")==filled)
    vc=vis_cell(pg)
    if not vc: R['debug']=pg.evaluate('[Z,BV,cs]'); print(R); return R
    r3,c3,x,y,w3=vc; pg.locator('.sw').nth(2).tap(); pg.touchscreen.tap(x,y); pg.wait_for_timeout(80)
    R['tap_place_zoomed']=(pg.evaluate(f"grid[{r3}][{c3}]")==2, f"{w3}px")
    # zoom out to fit with button, then drag-paint across a row
    pg.locator('#ztog').tap(); pg.wait_for_timeout(450); R['ztog_fit']=round(pg.evaluate("Z.z"),2)
    path=pg.evaluate("""(()=>{for(let r=0;r<L.n;r++){const run=[];for(let c=0;c<L.n;c++){if(isClue(r,c)||grid[r][c]>=0){run.length=0;continue}run.push(c);if(run.length==4){
      return run.map(c=>{const b=cells[r*L.n+c].getBoundingClientRect();return[r,c,b.x+b.width/2,b.y+b.height/2]})}}}})()""")
    pg.locator('.sw').nth(3).tap()
    pts=[(p[2],p[3]) for p in path]; fine=[]
    for i in range(len(pts)-1):
      for k in range(4): fine.append((pts[i][0]+(pts[i+1][0]-pts[i][0])*k/4,pts[i][1]))
    fine.append(pts[-1]); finger(pg,cdp,fine,step=20)
    R['drag_paint']=[pg.evaluate(f"grid[{p[0]}][{p[1]}]") for p in path]
    R['errors']=errs; b.close()
  return R
if __name__=="__main__":
  for d in ["iPhone 13","iPhone SE","Pixel 7","Galaxy S9+"]:
    for lvl in (3,1):
      print(d,"level",lvl,json.dumps(run(d,lvl)))
