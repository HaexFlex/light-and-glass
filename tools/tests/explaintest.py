"""One-time explainers for the clue mechanics: the first level with 'is not' bubbles / thick lead lines (canes) / lead rings (rosettes) shows a tap-to-dismiss
card with a plain-English rule (bubbles: about the NEIGHBOURS, not the pane itself); shown once, not again after a reload (flags in lightglass.tutorial.v1.mech),
each mechanic explained in turn on a level with several; readable in both themes on iPhone SE portrait; the rules (?) panel lists all three. Saves docs/screenshots/explain_<theme>.png."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8826","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
def lum(c):
  import re;v=[int(x)/255 for x in re.findall(r'\d+',c)[:3]];v=[x/12.92 if x<=.03928 else ((x+.055)/1.055)**2.4 for x in v];return .2126*v[0]+.7152*v[1]+.0722*v[2]
ST="()=>{const e=document.querySelector('#mexp'),on=e.classList.contains('on'),d=e.firstElementChild,r=d.getBoundingClientRect(),cs=getComputedStyle(d);return {on,k:e.dataset.k||'',t:e.querySelector('.mxt').textContent,fg:cs.color,bg:cs.backgroundColor,box:[r.left,r.top,r.right,r.bottom],vw:innerWidth,vh:innerHeight}}"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for theme in ('dark','light'):
      c=b.new_context(**p.devices["iPhone SE"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)));T=theme+'_'
      pg.goto("http://localhost:8826/index.html#preload&levels");pg.wait_for_timeout(300)
      if (theme=='light')!=pg.evaluate("document.body.classList.contains('light')"): pg.evaluate("document.querySelector('#themeBtn').click()");pg.wait_for_timeout(200)
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}","seaturtle");pg.wait_for_timeout(1200)
      s=pg.evaluate(ST);print(theme,s)
      ok[T+'bubble_explainer_shown']=s['on'] and s['k']=='not'
      ok[T+'says_neighbours_not_pane']='touching this one' in s['t'] and 'nothing about the pane itself' in s['t']
      L1,L2=lum(s['fg']),lum(s['bg']);ok[T+'readable_contrast']=(max(L1,L2)+.05)/(min(L1,L2)+.05)>=7
      ok[T+'inside_screen']=s['box'][0]>=0 and s['box'][2]<=s['vw'] and s['box'][1]>=0 and s['box'][3]<=s['vh'] and s['vh']>s['vw']
      pg.screenshot(path=os.path.join(R,f'docs/screenshots/explain_{theme}.png'))
      pg.mouse.click(160,300);pg.wait_for_timeout(300);ok[T+'tap_dismisses']=not pg.evaluate(ST)['on']
      pg.reload();pg.wait_for_timeout(300);pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}","seaturtle");pg.wait_for_timeout(1200)
      ok[T+'not_again_after_reload']=not pg.evaluate(ST)['on']
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}","balloon");pg.wait_for_timeout(1200);ok[T+'not_on_other_bubble_level']=not pg.evaluate(ST)['on']
      pg.evaluate("id=>{load(LEVELS.findIndex(l=>l.id==id))}","lion");pg.wait_for_timeout(1200);seen=[]
      for _ in range(4):
        s=pg.evaluate(ST)
        if not s['on']: break
        seen.append(s['k']);pg.mouse.click(160,300);pg.wait_for_timeout(450)
      ok[T+'canes_then_rings_explained_once']=seen==['cane','ros']
      ok[T+'flags_saved']=pg.evaluate("JSON.parse(localStorage.getItem('lightglass.tutorial.v1.mech')||'{}')")=={'not':1,'cane':1,'ros':1}
      pg.evaluate("$('#help').click()");pg.wait_for_timeout(200);rt=pg.evaluate("document.querySelector('#rules').textContent")
      ok[T+'rules_list_all_three']=all(x in rt for x in ('Crossed-out dots','Thick lead line','Lead ring'))
      c.close()
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
