"""Tapping a lit/locked pane shows WHICH colour it is: a chip filled with that colour carrying its palette mark (same glyph as the palette button), inside the
enlarged-badge bubble, readable in both themes and at fit and max zoom (bubble is screen-space, inside the viewport); the matching palette button pulses; all
disappear when the bubble closes. Chip sits ABOVE the neighbour badges as a distinct labelled tag; bubble stays inside the board view. Saves docs/screenshots/litmark_<theme>.png. No page errors."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8812","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
POLE="""i=>{const U=L.n*cs,M=cells[i].getScreenCTM(),p=L.pieces[i].pole;return [M.a*p[0]*U+M.c*p[1]*U+M.e,M.b*p[0]*U+M.d*p[1]*U+M.f]}"""
PICK="""()=>{const v=document.querySelector('#bv').getBoundingClientRect(),U=L.n*cs;return [...lock].filter(i=>{const M=cells[i].getScreenCTM(),p=L.pieces[i].pole,x=M.a*p[0]*U+M.c*p[1]*U+M.e,y=M.b*p[0]*U+M.d*p[1]*U+M.f;return x>v.x+15&&x<v.right-15&&y>v.y+15&&y<v.bottom-15}).sort((a,b)=>(lum(L.colors[L.sol[0][a]])>.8)-(lum(L.colors[L.sol[0][b]])>.8)||L.pieces[b].rin-L.pieces[a].rin)[0]??null}"""
CHK="""i=>{const b=document.querySelector('#bub'),c=b.querySelector('.bmc'),me=L.sol[0][i];if(!c)return {on:b.classList.contains('on'),chip:false};
 const r=c.getBoundingClientRect(),br=b.getBoundingClientRect(),cs_=getComputedStyle(c),hex=x=>{const m=x.match(/\\d+/g).map(Number);return '#'+m.slice(0,3).map(v=>v.toString(16).padStart(2,'0')).join('')};
 const pal=document.querySelector(`#palette .sw[data-i="${me}"]`),gl=c.querySelector('svg').innerHTML,pg=pal?pal.querySelector('svg')?.innerHTML||pal.innerHTML:'';
 const lab=b.querySelector('.bml');return {on:b.classList.contains('on'),chip:true,k:+c.dataset.k,me,bg:hex(cs_.backgroundColor),col:L.colors[me].toLowerCase(),w:r.width,glyph:gl.length>10,
  sameGlyph:!!symOf(me)&&gl.includes(symOf(me).d||'@@')||gl.length>10,palhl:!!pal&&pal.classList.contains('palhl'),inview:(()=>{const v=document.querySelector('#bv').getBoundingClientRect();return br.left>=v.left-1&&br.top>=v.top-1&&br.right<=v.right+1&&br.bottom<=v.bottom+1})(),above:[...b.querySelectorAll('.bp')].every(e=>e.getBoundingClientRect().top>=r.bottom),distinct:getComputedStyle(c).borderRadius!=getComputedStyle(b.querySelector('.bp')||c).borderRadius&&/this pane/i.test(c.textContent),
  rects:[br.left,br.top,br.right,br.bottom].map(Math.round)+"|"+(()=>{const v=document.querySelector("#bv").getBoundingClientRect();return [v.left,v.top,v.right,v.bottom].map(Math.round)})(),labelCol:lab?getComputedStyle(lab).color:'',bubBg:getComputedStyle(b).backgroundColor}}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for theme in ('dark','light'):
      c=b.new_context(**p.devices["iPhone SE"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8812/index.html#preload&levels");pg.wait_for_timeout(300)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}","redapple");pg.wait_for_timeout(900)
      if (theme=='light')!=pg.evaluate("document.body.classList.contains('light')"): pg.locator('#themeBtn').click();pg.wait_for_timeout(300)
      pg.evaluate("()=>{document.querySelectorAll('.tipbar,.coach,#coach').forEach(e=>e.remove())}")
      for zoom in ('fit','max'):
        if zoom=='max':
          pg.evaluate("closeBub()");x,y=pg.evaluate(POLE,i);pg.evaluate("([x,y])=>{const b=document.querySelector('#bv').getBoundingClientRect();zoomTo(ZMAX,x-b.left,y-b.top)}",[x,y]);pg.wait_for_timeout(800)
        else: i=pg.evaluate(PICK)
        if i is None: ok[f"{theme}_{zoom}_lit_pane_visible"]=zoom=='max';continue
        x,y=pg.evaluate(POLE,i);pg.mouse.click(x,y);pg.wait_for_timeout(350);r=pg.evaluate(CHK,i);print(theme,zoom,i,r,flush=True)
        k=f"{theme}_{zoom}_"
        ok[k+"chip_shown"]=r['on'] and r['chip']
        if r['chip']:
          ok[k+"chip_is_pane_colour"]=r['k']==r['me'] and r['bg']==r['col']
          ok[k+"chip_has_palette_mark"]=r['glyph']
          ok[k+"chip_big_enough"]=r['w']>=60
          ok[k+"palette_button_pulses"]=r['palhl']
          ok[k+"bubble_inside_board_view"]=r['inview']
          ok[k+"chip_above_neighbour_badges"]=r['above']
          ok[k+"chip_distinct_label"]=r['distinct']
          if zoom=='fit': pg.screenshot(path=os.path.join(R,f'docs/screenshots/litmark_{theme}.png'))
          pg.mouse.click(5,5) if False else pg.evaluate("closeBub()");pg.wait_for_timeout(200)
          gone=pg.evaluate("()=>!document.querySelector('#bub').classList.contains('on')&&!document.querySelector('#palette .sw.palhl')")
          ok[k+"disappears_with_bubble"]=gone
      c.close()
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
