"""Theme (dark/light) test + screenshots. iPhone 13, served over http so localStorage persists."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8799","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8799/index.html#levels";ok={}
MID="""()=>{const seen=new Set(L.start),q=[...L.start];while(q.length&&seen.size<Math.round(L.pieces.length*.3)){const i=q.shift();for(const j of L.nb[i])if(!seen.has(j)){seen.add(j);q.push(j)}}
 seen.forEach(i=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])});
 const c=[...seen].map(i=>L.pieces[i].pole).reduce((a,p)=>[a[0]+p[0]/seen.size,a[1]+p[1]/seen.size],[0,0]),U=L.n*cs;Z.tx=BV.w/2-(c[0]*U+padF);Z.ty=BV.h/2-(c[1]*U+padF);clamp();apply();return seen.size}"""
light=lambda pg:pg.evaluate("()=>document.body.classList.contains('light')")
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"]);err=[]
  # system default
  for sch in ["light","dark"]:
    c=b.new_context(**p.devices["iPhone 13"],color_scheme=sch);pg=c.new_page();pg.goto(U);pg.wait_for_timeout(300)
    ok[f"default_{sch}"]=light(pg)==(sch=="light")
    pg.screenshot(path=f"{D}theme_{sch}_menu.png")
    pg.locator('.card[data-l="3"]').tap();pg.wait_for_timeout(600);pg.screenshot(path=f"{D}theme_{sch}_fox_start.png")
    n=pg.evaluate(MID);pg.wait_for_timeout(900);pg.screenshot(path=f"{D}theme_{sch}_fox_mid.png")
    if sch=="light":
      # close-up: zoom on a lit white pane next to unlit glass
      i=pg.evaluate("()=>{const w=L.colors.indexOf('#f6f1ea');return [...L.pieces.keys()].find(i=>L.sol[0][i]==w&&!lock.has(i)&&L.nb[i].some(j=>!lock.has(j)&&j!=i))}")
      pg.evaluate("i=>{glowSet(0,i,L.sol[0][i]);Z.z=2.6;commit();const P=L.pieces[i],U=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U+padF);Z.ty=BV.h/2-(P.pole[1]*U+padF);clamp();apply()}",i)
      pg.wait_for_timeout(900);pg.screenshot(path=f"{D}theme_light_white_closeup.png")
    c.close()
  # persistence + toggles (system dark)
  c=b.new_context(**p.devices["iPhone 13"],color_scheme="dark");pg=c.new_page();pg.on("pageerror",lambda e:err.append(str(e)));pg.goto(U);pg.wait_for_timeout(300)
  pg.locator('#themeMenu').tap();ok["menu_toggle"]=light(pg)
  pg.reload();pg.wait_for_timeout(300);ok["persist_after_reload"]=light(pg)
  pg.locator('.card[data-l="3"]').tap();pg.wait_for_timeout(500)
  pg.evaluate("()=>{[...L.pieces.keys()].filter(i=>!lock.has(i)).slice(0,5).forEach(i=>glowSet(0,i,L.sol[0][i]))}")
  before=pg.evaluate("()=>({n:lock.size,grid:JSON.stringify(grid),z:Z.z})");save0=pg.evaluate("()=>localStorage.getItem('lightglass.save.v1')")
  pg.locator('#themeBtn').tap();pg.wait_for_timeout(200)
  after=pg.evaluate("()=>({n:lock.size,grid:JSON.stringify(grid),z:Z.z})")
  ok["level_toggle_dark"]=not light(pg);ok["state_kept_on_toggle"]=before==after
  ok["save_untouched_by_toggle"]=pg.evaluate("()=>localStorage.getItem('lightglass.save.v1')")==save0
  pg.reload();pg.wait_for_timeout(300);ok["dark_persist"]=not light(pg)
  pg.locator('.card[data-l="3"]').tap();pg.wait_for_timeout(500);ok["progress_after_reload"]=pg.evaluate("()=>lock.size")==before["n"]
  ok["theme_key"]=pg.evaluate("()=>localStorage.getItem('lightglass.theme')")
  ok["errors"]=err;b.close()
finally: srv.terminate()
print(json.dumps(ok))
