"""Replay: win a level, 'Play again' from the win bar (confirm), win again; then replay from the level-select card. Solved mark/flawless kept, fingerprints unchanged. Screenshot of win bar."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8766","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8766/index.html";ok={}
SOLVE="()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}"
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"]);c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page();err=[];pg.on("pageerror",lambda e:err.append(str(e)))
  msgs=[];pg.on("dialog",lambda d:(msgs.append(d.message),d.accept()))
  pg.goto(U);pg.wait_for_timeout(300)
  fps=pg.evaluate("()=>LEVELS.map(l=>l.fp)")
  ok["no_replay_before_solve"]=pg.locator('.rp').count()==0
  pg.locator('.card[data-l="1"]').tap();pg.wait_for_timeout(500)
  pg.evaluate(SOLVE);pg.wait_for_timeout(6500)
  ok["won1"]=pg.evaluate("()=>won");ok["btn_visible"]=pg.locator('#replay').is_visible()
  bb=pg.locator('#winBar').bounding_box();fl=pg.evaluate("()=>{const r=document.querySelector('#rvSvg').getBoundingClientRect();return[r.top,r.bottom]}")
  pg.screenshot(path=D+"replay_win_bar.png")
  pg.locator('#replay').tap();pg.wait_for_timeout(600)
  ok["confirm_shown"]=any("again" in m for m in msgs)
  ok["cleared"]=pg.evaluate("()=>!won&&lock.size==L.start.length&&cracks==0")
  sv=pg.evaluate("()=>JSON.parse(localStorage.getItem('lightglass.save.v1')).levels[L.id]")
  ok["marks_kept"]=sv["solved"] and sv["flawless"] and not sv.get("placed")
  ok["no_win_bar"]=not pg.evaluate("()=>document.getElementById('app').classList.contains('win')")
  pg.evaluate(SOLVE);pg.wait_for_timeout(1000);ok["won2"]=pg.evaluate("()=>won")
  # menu replay
  pg.wait_for_timeout(5000);pg.locator('#toMenu').tap();pg.wait_for_timeout(400)
  ok["card_replay_btn"]=pg.locator('.card[data-l="1"] .rp').count()==1
  pg.locator('.card[data-l="1"] .rp').tap();pg.wait_for_timeout(600)
  ok["card_replay_opens_fresh"]=pg.evaluate("()=>!won&&lock.size==L.start.length&&cracks==0&&lv==1")
  pg.evaluate(SOLVE);pg.wait_for_timeout(1000);ok["won3"]=pg.evaluate("()=>won")
  ok["fp_same"]=pg.evaluate("()=>LEVELS.map(l=>l.fp)")==fps
  ok["save_key_kept"]=pg.evaluate("()=>JSON.parse(localStorage.getItem('lightglass.save.v1')).levels[LEVELS[1].id].solved")
  ok["no_err"]=not err
  b.close()
finally: srv.terminate()
print(json.dumps(ok,indent=1));raise SystemExit(0 if all(ok.values()) else 1)
