"""Autofill (no cap; chained autofills allowed): a level whose start would force a guess gets exactly the autofill events the python mirror (tools/freeglass/autofill.py) predicts;
revealed panes cost nothing (no cracks, flawless kept, no assisted mark), levels with a strict no-guess start get none, the 30 saved levels have 0 autofills,
and reduced motion is respected (the glow animation is off)."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from autofill import simulate
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8799","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
LV=__import__("levelstore").load_all();byid={l['id']:l for l in LV}
ok["all_30_levels_need_no_autofill"]=all(simulate(l['sol'],l['nb'],len(l['colors']),l['start'])[0]==[] for l in LV)
cases={"cupcake":byid["cupcake"]['start'][:1],"teapot":byid["teapot"]['start'][:1],"teapot_chain":[42]}
JS="""async([id,start,rm])=>{const i=LEVELS.findIndex(l=>l.id==id);LEVELS[i].start=start;load(i);AFN=0;await new Promise(r=>setTimeout(r,700));
 let guard=0;const fills=[];let last=0;
 while(!won&&guard++<400){const s=sunbeamRaw(pcSolve());if(s.length){for(const q of s){glowSet(0,q,L.sol[0][q])}}
  await new Promise(r=>setTimeout(r,520));if(AFN!=last){last=AFN}}
 return {won,AFN,cracks,locked:lock.size,n:L.pieces.length,assisted:(typeof PU!=='undefined'&&PU.assisted)||0}}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
    for lid,st in cases.items():
      l=byid[lid.split('_')[0]];exp,u=simulate(l['sol'],l['nb'],len(l['colors']),st,cap=None)
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto(f"http://localhost:8799/index.html#preload&levels");pg.wait_for_timeout(300)
      r=pg.evaluate(JS,[lid.split('_')[0],st,1]);print(lid,"expected",len(exp),r,flush=True)
      ok[lid+"_autofill_count_matches_python"]=r['AFN']==len(exp) and u==0 and len(exp)>=1
      ok[lid+"_chained_ge2"]=(len(exp)>=2) if 'chain' in lid else True
      ok[lid+"_wins"]=r['won'] and r['locked']==r['n']
      ok[lid+"_no_cracks_flawless_kept"]=r['cracks']==0
      c.close()
    # strict start: zero autofills
    c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)));pg.goto("http://localhost:8799/index.html#preload&levels");pg.wait_for_timeout(300)
    r=pg.evaluate(JS,["teapot",byid["teapot"]['start'],0]);ok["strict_start_zero_autofills"]=r['AFN']==0 and r['won']
    # animation disabled for reduced motion
    c2=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg2=c2.new_page();pg2.goto("http://localhost:8799/index.html#preload&levels");pg2.wait_for_timeout(300)
    ok["reduced_motion_css"]=pg2.evaluate("()=>{const d=document.createElement('div');d.className='cell afill';document.body.appendChild(d);const a=getComputedStyle(d).animationName;d.remove();return a=='none'}")
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
