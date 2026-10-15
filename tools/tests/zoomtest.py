"""Max-zoom + bubble test (iPhone 13 and SE touch emulation): at max zoom every lit pane shows ALL its badges (no overflow) at readable size;
smallest and most-badge panes across all levels; tap a lit pane -> bubble lists all neighbour counts; dismiss; pinch to max and pan work."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8800","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8800/index.html#levels";ok={}
BADGES="""()=>{const out=[];[...lock].forEach(i=>{});const g=[...document.querySelectorAll('#badges .bdg')];return g.map(x=>({n:x.querySelectorAll('text').length,fs:Math.min(...[...x.querySelectorAll('text')].map(t=>t.getBoundingClientRect().height)),txt:[...x.querySelectorAll('text')].map(t=>t.textContent).join(',')}))}"""
def tap_pane(pg,i):
  x,y=pg.evaluate("i=>{const b=board.querySelector('svg').getBoundingClientRect(),P=L.pieces[i],U=L.n*cs,s=Z.z/Z.rz;return[b.left+P.pole[0]*U*s,b.top+P.pole[1]*U*s]}",i);pg.touchscreen.tap(x,y)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"]);err=[]
  for dev in ["iPhone 13","iPhone SE"]:
    c=b.new_context(**{**p.devices[dev],"device_scale_factor":2});pg=c.new_page();pg.on("pageerror",lambda e:err.append(str(e)))
    pg.goto(U);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(300)
    # across all levels: light everything, jump to max zoom, check badges
    stats=pg.evaluate("LEVELS.map(l=>{const c=l.pieces.map((_,i)=>new Set(l.nb[i].map(j=>l.sol[0][j])).size);return{n:l.name,minrin:Math.min(...l.pieces.map(p=>p.rin)),maxb:Math.max(...c)}})")
    for li,st in enumerate(stats):
      pg.locator('#back').tap() if pg.evaluate("document.body.classList.contains('playing')") else None
      pg.wait_for_timeout(200);pg.locator(f'.card[data-l="{li}"]').tap();pg.wait_for_timeout(400)
      pg.evaluate("L.sol[0].forEach((v,i)=>{if(!lock.has(i)){grid[0][i]=v;lock.add(i)}});render()")
      pg.evaluate("Z.z=ZMAX;commit();clamp();apply()");pg.wait_for_timeout(300)
      # visit the smallest pane and the most-badge pane: centre on them
      res={}
      for tag,expr in (("smallest","L.pieces.map((p,i)=>[p.rin,i]).sort((a,b)=>a[0]-b[0])[0][1]"),("mostbadge","(()=>{let b=-1,bi=0;L.pieces.forEach((p,i)=>{const k=new Set(L.nb[i].map(j=>L.sol[0][j])).size*1000-p.rin*1000;if(k>b){b=k;bi=i}});return bi})()")):
        i=pg.evaluate(expr);pg.evaluate("i=>{const P=L.pieces[i],U=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U+padF);Z.ty=BV.h/2-(P.pole[1]*U+padF);clamp();apply()}",i);pg.wait_for_timeout(200)
        want=pg.evaluate("i=>new Set(L.nb[i].map(j=>L.sol[0][j])).size",i)
        d=pg.evaluate("i=>{const g=[...document.querySelectorAll('#badges .bdg')][[...lock].indexOf(i)];if(!g)return null;const t=[...g.querySelectorAll('text')];return{n:t.length,minpx:Math.min(...t.map(q=>q.getBoundingClientRect().height)),plus:/\\+/.test(g.textContent)}}",i)
        res[tag]=dict(pane=i,want=want,shown=d and d['n'],minpx=d and round(d['minpx'],1),plus=d and d['plus'],rin=pg.evaluate("i=>L.pieces[i].rin",i))
        if tag=="smallest" and li==4 and dev=="iPhone 13": pg.screenshot(path=D+"zoom_max_smallest_pane.png")
        if tag=="mostbadge" and li==4 and dev=="iPhone 13": pg.screenshot(path=D+"zoom_max_mostbadge_pane.png")
      allfull=pg.evaluate("(()=>{let bad=0;L.pieces.forEach((P,i)=>{const w=new Set(L.nb[i].map(j=>L.sol[0][j])).size,g=[...document.querySelectorAll('#badges .bdg')][[...lock].indexOf(i)];if(!g||g.querySelectorAll('text').length!=w||/\\+/.test(g.textContent))bad++});return bad})()")
      res['panes_with_missing_badges']=allfull;ok[f"{dev}|{st['n']}"]=res
    c.close()
  # Alpine Lake: ZMAX via real pinch, pan at max, ⤢ cycle, bubble
  for dev in ["iPhone 13","iPhone SE"]:
    c=b.new_context(**{**p.devices[dev],"device_scale_factor":2});pg=c.new_page();pg.on("pageerror",lambda e:err.append(str(e)))
    pg.goto(U);pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_timeout(300);pg.locator('.card[data-l="4"]').tap();pg.wait_for_timeout(600)
    pg.evaluate("(f=>{const seen=new Set(L.start),q=[...L.start];while(q.length&&seen.size<L.pieces.length*f){const i=q.shift();for(const j of L.nb[i])if(!seen.has(j)){seen.add(j);q.push(j)}}seen.forEach(i=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})})(.5)");pg.wait_for_timeout(500)
    cyc=[]
    for k in range(5): pg.locator('#ztog').tap();pg.wait_for_timeout(700);cyc.append(round(pg.evaluate("Z.z"),2))
    ok[f"{dev}|ztog_cycle"]=cyc
    # real pinch to max
    cdp=c.new_cdp_session(pg);tp=lambda t,pts:cdp.send("Input.dispatchTouchEvent",{"type":t,"touchPoints":[{"x":x,"y":y,"id":i} for i,(x,y) in enumerate(pts)]})
    pg.evaluate("zoomTo(1,BV.w/2,BV.h/2)");pg.wait_for_timeout(600);cx,cy=195,300
    tp("touchStart",[(cx-20,cy),(cx+20,cy)])
    for k in range(1,40): pg.wait_for_timeout(15);tp("touchMove",[(cx-20-k*4,cy),(cx+20+k*4,cy)])
    tp("touchEnd",[]);pg.wait_for_timeout(500)
    ok[f"{dev}|pinch_max"]=dict(z=round(pg.evaluate("Z.z"),2),crisp=pg.evaluate("Math.abs(Z.z-Z.rz)<.01"))
    moved=False
    for sgn in (-1,1):
      t0=pg.evaluate("[Z.tx,Z.ty]");tp("touchStart",[(190,350)])
      for k in range(1,8): pg.wait_for_timeout(15);tp("touchMove",[(190+sgn*k*20,350+sgn*k*15)])
      tp("touchEnd",[]);pg.wait_for_timeout(300);moved|=pg.evaluate("t=>Math.hypot(Z.tx-t[0],Z.ty-t[1])>50",t0)
    ok[f"{dev}|pan_at_max"]=moved
    # bubble: tap a lit pane with many neighbours colours
    pg.evaluate("zoomTo(Z0,BV.w/2,BV.h/2)");pg.wait_for_timeout(700)
    i=pg.evaluate("[...lock].sort((a,b)=>new Set(L.nb[b].map(j=>L.sol[0][j])).size-new Set(L.nb[a].map(j=>L.sol[0][j])).size)[0]")
    pg.evaluate("i=>{const P=L.pieces[i],U=L.n*cs;Z.tx=BV.w/2-(P.pole[0]*U+padF);Z.ty=BV.h/2-(P.pole[1]*U+padF);clamp();apply()}",i);pg.wait_for_timeout(200)
    tap_pane(pg,i);pg.wait_for_timeout(250)
    bub=pg.evaluate("(()=>{const b=document.querySelector('#bub'),r=b.getBoundingClientRect();return{on:b.classList.contains('on'),items:[...b.querySelectorAll('.bp b')].map(x=>+x.textContent),inside:r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight}})()")
    exp=pg.evaluate("i=>countsF(i).filter(n=>n)",i)
    pane=pg.evaluate("i=>{const b=board.querySelector('svg').getBoundingClientRect(),P=L.pieces[i],U=L.n*cs,s=Z.z/Z.rz;return[b.left+P.pole[0]*U*s,b.top+P.pole[1]*U*s]}",i);br=pg.evaluate("(()=>{const r=document.querySelector('#bub').getBoundingClientRect();return[r.left,r.top,r.right,r.bottom]})()")
    ok[f"{dev}|bubble"]=dict(bub,expected=exp,matches=bub['items']==exp,finger_covered=br[0]<=pane[0]<=br[2] and br[1]<=pane[1]<=br[3],hl=pg.evaluate("document.querySelectorAll('.cell.nbhl').length"))
    if dev=="iPhone 13": pg.screenshot(path=D+"bubble_alpine.png")
    pg.touchscreen.tap(20,700);pg.wait_for_timeout(200);ok[f"{dev}|bubble_dismissed"]=not pg.evaluate("document.querySelector('#bub').classList.contains('on')")
    c.close()
  ok['errors']=err
finally: srv.terminate()
bad=[k for k,v in ok.items() if isinstance(v,dict) and v.get('panes_with_missing_badges')]
print(json.dumps(ok,indent=0));print("BAD:",bad)
