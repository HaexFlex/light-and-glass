"""Lazy level loading: index.html carries only the manifest; a level's glass data is fetched when it is opened (once, then cached in memory),
a short loading state is shown, a failed/corrupt fetch gives a retry + back option, manifest entries match the data files, fingerprints equal the old ones."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
import levelstore
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8802","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
B="http://localhost:8802/index.html";ok={};ERR=[]
FPS={'freeflower': 'v4l974', 'freekoi': '193fvo2', 'freeswan': '1k7oiq6', 'freefox': 'lwl4wr', 'firstlight': '14ec0zr', 'eveningstar': '1hhefuh', 'moonwater': '7dxc6z', 'daisy': '1s4vj21', 'butterfly': 'jv91il', 'cottage': '14fw5ov'}
M=levelstore.manifest();html=open(R+"/index.html").read()
ok["index_has_no_glass_data"]='"pieces":[' not in html and len(html)<250000
A=levelstore.archive_manifest()
ok["manifest_matches_files"]=len(M)==23 and all(m["set"]=="fresh" for m in M) and all(os.path.exists(R+"/"+m['file']) for m in M) and all(len(d['pieces'])==m['panes'] and len(d['colors'])==m['ncolors'] and len(d['start'])==m['nstart'] and len(d.get('gift',[]))==m['ngift'] and d.get('tier',3)==m['tier'] for m,d in zip(M,levelstore.load_all()))
ok["archive_manifest_41"]=len(A)==41 and all(m["set"]=="archive" for m in A) and all(os.path.exists(R+"/"+m["file"]) for m in A)
ok["manifest_fingerprints_unchanged"]={m['id']:m['fp'] for m in A if m['id'] in FPS}==FPS
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)));reqs=[]
  pg.on("request",lambda r:reqs.append(r.url) if "/levels/data/" in r.url else 0)
  pg.goto(B+"#levels");pg.wait_for_timeout(400)
  ok["menu_without_level_data"]=pg.locator('.card').count()==23 and pg.evaluate("LEVELS.filter(l=>l.loaded).length")==0 and not reqs
  ok["cards_use_manifest"]="panes" in pg.locator('.card').first.inner_text()
  pg.locator('.card[data-id="fresh09"]').tap();pg.wait_for_timeout(700)
  json_reqs=[u for u in reqs if "fresh09.json" in u]
  ok["open_fetches_one_level"]=len(json_reqs)==1 and pg.evaluate("LEVELS.filter(l=>l.loaded).map(l=>l.id)")==["fresh09"] and pg.evaluate("document.body.classList.contains('playing')")
  ok["loaded_fp_equals_manifest"]=pg.evaluate("levelFP(L)===L.fp")
  pg.evaluate("menu()");pg.locator('.card[data-id="fresh09"]').tap();pg.wait_for_timeout(300)
  ok["reopen_uses_memory_cache"]=len([u for u in reqs if "fresh09.json" in u])==1 and pg.evaluate("document.body.classList.contains('playing')")
  # loading state (slow network)
  pg.evaluate("menu()")
  held=[]
  def slow(route): held.append(route)
  pg.route("**/levels/data/fresh01.json*",slow);pg.locator('.card[data-id="fresh01"]').tap();pg.wait_for_timeout(450)
  ok["loading_state_shown"]=pg.evaluate("document.querySelector('#ldg').classList.contains('on')") and "Loading" in pg.locator('#ldgT').inner_text() and not pg.evaluate("document.body.classList.contains('playing')")
  [h.continue_() for h in held];pg.wait_for_timeout(900);ok["loading_state_clears"]=pg.evaluate("!document.querySelector('#ldg').classList.contains('on')&&document.body.classList.contains('playing')&&L.id=='fresh01'")
  pg.unroute("**/levels/data/fresh01.json*")
  # failure -> retry / back
  pg.evaluate("menu()");pg.route("**/levels/data/fresh04.json*",lambda r:r.abort());pg.locator('.card[data-id="fresh04"]').tap();pg.wait_for_timeout(500)
  ok["error_state_with_retry"]=pg.evaluate("document.querySelector('#ldg').classList.contains('err')") and pg.locator('#ldgRetry').is_visible() and not pg.evaluate("document.body.classList.contains('playing')")
  pg.unroute("**/levels/data/fresh04.json*");pg.locator('#ldgRetry').tap();pg.wait_for_timeout(600)
  ok["retry_recovers"]=pg.evaluate("document.body.classList.contains('playing')&&L.id=='fresh04'&&!document.querySelector('#ldg').classList.contains('on')")
  pg.evaluate("menu()");pg.route("**/levels/data/fresh05.json*",lambda r:r.abort());pg.locator('.card[data-id="fresh05"]').tap();pg.wait_for_timeout(400);pg.locator('#ldgBack').tap();pg.wait_for_timeout(300)
  ok["back_returns_to_menu"]=pg.evaluate("!document.body.classList.contains('playing')&&!document.querySelector('#ldg').classList.contains('on')")
  pg.unroute("**/levels/data/fresh05.json*")
  # corrupt data must be rejected (fingerprint) and recover on retry
  def bad(route):
    r=route.fetch();d=json.loads(r.text());d['sol'][0]=(d['sol'][0]+1)%len(d['colors']);route.fulfill(response=r,body=json.dumps(d))
  pg.route("**/levels/data/fresh08.json*",bad);pg.locator('.card[data-id="fresh08"]').tap();pg.wait_for_timeout(500)
  ok["corrupt_data_rejected"]=pg.evaluate("document.querySelector('#ldg').classList.contains('err')&&!LEVELS.find(l=>l.id=='fresh08').loaded")
  pg.unroute("**/levels/data/fresh08.json*");pg.locator('#ldgRetry').tap();pg.wait_for_timeout(600);ok["corrupt_then_retry_ok"]=pg.evaluate("document.body.classList.contains('playing')&&L.id=='fresh08'")
  # hash opening + solve hook work with lazy data
  pg.goto(B+"#lvl=2&solve");pg.reload();pg.wait_for_timeout(900)
  ok["hash_lvl_solve_lazy"]=pg.evaluate("document.body.classList.contains('playing')&&grid[0].every((v,i)=>v==L.sol[0][i])")
  # title art (home) fetches a playable photo window lazily without errors
  pg.goto(B);pg.wait_for_timeout(700);ok["home_title_art"]=pg.evaluate("document.querySelector('#tArt svg')!=null")
  ok["no_page_errors"]=not ERR
  b.close()
srv.terminate()
print(json.dumps(ok,indent=1));print("failed:",[k for k,v in ok.items() if not v]);sys.exit(0 if all(ok.values()) else 1)
