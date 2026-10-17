"""Alpine Lake + colour-symbol screenshots (iPhone 13 emulation): start, mid-play dark/light, palette/badge close-up,
Fox with symbols, symbols-off check, win reveal (no overlap between floor picture and win bar), quantisation compare."""
import os,json,subprocess,time
from PIL import Image
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8791","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8791/index.html#levels";ok={}
MID="""(f)=>{const seen=new Set(L.start),q=[...L.start];while(q.length&&seen.size<Math.round(L.pieces.length*f)){const i=q.shift();for(const j of L.nb[i])if(!seen.has(j)){seen.add(j);q.push(j)}}
 seen.forEach(i=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])});return seen.size}"""
FOCUS="""(z)=>{zoomTo(z,BV.w/2,BV.h/2)}"""
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"]);err=[]
  def page(theme,dpr=2):
    c=b.new_context(**{**p.devices["iPhone 13"],"device_scale_factor":dpr});pg=c.new_page();pg.on("pageerror",lambda e:err.append(str(e)))
    pg.goto(U);pg.evaluate(f"localStorage.clear();localStorage.setItem('lightglass.theme','{theme}')");pg.reload();pg.wait_for_timeout(300);return pg
  pg=page('dark');pg.screenshot(path=D+"alpine_menu.png")
  pg.locator('.card[data-l="4"]').tap();pg.wait_for_timeout(700);pg.screenshot(path=D+"alpine_start_dark.png")
  ok['aspect']=pg.evaluate("(()=>{const r=board.querySelector('svg').getBoundingClientRect();return +(r.width/r.height).toFixed(3)})()")
  n=pg.evaluate(MID,.4);pg.evaluate("zoomTo(1.6,BV.w/2,BV.h/2)");pg.wait_for_timeout(900);pg.screenshot(path=D+"alpine_mid_dark.png")
  pg.evaluate("zoomTo(1,BV.w/2,BV.h/2)");pg.wait_for_timeout(600);pg.screenshot(path=D+"alpine_mid_dark_fit.png")
  # close-up: zoom in on lit panes with many badges, then crop board+palette
  pg.evaluate("(()=>{const i=[...lock].sort((a,b)=>L.pieces[b].rin-L.pieces[a].rin)[3],P=L.pieces[i],U=L.n*cs;Z.z=3.2;commit();const U2=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U2+padF);Z.ty=BV.h/2-(P.pole[1]*U2+padF);clamp();apply()})()");pg.wait_for_timeout(700)
  pg.screenshot(path=D+"alpine_closeup_badges_palette.png",clip={"x":0,"y":150,"width":390,"height":560})
  pg=page('light');pg.locator('.card[data-l="4"]').tap();pg.wait_for_timeout(500);pg.evaluate(MID,.4);pg.evaluate("zoomTo(1.6,BV.w/2,BV.h/2)");pg.wait_for_timeout(900);pg.screenshot(path=D+"alpine_mid_light.png")
  pg=page('dark');pg.locator('.card[data-l="3"]').tap();pg.wait_for_timeout(500);pg.evaluate(MID,.3);pg.wait_for_timeout(900);pg.screenshot(path=D+"fox_symbols_dark.png")
  pg=page('light');pg.locator('.card[data-l="3"]').tap();pg.wait_for_timeout(500);pg.evaluate(MID,.3);pg.wait_for_timeout(900);pg.screenshot(path=D+"fox_symbols_light.png")
  # symbols toggle
  pg.locator('#back').tap();pg.wait_for_timeout(300);pg.locator('#symMenu').tap();ok['toggle_off']=pg.evaluate("!SYM&&document.body.classList.contains('nosym')&&localStorage.getItem('lightglass.symbols')==='0'")
  pg.reload();pg.wait_for_timeout(300);ok['toggle_persist']=pg.evaluate("!SYM");pg.locator('.card[data-l="3"]').tap();pg.wait_for_timeout(500)
  ok['off_circles']=pg.evaluate("document.querySelectorAll('#badges circle').length>0&&document.querySelectorAll('#badges .gy').length==0");pg.screenshot(path=D+"fox_symbols_off.png")
  pg.locator('#back').tap();pg.locator('#symMenu').tap();ok['toggle_on_again']=pg.evaluate("SYM")
  # win reveal
  for th in ('dark','light'):
    pg=page(th);pg.locator('.card[data-l="4"]').tap();pg.wait_for_timeout(500)
    pg.evaluate("L.sol[0].forEach((v,i)=>{if(!lock.has(i))glowSet(0,i,v)})");pg.wait_for_timeout(6500);pg.screenshot(path=D+f"alpine_win_{th}.png")
    if th=='dark':
      ok['won']=pg.evaluate("won");ok['win_no_overlap']=pg.evaluate("(()=>{const f=document.querySelector('#rvFloor').getBoundingClientRect(),w=document.querySelector('#rvWin').getBoundingClientRect(),bar=document.querySelector('#winBar').getBoundingClientRect(),t=document.querySelector('#rvTitle').getBoundingClientRect();return f.bottom<=bar.top&&w.bottom<=f.top&&t.bottom<=w.top&&f.left>=0&&f.right<=innerWidth})()")
  ok['errors']=err
finally: srv.terminate()
# quantisation compare (original | quantised), side by side
a=Image.open(R+"/levels/source/mountains.jpg").convert('RGB');q=Image.open(R+"/tools/freeglass/out_alpinelake_quant.png").convert('RGB')
w=600;h=round(w*a.height/a.width);a=a.resize((w,h),Image.LANCZOS);q=q.resize((w,h),Image.NEAREST)
c=Image.new('RGB',(2*w+12,h),(20,17,15));c.paste(a,(0,0));c.paste(q,(w+12,0));c.save(D+"alpine_original_vs_quantised.png")
print(json.dumps(ok))
