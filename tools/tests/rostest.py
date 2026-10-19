"""Rosettes (level.ros = [{panes:[3-6 contiguous], cols:[colour set]}]): a bold lead ring round the group + a tag listing which colours occur inside (no counts).
Checks: data valid (contiguous, 3-6 panes, exact colour set, no overlap, not starts/gift/detail), only Jewel; python: unique no-guess and one-badge-at-a-time with
all clues, every rosette needed, 3-6 rosettes; fingerprint changes only when rosettes are present; game: one ring path per rosette that runs only along the group's
outer border, one tag per rosette with one dot per colour, both puzzle themes; the game's solver uses rosettes soundly; won by deduction, no cracks; plain levels draw none."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from freeglass2 import solve, solve_direct
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8793","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
LV=__import__("levelstore").load_all();RS=[l for l in LV if l.get('ros')];PLAIN=[l for l in LV if not l.get('ros') and l.get('set')=='photo']
ok["jewel_photo_levels_all_have_rosettes"]=all(l.get('ros') for l in LV if l.get('tier')==4 and l.get('set')=='photo') and len(RS)>=2
ok["rosettes_only_jewel"]=all(l.get('tier')==4 for l in RS)
def contig(l,ps):
  ps=set(ps);seen={min(ps)};st=[min(ps)]
  while st:
    x=st.pop()
    for y in l['nb'][x]:
      if y in ps and y not in seen: seen.add(y);st.append(y)
  return seen==ps
for l in RS:
  K=len(l['colors']);g=l.get('gift',[]);d=l.get('detail',[]);a=l.get('auto',[]);kw=dict(gift=g,detail=d,auto=a,nots=l.get('not'),canes=l.get('canes'));args=(l['sol'],l['nb'],K,l['start']);rs=l['ros']
  allp=[x for r in rs for x in r['panes']]
  ok[l['id']+"_data_valid"]=all(3<=len(r['panes'])<=6 and contig(l,r['panes']) and sorted(r['cols'])==sorted({l['sol'][x] for x in r['panes']}) for r in rs) and len(allp)==len(set(allp)) and not set(allp)&(set(l['start'])|set(g)|set(d))
  ok[l['id']+"_unique_no_guess"]=solve(*args,ros=rs,**kw)==0
  ok[l['id']+"_one_badge_at_a_time"]=solve_direct(*args,ros=rs,**kw)==0
  ok[l['id']+"_every_rosette_needed"]=all(solve_direct(*args,ros=[x for x in rs if x is not r],**kw)>0 for r in rs)
  ok[l['id']+"_3_to_6_rosettes"]=3<=len(rs)<=6
  ok[l['id']+"_metrics_recorded"]=l['metrics'].get('ros')==len(rs)
JS="""async(id)=>{const i=LEVELS.findIndex(l=>l.id==id);load(i);await new Promise(r=>setTimeout(r,400));
 const rings=[...document.querySelectorAll('.ros .rosr')].map(e=>e.getAttribute('d')),tags=[...document.querySelectorAll('.rtags .rtag')].map(e=>e.querySelectorAll('circle').length);
 const U=L.n*cs,k=p=>(p[0]*U).toFixed(1)+' '+(p[1]*U).toFixed(1);let outer=true;
 L.ros.forEach((r,j)=>{const segs=(rings[j]||'').split('M').filter(Boolean);segs.forEach(sg=>{const [p,q]=sg.split('L');const owners=L.pieces.map((P,pi)=>P.p.some((x,xi)=>{const y=P.p[(xi+1)%P.p.length];return (k(x)==p.trim()&&k(y)==q.trim())||(k(y)==p.trim()&&k(x)==q.trim())})?pi:-1).filter(x=>x>=0);if(owners.filter(o=>r.panes.includes(o)).length!=1)outer=false});if(!segs.length)outer=false});
 const w=rings.length?parseFloat(getComputedStyle(document.querySelector('.ros .rosr')).strokeWidth):0,lw=parseFloat(getComputedStyle(document.querySelector('.cell')).strokeWidth);
 let guard=0,used=0,unsound=0;while(!won&&guard++<900){const sv=ROS;ROS=[];const D0=pcSolve();ROS=sv;const D1=pcSolve();D0.forEach((d,q)=>{if(D1[q]!=d){used++;if((D1[q]&d)!=D1[q]||!(D1[q]>>L.sol[0][q]&1))unsound++}});const s=sunbeamRaw(D1);for(const q of s)glowSet(0,q,L.sol[0][q]);await new Promise(r=>setTimeout(r,90))}
 return {n:rings.length,tags,outer,w,lw,used,unsound,won,cracks,nr:ROS.length}}"""
FP="""(drop)=>levelFP({pieces:L.pieces,sol:[L.sol[0]],colors:L.colors,gift:L.gift,detail:L.detail,auto:L.auto,not:L.not,canes:L.canes,ros:drop?undefined:L.ros})"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
    for l in RS:
      for theme in ('dark','light'):
        c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce',color_scheme=theme);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
        pg.goto("http://localhost:8793/index.html#preload&levels");pg.wait_for_timeout(300)
        r=pg.evaluate(JS,l['id']);print(l['id'],theme,r,flush=True)
        ok[f"{l['id']}_{theme}_one_ring_per_rosette_on_outer_border"]=r['n']==len(l['ros'])==r['nr'] and r['outer']
        ok[f"{l['id']}_{theme}_one_tag_per_rosette_with_its_colours"]=r['tags']==[len(x['cols']) for x in l['ros']]
        ok[f"{l['id']}_{theme}_ring_bold"]=r['w']>=2.5*r['lw']
        ok[f"{l['id']}_{theme}_game_solver_uses_rosettes_soundly"]=r['used']>0 and r['unsound']==0
        ok[f"{l['id']}_{theme}_won_by_deduction_no_cracks"]=r['won'] and r['cracks']==0
        if theme=='dark': ok[l['id']+"_fingerprint_depends_on_rosettes"]=pg.evaluate(FP,0)!=pg.evaluate(FP,1)
        c.close()
    for l in PLAIN[:2]:
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8793/index.html#preload&levels");pg.wait_for_timeout(300)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",l['id']);pg.wait_for_timeout(400)
      ok[l['id']+"_no_rosettes_drawn"]=pg.locator('.ros .rosr').count()==0 and pg.locator('.rtags .rtag').count()==0
      ok[l['id']+"_fingerprint_unchanged_without_rosettes"]=pg.evaluate(FP,0)==pg.evaluate(FP,1)
      c.close()
    b.close()
finally: srv.terminate()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("failed:",[k for k,v in ok.items() if not v]);sys.exit(1 if [k for k,v in ok.items() if not v] else 0)
