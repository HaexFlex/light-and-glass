"""Options screen: independent App/Puzzle themes (+migration of the old lightglass.theme), sound, colour symbols, reset tutorial,
saves note. Real touch taps on iPhone 13 and iPhone SE. Screenshots -> docs/screenshots/options_*.png"""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8767","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8767/index.html";ok={}
light=lambda pg:pg.evaluate("()=>document.body.classList.contains('light')")
plight=lambda pg:pg.evaluate("()=>document.querySelector('#bv').classList.contains('plight')")
chrome=lambda pg:pg.evaluate("()=>{const c=getComputedStyle(document.querySelector('#pubar')).backgroundColor.match(/\\d+/g).map(Number),f=getComputedStyle(document.querySelector('.cell:not(.f)')).fill;return[c[0]+c[1]+c[2]>450,f.includes('milk')]}")
ls=lambda pg,k:pg.evaluate("k=>localStorage.getItem(k)",k)
def seg(pg,w,v): pg.locator(f'#options button[data-th="{w}:{v}"]').tap();pg.wait_for_timeout(120)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"]);err=[]
  for dev,tag in (("iPhone 13","13"),("iPhone SE","se")):
    c=b.new_context(**p.devices[dev],color_scheme="dark");pg=c.new_page();pg.on("pageerror",lambda e:err.append(str(e)));pg.goto(U);pg.wait_for_timeout(300)
    K=lambda s:f"{tag}_{s}"
    # reachable from the title / level-select screen two ways
    pg.locator('#optMenu').tap();ok[K("open_icon")]=pg.locator('#options').is_visible();pg.locator('#optBack').tap()
    ok[K("closed")]=not pg.locator('#options').is_visible()
    pg.locator('#optBtn').tap();ok[K("open_button")]=pg.locator('#options').is_visible()
    pg.screenshot(path=D+f"options_dark_{tag}.png")
    # independent: app dark + puzzle light
    seg(pg,"app","dark");seg(pg,"puzzle","light")
    ok[K("pressed")]=pg.evaluate("()=>[...document.querySelectorAll('#options .seg button[aria-pressed=true]')].map(b=>b.dataset.th).join()")=="app:dark,puzzle:light"
    ok[K("menu_follows_app_dark")]=not light(pg)
    ok[K("preview")]=pg.evaluate("()=>[pvApp.className,pvPuz.className].join()")=="pa-dark,pp-light"
    pg.screenshot(path=D+f"options_app_dark_puzzle_light_{tag}.png")
    pg.locator('#optBack').tap();pg.locator('.card[data-l="1"]').tap();pg.wait_for_timeout(500)
    ok[K("puzzle_light_in_level")]=plight(pg) and not light(pg)
    ok[K("chrome_follows_app_board_follows_puzzle")]=chrome(pg)==[False,True]
    pg.screenshot(path=D+f"options_puzzle_light_level_{tag}.png")
    pg.locator('#back').tap();pg.wait_for_timeout(300);ok[K("menu_dark_after_level")]=not light(pg)
    pg.reload();pg.wait_for_timeout(300);ok[K("persist_app")]=not light(pg)
    pg.locator('.card[data-l="1"]').tap();pg.wait_for_timeout(500);ok[K("persist_puzzle")]=plight(pg) and not light(pg)
    ok[K("keys")]=[ls(pg,"lightglass.theme.app"),ls(pg,"lightglass.theme.puzzle")]==["dark","light"]
    # opposite: app light + puzzle dark
    pg.locator('#back').tap();pg.locator('#optMenu').tap();seg(pg,"app","light");seg(pg,"puzzle","dark");ok[K("menu_light")]=light(pg)
    pg.screenshot(path=D+f"options_app_light_puzzle_dark_{tag}.png")
    pg.locator('#optBack').tap();pg.locator('.card[data-l="1"]').tap();pg.wait_for_timeout(400);ok[K("puzzle_dark_in_level")]=light(pg) and not plight(pg)
    ok[K("chrome_light_board_dark")]=chrome(pg)==[True,False]
    pg.screenshot(path=D+f"options_app_light_puzzle_dark_level_{tag}.png")
    # auto follows system
    pg.locator('#back').tap();pg.locator('#optMenu').tap();seg(pg,"app","auto");seg(pg,"puzzle","auto");ok[K("auto_dark")]=not light(pg)
    pg.emulate_media(color_scheme="light");pg.wait_for_timeout(200);ok[K("auto_follows_system")]=light(pg)
    pg.emulate_media(color_scheme="dark")
    # sound / symbols
    pg.locator('#optSound').tap();ok[K("sound_off")]=pg.evaluate("()=>!SND")and ls(pg,"lightglass.sound")=="0"
    pg.locator('#optSound').tap();ok[K("sound_on")]=pg.evaluate("()=>SND")and ls(pg,"lightglass.sound")=="1"
    pg.locator('#optSym').tap();ok[K("sym_off")]=pg.evaluate("()=>!SYM&&document.body.classList.contains('nosym')")and ls(pg,"lightglass.symbols")=="0"
    pg.locator('#optBack').tap();ok[K("sym_menu_synced")]="off" in pg.locator('#symMenu').inner_text()
    pg.locator('#optMenu').tap();pg.locator('#optSym').tap();ok[K("sym_on")]=pg.evaluate("()=>SYM")
    # reset tutorial clears only its key
    pg.evaluate("()=>{localStorage.setItem('lightglass.tutorial.v1','1');localStorage.setItem('lightglass.powerups.v1','{\"keep\":1}')}")
    sv=ls(pg,"lightglass.save.v1");th=ls(pg,"lightglass.theme.app")
    pg.locator('#optTut').scroll_into_view_if_needed();pg.locator('#optTut').tap();pg.wait_for_timeout(100)
    ok[K("tutorial_cleared")]=ls(pg,"lightglass.tutorial.v1") is None
    ok[K("others_untouched")]=ls(pg,"lightglass.save.v1")==sv and ls(pg,"lightglass.theme.app")==th and ls(pg,"lightglass.powerups.v1")=='{"keep":1}' and ls(pg,"lightglass.symbols")=="1"
    ok[K("saves_note")]="stay on this device" in pg.locator('#options').inner_text()
    pg.locator('#options').evaluate("e=>e.scrollTop=e.scrollHeight");pg.wait_for_timeout(100);pg.screenshot(path=D+f"options_bottom_{tag}.png")
    ok[K("fits_width")]=pg.evaluate("()=>document.querySelector('#options').scrollWidth<=innerWidth+1")
    c.close()
    # migration of the old single key
    for old,sysc in (("light","dark"),("dark","light"),(None,"dark")):
      c=b.new_context(**p.devices[dev],color_scheme=sysc);pg=c.new_page();pg.goto(U);pg.wait_for_timeout(200)
      pg.evaluate("o=>{localStorage.removeItem('lightglass.theme.app');localStorage.removeItem('lightglass.theme.puzzle');o?localStorage.setItem('lightglass.theme',o):localStorage.removeItem('lightglass.theme')}",old)
      pg.reload();pg.wait_for_timeout(300)
      want=old or sysc
      ok[K(f"migrate_{old}_menu")]=light(pg)==(want=="light")
      pg.locator('.card[data-l="1"]').tap();pg.wait_for_timeout(400);ok[K(f"migrate_{old}_level")]=light(pg)==(want=="light") and plight(pg)==(want=="light")
      ok[K(f"migrate_{old}_keys")]=[ls(pg,"lightglass.theme.app"),ls(pg,"lightglass.theme.puzzle")]==([old,old] if old else ["auto","auto"])
      ok[K(f"migrate_{old}_oldkey_kept")]=ls(pg,"lightglass.theme")==old
      c.close()
  ok["errors"]=err;b.close()
finally: srv.terminate()
print(json.dumps(ok,indent=1));raise SystemExit(0 if all(v for v in ok.values() if not isinstance(v,list)) and not ok["errors"] else 1)
