"""Rosette tags on Reef, Beads and Quilt must not cover pane badges (collision on SVG boxes),
must stay reasonably compact, and must still show one colour dot per listed colour."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
SHOT=os.path.join("/workspace/puzzle-studio/fresh/rework")
os.makedirs(SHOT,exist_ok=True)
IDS=['fresh17','fresh14','fresh05']  # Reef, Beads, Quilt
srv=subprocess.Popen(["python3","-m","http.server","8842","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
JS="""()=>{
  const svg=board.querySelector('svg'),U=L.n*cs,W=U,H=U/ASP();
  const box=el=>{try{const b=el.getBBox();return {x:b.x,y:b.y,w:b.width,h:b.height}}catch(e){return null}};
  const hit=(a,b,pad)=>{return a&&b&&a.x<b.x+b.w+pad&&a.x+a.w+pad>b.x&&a.y<b.y+b.h+pad&&a.y+a.h+pad>b.y};
  const tags=[...document.querySelectorAll('.rtags .rtag')].map((e,i)=>({i,box:box(e),dots:e.querySelectorAll('circle').length,w:(box(e)||{}).w}));
  const badges=[...document.querySelectorAll('#badges .bdg, #badges .nbdg')].map(e=>box(e)).filter(Boolean);
  const overlaps=[];
  tags.forEach(t=>{if(!t.box)return;badges.forEach((b,bi)=>{if(hit(t.box,b,1.5))overlaps.push({tag:t.i,badge:bi,tw:t.box.w,th:t.box.h})})});
  return {nros:L.ros.length,ntags:tags.length,dots:tags.map(t=>t.dots),expect:(L.ros||[]).map(r=>r.cols.length),
    tw:tags.map(t=>t.w),W,overlaps,maxTagW:Math.max(0,...tags.map(t=>t.w||0)),nBadges:badges.length}
}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    c=b.new_context(**p.devices["iPhone SE"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.goto("http://localhost:8842/index.html#preload&levels");pg.wait_for_timeout(400)
    for lid in IDS:
      # tinted: the mode Haex was using on Reef
      pg.evaluate("()=>localStorage.setItem('lightglass.photomode','tinted')")
      name=pg.evaluate("id=>{const l=LEVELS.find(x=>x.id==id);load(LEVELS.findIndex(x=>x.id==id));return l&&l.name}",lid)
      pg.wait_for_timeout(900)
      pg.evaluate("()=>{hintEnd0&&hintEnd0();const m=document.querySelector('#mexp');if(m)m.classList.remove('on');document.querySelectorAll('.tipbar,.coach,#coach,#rules.on').forEach(e=>e.remove())}")
      r=pg.evaluate(JS)
      print(lid,name,r,flush=True)
      ok[f"{lid}_loaded"]=bool(name)
      ok[f"{lid}_one_tag_per_rosette"]=r['ntags']==r['nros'] and r['nros']>0
      ok[f"{lid}_dots_match_colours"]=r['dots']==r['expect']
      ok[f"{lid}_tag_does_not_cover_badges"]=r['overlaps']==[]
      ok[f"{lid}_tag_compact"]=r['maxTagW']>0 and r['maxTagW']<=0.28*r['W']+1
      if lid=='fresh17':
        pg.screenshot(path=os.path.join(SHOT,"fix_reef_rosettes_tinted.png"))
      elif lid=='fresh14':
        pg.screenshot(path=os.path.join(SHOT,"fix_beads_rosettes_tinted.png"))
      elif lid=='fresh05':
        pg.screenshot(path=os.path.join(SHOT,"fix_quilt_rosettes_tinted.png"))
    c.close();b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
if ERR: print("ERR",ERR)
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
