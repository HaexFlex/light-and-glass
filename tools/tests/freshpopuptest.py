"""Tap a lit (start) pane on a fresh photo level: the popup must appear with enlarged neighbour
badges and the pane's own colour chip (palette mark), in every photo display mode (photo / flat / tinted).
This catches the baked-canvas regression where fill:none cells were not hittable."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
SHOT=os.path.join("/workspace/puzzle-studio/fresh/rework")
os.makedirs(SHOT,exist_ok=True)
srv=subprocess.Popen(["python3","-m","http.server","8841","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
POLE="""i=>{const U=L.n*cs,M=cells[i].getScreenCTM(),p=L.pieces[i].pole;return [M.a*p[0]*U+M.c*p[1]*U+M.e,M.b*p[0]*U+M.d*p[1]*U+M.f]}"""
CHK="""i=>{const b=document.querySelector('#bub'),c=b&&b.querySelector('.bmc'),me=L.sol[0][i];
 if(!b||!b.classList.contains('on'))return {on:false,chip:false,baked:document.querySelector('#bv').classList.contains('baked'),mode:photoMode(),cellFill:getComputedStyle(cells[i]).fill};
 const r=c?c.getBoundingClientRect():null,bps=[...b.querySelectorAll('.bp')];
 return {on:true,chip:!!c,k:c?+c.dataset.k:null,me,badges:bps.length,glyph:!!(c&&c.querySelector('svg')&&c.querySelector('svg').innerHTML.length>10),
  above:c&&bps.length?bps.every(e=>e.getBoundingClientRect().top>=c.getBoundingClientRect().bottom-1):true,
  baked:document.querySelector('#bv').classList.contains('baked'),mode:photoMode()}}"""
# pick a visible start pane
PICK="""()=>{const v=document.querySelector('#bv').getBoundingClientRect(),U=L.n*cs;
 return (L.start||[]).filter(i=>{const M=cells[i].getScreenCTM(),p=L.pieces[i].pole,x=M.a*p[0]*U+M.c*p[1]*U+M.e,y=M.b*p[0]*U+M.d*p[1]*U+M.f;return x>v.x+12&&x<v.right-12&&y>v.y+12&&y<v.bottom-12}).sort((a,b)=>L.pieces[b].rin-L.pieces[a].rin)[0]??(L.start||[])[0]??null}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    c=b.new_context(**p.devices["iPhone SE"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.goto("http://localhost:8841/index.html#preload&levels");pg.wait_for_timeout(400)
    # prefer a playable fresh photo level; Kitchen if present, else first fresh
    lid=pg.evaluate("""()=>{const ids=LEVELS.filter(l=>l.set=='fresh'&&l.mode=='free'&&isPlayable(l)&&!l.hints&&l.id!='firstlight').map(l=>l.id);
      return ids.includes('fresh17')?'fresh17':(ids[0]||null)}""")
    ok["fresh_level"]=bool(lid)
    print("level",lid,flush=True)
    for mode in ('photo','flat','tinted'):
      pg.evaluate("""(m)=>{localStorage.setItem('lightglass.photomode',m)}""",mode)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",lid);pg.wait_for_timeout(900)
      pg.evaluate("()=>{hintEnd0&&hintEnd0();const m=document.querySelector('#mexp');if(m)m.classList.remove('on');closeBub&&closeBub()}")
      pg.wait_for_timeout(400)
      i=pg.evaluate(PICK)
      ok[f"{mode}_has_lit_pane"]=i is not None
      if i is None:
        print(mode,"no lit pane",flush=True);continue
      # confirm baked fill is none in photo/tinted/flat
      fill=pg.evaluate("i=>getComputedStyle(cells[i]).fill",i)
      baked=pg.evaluate("()=>document.querySelector('#bv').classList.contains('baked')&&['photo','flat','tinted'].includes(photoMode())")
      print(mode,"pane",i,"fill",fill,"baked",baked,flush=True)
      x,y=pg.evaluate(POLE,i)
      pg.mouse.click(x,y);pg.wait_for_timeout(400)
      r=pg.evaluate(CHK,i)
      print(mode,r,flush=True)
      k=f"{mode}_"
      ok[k+"popup_on_lit_tap"]=r.get('on') is True
      ok[k+"colour_chip"]=r.get('chip') is True and r.get('k')==r.get('me')
      ok[k+"chip_has_palette_mark"]=r.get('glyph') is True
      ok[k+"chip_above_badges"]=r.get('above') is True
      if mode=='tinted':
        pg.screenshot(path=os.path.join(SHOT,"fix_popup_tinted.png"))
      pg.evaluate("closeBub&&closeBub()")
    c.close();b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
if ERR: print("ERR",ERR)
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
