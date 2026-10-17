"""Detail panes: a normal pane holding a small painted image, fixed logic colour (not in the palette), never tapped/cracked/counted. Unlit plain glass until ONE neighbour is locked, then the
picture fades in (small sparkle; plain fade only with reduced motion). Reveal is derived from locked panes, so save/load needs no extra state. Uses an existing level (teapot) with one pane
marked as detail, in the test only (not in the shipped manifest)."""
import os,sys,json,subprocess,time
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from freeglass2 import choose_start,solve
from autofill import simulate
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8802","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
base=[l for l in __import__("levelstore").load_all() if l['id']=='teapot'][0]
K=len(base['colors']);nb=base['nb']
cands=[i for i in range(len(nb)) if len(nb[i])>=3 and len({base['sol'][q] for q in nb[i]})>=2]
for d in cands:   # a detail pane none of whose neighbours is a start pane, so the reveal really happens during play
  start,_=choose_start(base['sol'],nb,K,seeds=2,detail=[d])
  if not set(start)&set(nb[d]): break
else: raise SystemExit("no suitable detail pane")
P=base['pieces'][d]['p']
flat=[c for pt in P for c in pt] if isinstance(P[0],(list,tuple)) else list(P)
X=flat[0::2];Y=flat[1::2];x0,x1,y0,y1=min(X),max(X),min(Y),max(Y);mx,my=(x0+x1)//2,(y0+y1)//2
art={'s':100000,'pal':['#2b1b10','#e8c25a'],'poly':[[1,[x0,y0,x1,y0,x1,y1,x0,y1]],[0,[mx-(x1-x0)//6,my-(y1-y0)//3,mx+(x1-x0)//6,my-(y1-y0)//3,mx+(x1-x0)//6,my+(y1-y0)//3,mx-(x1-x0)//6,my+(y1-y0)//3]]]}
lv=json.loads(json.dumps(base));lv['id']='detailtest';lv['name']='Detail test';lv['detail']=[d];lv['pieces'][d]['detail']=art;lv['start']=start
ok["py_solves_with_detail"]=solve(lv['sol'],nb,K,start,detail=[d])==0 or simulate(lv['sol'],nb,K,start,detail=[d])[1]==0
ok["py_detail_not_in_start"]=d not in start
ok["py_no_neighbour_in_start"]=not set(start)&set(nb[d])
print("detail pane",d,"neighbours",len(nb[d]),"start",len(start),flush=True)
JS="""async([lv,reduced])=>{lv.clues=[];lv.n=12;lv.sol=[lv.sol];lv.loaded=true;lv.panes=lv.pieces.length;lv.nstart=lv.start.length;lv.ngift=0;lv.ndetail=lv.detail.length;LEVELS.push(lv);lv.fp=levelFP(lv);const i=LEVELS.length-1;load(i);AFN=0;await new Promise(r=>setTimeout(r,500));
 const dd=lv.detail[0],sl=ms=>new Promise(r=>setTimeout(r,ms)),out={};
 const g=()=>board.querySelector('.det[data-i="'+dd+'"]');
 out.rendered=!!g()&&g().querySelectorAll('path').length==2&&!!board.querySelector('#dc'+dd);
 out.unlit_before=!g().classList.contains('on')&&getComputedStyle(g()).opacity=='0'&&!REV.has(dd);
 out.clipped=g().getAttribute('clip-path')=='url(#dc'+dd+')';
 out.pal_hidden=[...document.querySelectorAll('#palette .sw')].length;
 out.neighbour_locked_at_start=L.nb[dd].some(q=>lock.has(q));
 // not clickable: pointer events pass through the picture, taps do nothing
 const r=g().getBoundingClientRect();const el=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);out.pointer_through=!el||!el.closest('.dt');
 let cr=cracks;sel=L.sol[0][dd];glowSet(0,dd,L.sol[0][dd]);glowSet(0,dd,(L.sol[0][dd]+1)%L.colors.length);await sl(700);out.tap_nothing=cracks==cr&&!lock.has(dd);
 out.pick_clean=sunbeamRaw(pcSolve()).every(z=>z!=dd);
 // reveal on neighbour fill
 let q=L.nb[dd].find(z=>!lock.has(z));
 if(q!==undefined){out.revealed_early=REV.has(dd);const wasOn=g().classList.contains('on');
  const f=sunbeamRaw(pcSolve());sel=L.sol[0][q];
  // lock the neighbour with its correct colour through the normal tap path
  glowSet(0,q,L.sol[0][q]);await sl(900);out.q_locked=lock.has(q);
  out.on_after=g().classList.contains('on')&&REV.has(dd)&&getComputedStyle(g()).opacity=='1';
  out.sparkle_seen=document.querySelectorAll('#fx .dsp').length;out.wasOn=wasOn;}
 else{out.revealed_early=false;out.on_after=REV.has(dd);out.q_locked=true;out.sparkle_seen=0;out.wasOn=true}
 await sl(1500);out.sparkle_gone=document.querySelectorAll('#fx .dsp').length==0;
 // save/load: reload the same level, reveal state comes back from the locked panes, silently
 const lockedBefore=lock.size;load(i);await sl(500);
 out.reload_on=REV.has(dd)&&g().classList.contains('on');out.reload_lock=lock.size==lockedBefore;out.reload_quiet=document.querySelectorAll('#fx .dsp').length==0;
 // play to the end without a single crack: flawless is unaffected, the detail pane is never input
 let guard=0;while(!won&&guard++<500){const s=sunbeamRaw(pcSolve());if(s.length)for(const z of s)glowSet(0,z,L.sol[0][z]);await sl(520)}
 await sl(1500);out.rv_win=document.querySelectorAll('#rvWin .rvdet path').length;out.rv_floor=document.querySelectorAll('#rvFloor .rvdet path').length;out.rv_clip=!!document.querySelector('#rvwc'+dd)&&!!document.querySelector('#rvfc'+dd);
 out.won=won;out.cracks=cracks;out.locked=lock.size;out.n=L.pieces.length;out.flawless=won&&cracks==0;out.detail_in_proj=!!document.querySelector('#proj clipPath');
 out.sub=document.querySelector('#lvsub')?document.querySelector('#lvsub').textContent:'';out.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 out.trans=getComputedStyle(g()).transitionDuration;return out}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox","--allow-file-access-from-files"])
    res={}
    for mode in ("no-preference","reduce"):
      c=b.new_context(**p.devices["iPhone 13"],reduced_motion=mode);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
      pg.goto("http://localhost:8802/index.html#preload&levels");pg.wait_for_timeout(300)
      pg.evaluate("localStorage.clear()")
      r=pg.evaluate(JS,[lv,mode]);res[mode]=r;print(mode,r,flush=True);c.close()
    b.close()
    for m,r in res.items():
      t=m+"_"
      ok[t+"renders_clipped_art"]=r['rendered'] and r['clipped']
      ok[t+"plain_glass_before_reveal"]=r['unlit_before']
      ok[t+"not_clickable"]=r['pointer_through'] and r['tap_nothing'] and r['pick_clean']
      ok[t+"reveals_on_neighbour_fill"]=not r['revealed_early'] and not r['neighbour_locked_at_start'] and r['q_locked'] and r['on_after']
      ok[t+"save_load_keeps_reveal_quietly"]=r['reload_on'] and r['reload_lock'] and r['reload_quiet']
      ok[t+"flawless_unaffected"]=r['won'] and r['cracks']==0 and r['flawless'] and r['locked']==r['n']-1
      ok[t+"counter_excludes_detail"]=r['sub'].startswith(str(r['n']-1)+' / '+str(r['n']-1))
      ok[t+"finished_window_and_floor_have_art"]=r['rv_win']>=2 and r['rv_floor']>=2 and r['rv_clip']
      ok[t+"floor_picture_has_art"]=r['detail_in_proj']
    ok["sparkle_with_motion"]=res['no-preference']['sparkle_seen']>0 and not res['no-preference']['wasOn']
    ok["reduced_motion_no_sparkle_plain_fade"]=res['reduce']['sparkle_seen']==0 and res['reduce']['reduced'] and res['reduce']['trans'] in('0.35s',)
    ok["sparkle_removed_after"]=res['no-preference']['sparkle_gone']
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
