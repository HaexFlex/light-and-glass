"""Progress saving: place panes, reload -> restored; solve, reload -> solved mark; restart clears. iPhone 13 emulation, http server (localStorage)."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8765","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8765/index.html";ok={}
def tap_piece(pg,i):
  x,y=pg.evaluate("i=>{const r=cells[i].getBoundingClientRect(),P=L.pieces[i],U=L.n*cs,s=Z.z/Z.rz,b=board.querySelector('svg').getBoundingClientRect();return[b.left+P.pole[0]*U*s,b.top+P.pole[1]*U*s]}",i)
  pg.touchscreen.tap(x,y)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"]);c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page();err=[];pg.on("pageerror",lambda e:err.append(str(e)))
  pg.on("dialog",lambda d:d.accept())
  pg.goto(U);pg.wait_for_timeout(300);pg.locator('.card').nth(1).tap();pg.wait_for_timeout(500)
  # place 3 correct panes that are deducible-agnostic (just correct colour), via real taps; centre view on each
  targets=pg.evaluate("()=>[...L.pieces.keys()].filter(i=>!lock.has(i)).slice(0,3)")
  for i in targets:
    pg.evaluate("i=>{const P=L.pieces[i],U=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U+padF);Z.ty=BV.h/2-(P.pole[1]*U+padF);clamp();apply()}",i)
    k=pg.evaluate("i=>L.sol[0][i]",i);pg.locator('.sw').nth(k).tap();tap_piece(pg,i);pg.wait_for_timeout(250)
  # one wrong tap -> crack
  w=pg.evaluate("()=>[...L.pieces.keys()].find(i=>!lock.has(i))");pg.evaluate("i=>{const P=L.pieces[i],U=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U+padF);Z.ty=BV.h/2-(P.pole[1]*U+padF);clamp();apply()}",w)
  k=pg.evaluate("i=>(L.sol[0][i]+1)%L.colors.length",w);pg.locator('.sw').nth(k).tap();tap_piece(pg,w);pg.wait_for_timeout(900)
  before=pg.evaluate("()=>({locked:lock.size,cracks})")
  pg.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))")
  pg.reload();pg.wait_for_timeout(400)
  ok["menu_in_progress"]="in progress" in pg.locator('.card').nth(1).inner_text()
  pg.locator('.card').nth(1).tap();pg.wait_for_timeout(500)
  after=pg.evaluate("()=>({locked:lock.size,cracks,restored:%s.every(i=>lock.has(i))})"%json.dumps(targets))
  ok["restore"]=after["locked"]==before["locked"] and after["cracks"]==before["cracks"]==1 and after["restored"]
  # restart (confirm accepted)
  pg.locator('#restart').tap();pg.wait_for_timeout(500)
  ok["restart"]=pg.evaluate("()=>lock.size==L.start.length&&cracks==0")
  pg.reload();pg.wait_for_timeout(300);ok["restart_persists"]="in progress" not in pg.locator('.card').nth(1).inner_text()
  # solve level via correct placements through glowSet, then reload
  pg.locator('.card').nth(1).tap();pg.wait_for_timeout(400)
  pg.evaluate("()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}");pg.wait_for_timeout(800)
  ok["won"]=pg.evaluate("()=>won")
  pg.reload();pg.wait_for_timeout(400);t=pg.locator('.card').nth(1).inner_text();ok["solved_mark"]="flawless" in t
  ok["persist_api"]=pg.evaluate("()=>window.__persisted")
  # corrupt storage -> robust fallback
  pg.evaluate("()=>localStorage.setItem('lightglass.save.v1','{bad json')");pg.reload();pg.wait_for_timeout(300)
  ok["corrupt_ok"]=pg.locator('.card').count()==pg.evaluate('LEVELS.length')
  # fingerprints: legacy save (no fp) keeps progress; stale fp drops in-progress but keeps solved marks
  ids=pg.evaluate("()=>LEVELS.map(l=>l.id)")
  pg.evaluate("ids=>localStorage.setItem('lightglass.save.v1',JSON.stringify({v:1,levels:{[ids[0]]:{placed:[0,1,2].filter(i=>!LEVELS[0].start.includes(i)).slice(0,2),cracks:2},[ids[2]]:{placed:[5],cracks:1,solved:true,flawless:false,fp:'stale'}}}))",ids)
  pg.reload();pg.wait_for_timeout(300)
  sv=pg.evaluate("()=>JSON.parse(localStorage.getItem('lightglass.save.v1'))")
  ok["legacy_kept"]=len(sv["levels"][ids[0]]["placed"])==2 and sv["levels"][ids[0]]["fp"]==pg.evaluate("()=>LEVELS[0].fp")
  s2=sv["levels"][ids[2]];ok["stale_dropped_marks_kept"]=not s2.get("placed") and s2["solved"] and s2["fp"]==pg.evaluate("()=>LEVELS[2].fp")
  pg.locator('.card').nth(2).tap();pg.wait_for_timeout(400);ok["releaded_note"]="re-leaded" in pg.locator('#msg').inner_text()
  ok["errors"]=err;b.close()
finally: srv.terminate()
print(json.dumps(ok))
