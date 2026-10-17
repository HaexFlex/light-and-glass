"""Designed autofill (level.auto): panes in `auto` reveal by themselves, chained, once a neighbour is locked, even when logic could deduce them.
Checks: fingerprint changes only when `auto` is present; python solver/validator mirror; in the game an untouched level settles at start + auto chain (no deduced pane is placed for the player,
no autofill needed); the player then finishes with the remaining panes, wins, no cracks, flawless kept; a level without `auto` reveals nothing by itself."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from autofill import simulate
from freeglass2 import solve
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8798","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
LV=__import__("levelstore").load_all();AU=[l for l in LV if l.get('auto')]
ok["some_levels_have_auto"]=len(AU)>=1
def chain(l):
  lit=set(l['start']);ch=True
  while ch:
    ch=False
    for a in l['auto']:
      if a not in lit and any(q in lit for q in l['nb'][a]): lit.add(a);ch=True
  return lit
for l in AU:
  K=len(l['colors']);N=len(l['pieces']);g=l.get('gift',[]);d=l.get('detail',[])
  ok[l['id']+"_auto_valid"]=len(set(l['auto']))==len(l['auto']) and not set(l['auto'])&(set(g)|set(d)|set(l['start']))
  ok[l['id']+"_python_no_guess"]=solve(l['sol'],l['nb'],K,l['start'],gift=g,detail=d,auto=l['auto'])==0
  ok[l['id']+"_auto_share_4_to_45pct"]=0.25<=len(l['auto'])/(N-len(g)-len(d))<=0.45
  ok[l['id']+"_few_lit_starts"]=len(l['start'])/(N-len(g)-len(d))<=0.06
  ok[l['id']+"_recorded_autofill"]=len(simulate(l['sol'],l['nb'],K,l['start'],gift=g,detail=d,auto=l['auto'])[0])==l['metrics'].get('autofills',0)
FP="""()=>levelFP({pieces:L.pieces,sol:[L.sol[0]],colors:L.colors,gift:L.gift,detail:L.detail,auto:L.auto})"""
JS="""async([id,noauto])=>{const i=LEVELS.findIndex(l=>l.id==id);const keep=LEVELS[i].auto;if(noauto)LEVELS[i].auto=[];load(i);await new Promise(r=>setTimeout(r,300));
 const a=[...AUTO].length;await new Promise(r=>setTimeout(r,6000));const settled=[...lock].sort((x,y)=>x-y);AFNs=AFN;
 let guard=0;while(!won&&guard++<600){const s=sunbeamRaw(pcSolve());for(const q of s)glowSet(0,q,L.sol[0][q]);await new Promise(r=>setTimeout(r,200))}
 const r={a,settled,won,cracks,AFN,locked:lock.size,n:L.pieces.length};LEVELS[i].auto=keep;return r}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
    for l in AU[:2]:
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8798/index.html#preload&levels");pg.wait_for_timeout(300)
      r=pg.evaluate(JS,[l['id'],0]);exp=sorted(chain(l));print(l['id'],{k:v for k,v in r.items() if k!='settled'},len(exp),flush=True)
      ok[l['id']+"_game_settles_at_start_plus_auto_chain"]=r['settled']==exp and r['a']==len(l['auto'])
      ok[l['id']+"_game_wins_no_cracks"]=r['won'] and r['cracks']==0 and r['locked']+len(l.get('detail',[]))==r['n']
      nch=len(chain(l))-len(l['start']);ok[l['id']+"_auto_reveals_counted_as_autofill_events"]=nch<=r['AFN']<=len(l['auto'])+len(simulate(l['sol'],l['nb'],len(l['colors']),l['start'],gift=l.get('gift',[]),detail=l.get('detail',[]),auto=l['auto'])[0])
      c.close();c=b.new_context(**p.devices['iPhone 13'],reduced_motion='reduce');pg=c.new_page();pg.goto('http://localhost:8798/index.html#preload&levels');pg.wait_for_timeout(300);r2=pg.evaluate(JS,[l['id'],1]);ok[l['id']+"_no_auto_no_self_reveal"]=set(l['start'])<=set(r2['settled']) and len(r2['settled'])<=len(l['start'])+1
      fp=pg.evaluate(FP);fp2=pg.evaluate(FP.replace("auto:L.auto","auto:[]"));ok[l['id']+"_fingerprint_depends_on_auto"]=fp!=fp2
      c.close()
    b.close()
finally: srv.terminate()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("failed:",[k for k,v in ok.items() if not v]);sys.exit(1 if [k for k,v in ok.items() if not v] else 0)
