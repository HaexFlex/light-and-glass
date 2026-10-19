"""'Is not' bubbles (level.not = {pane: [colour,...]}): none of that pane's neighbours has these colours; shown on the dark pane as crossed-out colour dots.
Checks: data valid (colours truly absent around the pane, pane not a start/gift/detail); python: unique no-guess with bubbles, one-badge-at-a-time solvable (solve_direct)
and every bubble is needed for that; fingerprint changes only when `not` is present; game: bubbles drawn with the right dots, hidden once the pane is locked,
the game's solver uses them (neighbour candidates exclude the colours), the level is won by deduction alone with no cracks; a level without bubbles draws none."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from freeglass2 import solve, solve_direct
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8797","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
LV=__import__("levelstore").load_all();NT=[l for l in LV if l.get('not')];PLAIN=[l for l in LV if not l.get('not') and l.get('set')=='photo']
ok["tinted_photo_levels_all_have_bubbles"]=all(l.get('not') for l in LV if l.get('tier')==2 and l.get('set')=='photo') and len(NT)>=5
ok["bubbles_only_tinted_and_up"]=all(l.get('tier',1)>=2 for l in NT)
for l in NT:
  K=len(l['colors']);g=l.get('gift',[]);d=l.get('detail',[]);a=l.get('auto',[]);nt=l['not'];args=(l['sol'],l['nb'],K,l['start'])
  ok[l['id']+"_data_valid"]=all(k.isdigit() and int(k) not in set(l['start'])|set(g)|set(d) and v and all(0<=c<K and all(l['sol'][q]!=c for q in l['nb'][int(k)]) for c in v) for k,v in nt.items())
  ok[l['id']+"_unique_no_guess"]=solve(*args,gift=g,detail=d,auto=a,nots=nt,canes=l.get('canes'),ros=l.get('ros'))==0
  M=solve_direct   # Tinted and Stained generators both use the one-badge-at-a-time model
  ok[l['id']+"_one_badge_at_a_time"]=solve_direct(*args,gift=g,detail=d,auto=a,nots=nt,canes=l.get('canes'),ros=l.get('ros'))==0
  ok[l['id']+"_every_bubble_needed"]=all(M(*args,gift=g,detail=d,auto=a,nots={x:v for x,v in nt.items() if x!=k},canes=l.get('canes'),ros=l.get('ros'))>0 for k in nt)
  ok[l['id']+"_metrics_recorded"]=l['metrics'].get('nots')==len(nt)
JS="""async(id)=>{const i=LEVELS.findIndex(l=>l.id==id);load(i);await new Promise(r=>setTimeout(r,400));
 const bub=[...document.querySelectorAll('#badges .nbdg')].map(e=>[+e.dataset.not,e.querySelectorAll('circle').length]);
 const D=pcSolve();let used=true;NOT.forEach((cs,p)=>L.nb[p].forEach(q=>{if(!lock.has(q))cs.forEach(c=>{if(D[q]>>c&1)used=false})}));
 let guard=0;while(!won&&guard++<600){const s=sunbeamRaw(pcSolve());for(const q of s)glowSet(0,q,L.sol[0][q]);await new Promise(r=>setTimeout(r,120))}
 const after=document.querySelectorAll('#badges .nbdg').length;return {bub,used,won,cracks,after,nnot:NOT.size}}"""
FP="""(drop)=>levelFP({pieces:L.pieces,sol:[L.sol[0]],colors:L.colors,gift:L.gift,detail:L.detail,auto:L.auto,not:drop?undefined:L.not})"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
    for l in NT:
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8797/index.html#preload&levels");pg.wait_for_timeout(300)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",l['id']);pg.wait_for_timeout(500);pg.screenshot(path=f"/tmp/nottest_{l['id']}.png")
      r=pg.evaluate(JS,l['id']);print(l['id'],r,flush=True)
      exp=sorted([int(k),len(v)] for k,v in l['not'].items())
      ok[l['id']+"_game_draws_bubbles"]=sorted(r['bub'])==exp and r['nnot']==len(exp)
      ok[l['id']+"_game_solver_uses_bubbles"]=r['used']
      ok[l['id']+"_game_won_by_deduction_no_cracks"]=r['won'] and r['cracks']==0
      ok[l['id']+"_bubbles_hidden_once_locked"]=r['after']==0
      ok[l['id']+"_fingerprint_depends_on_not"]=pg.evaluate(FP,0)!=pg.evaluate(FP,1)
      c.close()
    for l in PLAIN[:2]:
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8797/index.html#preload&levels");pg.wait_for_timeout(300)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",l['id']);pg.wait_for_timeout(400)
      ok[l['id']+"_no_bubbles_drawn"]=pg.locator('#badges .nbdg').count()==0
      ok[l['id']+"_fingerprint_unchanged_without_not"]=pg.evaluate(FP,0)==pg.evaluate(FP,1)
      c.close()
    b.close()
finally: srv.terminate()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("failed:",[k for k,v in ok.items() if not v]);sys.exit(1 if [k for k,v in ok.items() if not v] else 0)
