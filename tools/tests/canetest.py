"""Lead canes (level.canes = [[a,b],...]): neighbours a and b have DIFFERENT colours; drawn as a thick lead line on their shared border.
Checks: data valid (neighbours, different colours, shared edge), only Stained and up, python: unique no-guess and one-badge-at-a-time with canes, every cane needed,
5-10 canes, auto share 12-18%; fingerprint changes only when canes are present; game: one thick cane path per cane on the shared border (light and dark puzzle theme),
the game's solver uses canes, the level is won by deduction alone with no cracks; a level without canes draws none."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from freeglass2 import solve, solve_direct
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8795","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
LV=__import__("levelstore").load_all();CN=[l for l in LV if l.get('canes')];PLAIN=[l for l in LV if not l.get('canes') and l.get('set')=='photo']
ok["stained_photo_levels_all_have_canes"]=all(l.get('canes') for l in LV if l.get('tier')==3 and l.get('set')=='photo') and len(CN)>=2
ok["canes_only_stained_and_up"]=all(l.get('tier',1)>=3 for l in CN)
def edge(l,a,b):
  A=[tuple(x) for x in l['pieces'][a]['p']];B=[tuple(x) for x in l['pieces'][b]['p']];eb={frozenset((B[i],B[(i+1)%len(B)])) for i in range(len(B))}
  return any(frozenset((A[i],A[(i+1)%len(A)])) in eb for i in range(len(A)))
for l in CN:
  K=len(l['colors']);g=l.get('gift',[]);d=l.get('detail',[]);a=l.get('auto',[]);nt=l.get('not');cn=l['canes'];args=(l['sol'],l['nb'],K,l['start']);body=len(l['pieces'])-len(g)-len(d)
  ok[l['id']+"_data_valid"]=all(len(c)==2 and c[1] in l['nb'][c[0]] and l['sol'][c[0]]!=l['sol'][c[1]] and edge(l,*c) for c in cn) and len({frozenset(c) for c in cn})==len(cn)
  ok[l['id']+"_unique_no_guess"]=solve(*args,gift=g,detail=d,auto=a,nots=nt,canes=cn,ros=l.get('ros'))==0
  ok[l['id']+"_one_badge_at_a_time"]=solve_direct(*args,gift=g,detail=d,auto=a,nots=nt,canes=cn,ros=l.get('ros'))==0
  ok[l['id']+"_every_cane_needed"]=all(solve_direct(*args,gift=g,detail=d,auto=a,nots=nt,canes=[x for x in cn if x!=c],ros=l.get('ros'))>0 for c in cn)
  ok[l['id']+"_5_to_10_canes"]=l.get('tier')!=3 or 5<=len(cn)<=10
  ok[l['id']+"_auto_share_12_18"]=l.get('tier')!=3 or 0.12<=len(a)/body<=0.18
  ok[l['id']+"_metrics_recorded"]=l['metrics'].get('canes')==len(cn)
JS="""async(id)=>{const i=LEVELS.findIndex(l=>l.id==id);load(i);await new Promise(r=>setTimeout(r,400));
 const paths=[...document.querySelectorAll('.canes .cane')].map(e=>e.getAttribute('d')),w=paths.length?parseFloat(getComputedStyle(document.querySelector('.canes .cane')).strokeWidth):0,lw=parseFloat(getComputedStyle(document.querySelector('.cell')).strokeWidth);
 const exp=L.canes.map(([a,b])=>canePath(a,b));const D=pcSolve();
 let guard=0,used=0,unsound=0;while(!won&&guard++<700){const sv=CANES;CANES=[];const D0=pcSolve();CANES=sv;const D1=pcSolve();D0.forEach((d,i)=>{if(D1[i]!=d){used++;if((D1[i]&d)!=D1[i]||!(D1[i]>>L.sol[0][i]&1))unsound++}});const s=sunbeamRaw(D1);for(const q of s)glowSet(0,q,L.sol[0][q]);await new Promise(r=>setTimeout(r,100))}
 return {used,unsound,n:paths.length,same:JSON.stringify(paths)==JSON.stringify(exp),nonempty:paths.every(p=>p.length>8),w,lw,won,cracks,nc:CANES.length}}"""
USE="""()=>{const saved=CANES;CANES=[];const D0=pcSolve();CANES=saved;const D1=pcSolve();let fewer=0;D0.forEach((d,i)=>{if(D1[i]!=d){if((D1[i]&d)!=D1[i])fewer=-1e9;fewer++}});return fewer}"""
FP="""(drop)=>levelFP({pieces:L.pieces,sol:[L.sol[0]],colors:L.colors,gift:L.gift,detail:L.detail,auto:L.auto,not:L.not,canes:drop?undefined:L.canes})"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
    for l in CN:
      for theme in ('dark','light'):
        c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce',color_scheme=theme);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
        pg.goto("http://localhost:8795/index.html#preload&levels");pg.wait_for_timeout(300)
        pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",l['id']);pg.wait_for_timeout(400)
        # lock a few starts' neighbours? the game solver must narrow candidates with canes once one side is known
        r=pg.evaluate(JS,l['id']);print(l['id'],theme,r,flush=True)
        ok[f"{l['id']}_{theme}_one_cane_path_per_cane_on_shared_border"]=r['n']==len(l['canes'])==r['nc'] and r['same'] and r['nonempty']
        ok[f"{l['id']}_{theme}_cane_clearly_thicker_than_lead"]=r['w']>=2.5*r['lw']
        ok[f"{l['id']}_{theme}_game_solver_uses_canes_soundly"]=(r['used']>0 or l.get('tier')==4) and r['unsound']==0   # Jewel canes are needed by the one-badge model; the stronger game solver may not need them
        ok[f"{l['id']}_{theme}_won_by_deduction_no_cracks"]=r['won'] and r['cracks']==0
        if theme=='dark': ok[l['id']+"_fingerprint_depends_on_canes"]=pg.evaluate(FP,0)!=pg.evaluate(FP,1)
        c.close()
    for l in PLAIN[:2]:
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8795/index.html#preload&levels");pg.wait_for_timeout(300)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",l['id']);pg.wait_for_timeout(400)
      ok[l['id']+"_no_canes_drawn"]=pg.locator('.canes .cane').count()==0
      ok[l['id']+"_fingerprint_unchanged_without_canes"]=pg.evaluate(FP,0)==pg.evaluate(FP,1)
      c.close()
    b.close()
finally: srv.terminate()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("failed:",[k for k,v in ok.items() if not v]);sys.exit(1 if [k for k,v in ok.items() if not v] else 0)
