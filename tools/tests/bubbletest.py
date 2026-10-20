"""EVERY 'is not' bubble in ALL levels, checked against the GAME's own adjacency and solution (read from the running game, not from python):
 - no listed colour occurs on any neighbour in the game's adjacency (L.nb) -- the rule as the game's solver uses it;
 - the bubble never lists the pane's OWN colour (reads as 'this pane is not X' -- Sea Turtle bug, Haex 2026-10-20);
 - no listed colour occurs on any pane that VISIBLY touches it (corner / tiny contacts the game's nb leaves out, within 0.004);
 - the drawn dots match the data (same colours, same order) and the bubble is drawn fully inside the window (edge panes were clipped)."""
import os,sys,json,subprocess,time
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));sys.path.insert(0,os.path.join(R,'tools/freeglass'))
from add_not import touching
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(["python3","-m","http.server","8823","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[];bad=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"]);c=b.new_context(**p.devices["iPhone SE"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.goto("http://localhost:8823/index.html#preload&levels");pg.wait_for_timeout(400)
    ids=pg.evaluate("LEVELS.filter(l=>l.mode=='free').map(l=>l.id)");n=0
    for lid in ids:
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}",lid);pg.wait_for_timeout(250)
      g=pg.evaluate("""()=>{if(!NOT.size)return null;zoomTo(1,0,0);render&&0;const sv=document.querySelector('#badges').closest('svg'),vb=sv.viewBox.baseVal,U=L.n*cs,W=U,H=U/ASP();
        return {nb:L.nb,sol:L.sol[0],not:[...NOT.entries()],drawn:[...document.querySelectorAll('.nbdg')].map(e=>{const bb=e.getBBox();return [+e.dataset.not,[...e.querySelectorAll('circle')].map(c=>c.getAttribute('fill').toLowerCase()),[bb.x,bb.y,bb.x+bb.width,bb.y+bb.height]]}),cols:L.colors.map(c=>c.toLowerCase()),W,H}}""")
      if not g: continue
      lv=json.load(open(os.path.join(R,f'levels/data/{lid}.json')));T=touching(lv['pieces']);D={d[0]:d for d in g['drawn']}
      for pane,cs in g['not']:
        n+=1;sol=g['sol']
        if any(sol[q] in cs for q in g['nb'][pane]): bad.append((lid,pane,cs,'neighbour has listed colour'))
        if sol[pane] in cs: bad.append((lid,pane,cs,'own colour listed'))
        if any(sol[q] in cs for q in T[pane]): bad.append((lid,pane,cs,'visibly touching pane has listed colour'))
        if pane in D:
          d=D[pane]
          if d[1]!=[g['cols'][k] for k in cs]: bad.append((lid,pane,cs,'drawn dots differ',d[1]))
          x0,y0,x1,y1=d[2]
          if x0<-0.5 or y0<-0.5 or x1>g['W']+0.5 or y1>g['H']+0.5: bad.append((lid,pane,cs,'bubble outside window',[round(v,1) for v in d[2]],g['W'],g['H']))
        elif pane not in lv.get('start',[]): bad.append((lid,pane,cs,'bubble not drawn'))
    b.close()
finally: srv.kill()
for x in bad: print(x)
ok["bubbles_checked"]=n>=15;ok["every_bubble_true_for_game_adjacency_and_looks_right"]=not bad;ok["no_page_errors"]=not ERR
print(n,'bubbles');print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
