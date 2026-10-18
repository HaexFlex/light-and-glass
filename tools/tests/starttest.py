"""Start screen: logo, big Play (continues last unfinished level, else first unsolved, else the level list), Collection / Options / Atelier
(with gold leaf counter), Levels link and Home. Real touch taps on iPhone 13 and iPhone SE."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8801","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8801/index.html#preload";B="http://localhost:8801/index.html";ok={};ERR=[]
FPS={'freeflower': 'v4l974', 'freekoi': '193fvo2', 'freeswan': '1k7oiq6', 'freefox': '85h3id', 'firstlight': '14ec0zr', 'eveningstar': '1hhefuh', 'moonwater': '7dxc6z', 'daisy': '1s4vj21', 'butterfly': 'jv91il', 'cottage': '14fw5ov'}
def mk(b,p,dev,scheme="dark"):
  c=b.new_context(**p.devices[dev],color_scheme=scheme,reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)));pg.on("dialog",lambda d:d.accept())
  pg.goto(U);pg.wait_for_timeout(500);return c,pg
vis=lambda pg,s:pg.locator(s).is_visible()
def part(pg,id,n):
  pg.evaluate("""([id,n])=>{const i=LEVELS.findIndex(l=>l.id==id);load(i);let k=0;L.pieces.forEach((_,j)=>{if(k<n&&!lock.has(j)){glowSet(0,j,L.sol[0][j]);k++}});saveLevel()}""",[id,n]);pg.wait_for_timeout(150)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
  for dev,tag in (("iPhone 13","13"),("iPhone SE","se")):
    K=lambda s:f"{tag}_{s}"
    c,pg=mk(b,p,dev)
    ok[K("title_is_first_screen")]=vis(pg,'#title') and not vis(pg,'#menu') and pg.evaluate("document.body.classList.contains('home')")
    ok[K("logo_art")]=vis(pg,'#title h1') and 'Light' in pg.locator('#title h1').inner_text() and pg.evaluate("document.querySelectorAll('#tArt path').length")>20
    g=pg.evaluate("""()=>{const q=s=>document.querySelector(s).getBoundingClientRect(),W=innerWidth,H=innerHeight,r={logo:q('#title .tlogo'),arch:q('#title .tarch'),play:q('#tPlay'),lv:q('#tLevels'),coll:q('#tColl'),opt:q('#tOpt'),at:q('#tAtelier'),foot:q('#tFoot')};
      const ks=Object.keys(r),inside=ks.every(k=>r[k].left>=0&&r[k].right<=W&&r[k].top>=0&&r[k].bottom<=H),
      order=r.logo.bottom<=r.arch.top+1&&r.arch.bottom<=r.play.top+1&&r.play.bottom<=r.lv.top+1&&r.lv.bottom<=r.coll.top+1&&r.coll.bottom<=r.at.top+1&&r.at.bottom<=r.foot.top+1&&Math.abs(r.coll.top-r.opt.top)<2&&r.coll.right<=r.opt.left+1;
      return{inside,order,playBig:r.play.height>=54&&r.play.width>r.coll.width*1.5,minTap:Math.min(r.coll.height,r.opt.height,r.at.height,r.play.height),arch:[r.arch.width,r.arch.height],H}}""")
    ok[K("layout_inside_ordered")]=g["inside"] and g["order"];ok[K("play_is_big")]=g["playBig"];ok[K("tap_targets_ge_40")]=g["minTap"]>=40;ok[K("layout_detail")]=g
    ok[K("atelier_counter")]="⚜ 4" in pg.locator('#tAtelier').inner_text() and 'atelier' in pg.locator('#tAtelier').inner_text().lower()
    ok[K("footer_begin")]=pg.locator('#tFoot').inner_text().startswith('Begin')
    pg.screenshot(path=D+f"start_title_{tag}.png")
    # Play on a fresh save: first unsolved level
    first=pg.evaluate("LEVELS[menuOrder().filter(o=>!o.sect)[0].i].id")
    pg.locator('#tPlay').tap();pg.wait_for_timeout(700)
    ok[K("play_fresh_opens_first_level")]=pg.evaluate("L.id")==first and pg.evaluate("document.body.classList.contains('playing')") and not vis(pg,'#title')
    # back goes to the level list; Home returns to the start screen
    pg.locator('#back').tap();pg.wait_for_timeout(300)
    ok[K("back_to_level_list")]=vis(pg,'#menu') and not vis(pg,'#title') and pg.locator('.card').count()>=11
    pg.locator('#homeBtn').scroll_into_view_if_needed();pg.locator('#homeBtn').tap();pg.wait_for_timeout(300)
    ok[K("home_returns")]=vis(pg,'#title') and not vis(pg,'#menu')
    pg.locator('#tLevels').tap();pg.wait_for_timeout(300);ok[K("levels_link")]=vis(pg,'#menu') and not vis(pg,'#title')
    pg.locator('.card[data-id="daisy"]').tap();pg.wait_for_timeout(500);ok[K("level_select_still_works")]=pg.evaluate("L.id")=="daisy"
    c.close()
    # Play continues the LAST played unfinished level
    c,pg=mk(b,p,dev)
    part(pg,"firstlight",3);pg.wait_for_timeout(50);part(pg,"daisy",4);pg.reload();pg.wait_for_timeout(500)
    ok[K("footer_continue")]=pg.locator('#tFoot').inner_text().startswith('Continue · ') and 'Daisy' in pg.locator('#tFoot').inner_text()
    pg.screenshot(path=D+f"start_title_continue_{tag}.png")
    pg.locator('#tPlay').tap();pg.wait_for_timeout(700)
    ok[K("play_continues_last_unfinished")]=pg.evaluate("L.id")=="daisy" and pg.evaluate("lock.size")>pg.evaluate("L.start.length")
    # an older partial is not preferred; after finishing daisy the other unfinished one is picked
    pg.evaluate("()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}");pg.wait_for_timeout(500);pg.reload();pg.wait_for_timeout(500)
    pg.locator('#tPlay').tap();pg.wait_for_timeout(700)
    ok[K("play_after_solved_picks_other_unfinished")]=pg.evaluate("L.id")=="firstlight"
    c.close()
    # no unfinished level: first unsolved
    c,pg=mk(b,p,dev)
    pg.evaluate("()=>{const f=LEVELS.filter(l=>l.id!='butterfly');f.forEach(l=>SAVE.levels[l.id]={solved:true,flawless:false,fp:l.fp});persist()}");pg.reload();pg.wait_for_timeout(500)
    ok[K("footer_next")]=pg.locator('#tFoot').inner_text().startswith('Next window')
    pg.locator('#tPlay').tap();pg.wait_for_timeout(700);ok[K("play_first_unsolved")]=pg.evaluate("L.id")=="butterfly"
    c.close()
    # everything solved: Play opens the level list
    c,pg=mk(b,p,dev)
    pg.evaluate("()=>{LEVELS.forEach(l=>SAVE.levels[l.id]={solved:true,flawless:false,fp:l.fp});persist()}");pg.reload();pg.wait_for_timeout(500)
    ok[K("footer_all_lit")]='All windows lit' in pg.locator('#tFoot').inner_text()
    pg.locator('#tPlay').tap();pg.wait_for_timeout(500);ok[K("play_all_solved_opens_list")]=vis(pg,'#menu') and not vis(pg,'#title') and not pg.evaluate("document.body.classList.contains('playing')")
    c.close()
    # buttons open the right screens and return to the start screen
    c,pg=mk(b,p,dev)
    pg.locator('#tColl').tap();pg.wait_for_timeout(300)
    ok[K("collection_opens")]=vis(pg,'#coll') and pg.locator('#collT').inner_text().lower()=="collection" and pg.evaluate("COLLTAB")=="windows"
    pg.locator('#collBack').tap();pg.wait_for_timeout(250);ok[K("collection_back_to_title")]=vis(pg,'#title') and not vis(pg,'#coll')
    pg.locator('#tOpt').tap();pg.wait_for_timeout(300);ok[K("options_opens")]=vis(pg,'#options') and 'App theme' in pg.locator('#options').inner_text()
    pg.screenshot(path=D+f"start_options_{tag}.png")
    pg.locator('#optBack').tap();pg.wait_for_timeout(250);ok[K("options_back_to_title")]=vis(pg,'#title') and not vis(pg,'#options')
    pg.locator('#tAtelier').tap();pg.wait_for_timeout(300)
    ok[K("atelier_opens")]=vis(pg,'#coll') and pg.locator('#collT').inner_text().lower()=="atelier" and pg.evaluate("COLLTAB")=="powerups" and pg.locator('.buy').count()==6
    ok[K("atelier_counter_header")]="⚜ 4" in pg.locator('#collCnt').inner_text() and "⚜ 4" in pg.locator('#bal').inner_text()
    pg.screenshot(path=D+f"start_atelier_{tag}.png")
    pg.locator('.buy[data-k="lantern"]').scroll_into_view_if_needed();pg.locator('.buy[data-k="lantern"]').tap();pg.wait_for_timeout(250)
    ok[K("atelier_buy_updates_counters")]=pg.evaluate("PU.gold")==2 and "⚜ 2" in pg.locator('#collCnt').inner_text()
    pg.locator('#collBack').tap();pg.wait_for_timeout(250);ok[K("atelier_title_counter_updated")]="⚜ 2" in pg.locator('#tAtelier').inner_text()
    ok[K("tabs_labelled")]=pg.evaluate("[...document.querySelectorAll('#collTabs button')].map(b=>b.textContent)")==["Windows","Atelier"]
    ok[K("save_fingerprints_ok")]=(lambda d:{k:v for k,v in d.items() if k in FPS})(pg.evaluate("Object.fromEntries(LEVELS.map(l=>[l.id,l.fp]))"))==FPS
    c.close()
    # light app theme: start screen keeps its golden-hour look and stays usable
    c,pg=mk(b,p,dev,scheme="light");ok[K("light_title_visible")]=vis(pg,'#title') and vis(pg,'#tPlay');pg.screenshot(path=D+f"start_title_light_{tag}.png");c.close()
  # deep links keep working
  c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page();pg.goto(B+"#levels");pg.wait_for_timeout(400);ok["hash_levels_opens_list"]=vis(pg,'#menu') and not vis(pg,'#title')
  pg.goto(B+"#lvl=2");pg.reload();pg.wait_for_timeout(500);ok["hash_lvl_opens_level"]=pg.evaluate("document.body.classList.contains('playing')");c.close()
  ok["errors"]=ERR;b.close()
finally: srv.terminate()
bad=[k for k,v in ok.items() if v is False]
print(json.dumps(ok,indent=1));print("FAILED:",bad);raise SystemExit(1 if bad or ERR else 0)
