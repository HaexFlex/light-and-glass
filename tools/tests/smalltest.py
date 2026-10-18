"""Tutorial hints + play-through (real touch taps) of every small level (iPhone 13 emulation), level-select sections,
win reveal overlap check, screenshots: menu, tutorial start/hint steps, each new level start + win."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8798","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8798/index.html#levels";ok={}
IDS=["firstlight","eveningstar","moonwater","daisy","butterfly","cottage"]
def pt(pg,i): return pg.evaluate("i=>{const b=board.querySelector('svg').getBoundingClientRect(),P=L.pieces[i],U=L.n*cs,s=Z.z/Z.rz;return[b.left+P.pole[0]*U*s,b.top+P.pole[1]*U*s]}",i)
def tap(pg,i,col=None):
  if col is not None: pg.locator('.sw').nth(col).tap()
  x,y=pt(pg,i);pg.touchscreen.tap(x,y);pg.wait_for_timeout(60)
def hint(pg): return pg.evaluate("(()=>{const h=document.querySelector('#hint');return h.classList.contains('on')?h.innerText:null})()")
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"]);err=[]
  def ctxpage(theme='dark',dev="iPhone 13"):
    c=b.new_context(**{**p.devices[dev],"device_scale_factor":2});pg=c.new_page();pg.on("pageerror",lambda e:err.append(str(e)));pg.goto(U);pg.evaluate(f"localStorage.clear();localStorage.setItem('lightglass.theme','{theme}')");pg.reload();pg.wait_for_timeout(400);return c,pg
  c,pg=ctxpage()
  ok['menu_order']=pg.evaluate("[...document.querySelectorAll('#cards .sect,#cards .card')].map(e=>e.classList.contains('sect')?'#'+e.textContent:e.dataset.id)")
  ok['first_card']=pg.evaluate("document.querySelector('#cards .card').dataset.id")
  pg.screenshot(path=D+"menu_sections_top.png");pg.evaluate("document.querySelector('#menu').scrollTop=9999");pg.wait_for_timeout(200);pg.screenshot(path=D+"menu_sections_bottom.png");pg.evaluate("document.querySelector('#menu').scrollTop=0")
  # tutorial: hints
  pg.locator('.card[data-id="firstlight"]').tap();pg.wait_for_timeout(700);L_=pg.evaluate("[L.pieces.length,L.start,L.colors.length]");ok['tutorial']=L_
  ok['h0']=hint(pg);pg.screenshot(path=D+"tutorial_start_hint1.png")
  s0=L_[1][0];tap(pg,s0);pg.wait_for_timeout(300);ok['h1']=hint(pg);ok['bubble_on_tap']=pg.evaluate("document.querySelector('#bub').classList.contains('on')");pg.screenshot(path=D+"tutorial_hint2_bubble.png")
  sol=pg.evaluate("L.sol[0]");nb=pg.evaluate("L.nb")
  pg.touchscreen.tap(4,4)
  w=next(j for j in nb[s0] if j!=s0 and j not in L_[1]);pg.locator('.sw').nth(sol[w]).tap();pg.wait_for_timeout(300);ok['h2']=hint(pg);pg.screenshot(path=D+"tutorial_hint3_place.png")
  tap(pg,w);pg.wait_for_timeout(300);ok['h3']=hint(pg);pg.screenshot(path=D+"tutorial_hint4_done.png")
  ok['flag_set_after_end']=None
  pg.wait_for_timeout(7600);ok['hint_auto_end']=hint(pg) is None;ok['flag']=pg.evaluate("localStorage.getItem('lightglass.tutorial.v1')");ok['save_has_no_flag']='tutorial' not in pg.evaluate("localStorage.getItem('lightglass.save.v1')")
  pg.reload();pg.wait_for_timeout(300);pg.locator('.card[data-id="firstlight"]').tap();pg.wait_for_timeout(600);ok['hint_not_again']=hint(pg) is None
  c.close()
  # dismiss via ✕ stores flag
  c,pg=ctxpage();pg.locator('.card[data-id="firstlight"]').tap();pg.wait_for_timeout(500);pg.locator('#hintX').tap();pg.wait_for_timeout(200);ok['dismiss_flag']=pg.evaluate("localStorage.getItem('lightglass.tutorial.v1')")=='1' and hint(pg) is None;c.close()
  # other levels: no hints, play with real taps, screenshots
  for th in ('dark','light'):
   for lid in IDS:
    c,pg=ctxpage(th);pg.locator(f'.card[data-id="{lid}"]').tap();pg.wait_for_timeout(500)
    if lid!='firstlight': ok[f'{lid}_no_hint']=hint(pg) is None
    else: pg.locator('#hintX').tap();pg.wait_for_timeout(300)
    pg.evaluate("Z.z=Z.rz;");info=pg.evaluate("[L.name,L.pieces.length,L.start,Z.z,L.metrics.mono_share]")
    if th=='dark' or lid=='firstlight': pg.screenshot(path=D+f"level_{lid}_start_{th}.png")
    sol=pg.evaluate("L.sol[0]");nb=pg.evaluate("L.nb");N=len(sol);cr=0
    # wrong colour once -> crack
    s0=next(s for s in info[2] if any(j not in info[2] for j in nb[s]));w=next(j for j in nb[s0] if j not in info[2]);tap(pg,w,(sol[w]+1)%pg.evaluate("L.colors.length"));pg.wait_for_timeout(750);ok[f'{lid}_{th}_crack']=pg.evaluate("cracks")==1 and pg.evaluate(f"grid[0][{w}]")==-1
    for rnd in range(40):
      lit=set(pg.evaluate("[...lock]"));front=[j for j in range(N) if j not in lit and any(k in lit for k in nb[j])]
      if not front: break
      for j in front:
        x,y=pt(pg,j);vis=pg.evaluate("([x,y])=>{const v=document.querySelector('#bv').getBoundingClientRect();return x>v.x+3&&x<v.right-3&&y>v.y+3&&y<v.bottom-3}",[x,y])
        if not vis: pg.evaluate("i=>{const P=L.pieces[i],U=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U+padF);Z.ty=BV.h/2-(P.pole[1]*U+padF);clamp();apply()}",j)
        tap(pg,j,sol[j])
    pg.wait_for_timeout(300);ok[f'{lid}_{th}_won']=pg.evaluate("won");
    if th=='dark' or lid=='firstlight':
      pg.wait_for_timeout(6500);pg.screenshot(path=D+f"level_{lid}_win_{th}.png")
    ok[f'{lid}_{th}_overlap_free']=pg.evaluate("(()=>{const f=document.querySelector('#rvFloor').getBoundingClientRect(),w=document.querySelector('#rvWin').getBoundingClientRect(),bar=document.querySelector('#winBar').getBoundingClientRect(),t=document.querySelector('#rvTitle').getBoundingClientRect();return f.bottom<=bar.top&&w.bottom<=f.top&&t.bottom<=w.top&&f.left>=0&&f.right<=innerWidth&&Math.abs(f.width/f.height-ASP())<.02})()") if th=='dark' else None
    ok[f'{lid}_{th}_info']=info;c.close()
  ok['errors']=err
finally: srv.terminate()
print(json.dumps(ok,indent=0))
bad=[k for k,v in ok.items() if v is False]; print("FAILED:",bad)
