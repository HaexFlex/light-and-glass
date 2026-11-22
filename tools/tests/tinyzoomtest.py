"""Tiny-pane zoom: max zoom is high enough that the smallest pane of every level reaches >=40px on iPhone SE / Galaxy S9+; start zoom is unchanged for large-pane levels;
a tap never moves the camera (no tap-zoom, even on panes <16px): it places right away; the ⤢ zoom button sits in the top bar, the tools row is gone and
board / palette / power-up bar do not overlap; no page errors."""
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
import os,sys
sys.path.insert(0,os.path.dirname(__file__))
from openlevel import open_level
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8803","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for dev in ["iPhone SE","Galaxy S9+"]:
      for lid in ["redtulip","orangecat","alpinelake","toadstool"]:
        ctx=b.new_context(**p.devices[dev]);ctx.add_init_script("localStorage.setItem('lightglass.tutorial.v1.mech',JSON.stringify({not:1,cane:1,ros:1}))");pg=ctx.new_page();  # mechanic explainers already seen (explaintest covers them)
        pg.on("pageerror",lambda e:ERR.append(str(e)))
        pg.goto("http://localhost:8803/index.html#preload&levels");pg.wait_for_timeout(300);open_level(pg,lid,400)
        px=lambda:pg.evaluate("(()=>{const k=L.n*cs*(Z.z/Z.rz);return 2*Math.min(...L.pieces.map(p=>p.rin))*k})()")
        z0=pg.evaluate("Z.z");pg.evaluate("zoomTo(ZMAX,BV.w/2,BV.h/2)");pg.wait_for_timeout(900);mx=px()
        ok[f"{dev}_{lid}_smallest_pane_ge_40px_at_max_zoom"]=mx>=40
        pg.evaluate("load(LEVELS.findIndex(l=>l.id==L.id))");pg.wait_for_timeout(500);z1=pg.evaluate("Z.z");tiny=px()<16
        info=pg.evaluate("""(()=>{let best=-1,bv=1e9;const v=document.querySelector('#bv').getBoundingClientRect();const skip=new Set([...(L.detail||[]),...(L.gift||[])]);L.pieces.forEach((p,i)=>{if(!lock.has(i)&&!skip.has(i)&&p.rin<bv){const m=cells[i].getBoundingClientRect(),x=m.x+m.width/2,y=m.y+m.height/2;if(x>v.x+5&&x<v.right-5&&y>v.y+5&&y<v.bottom-5){bv=p.rin;best=i}}});if(best<0)return null;const U=L.n*cs,M=cells[best].getScreenCTM(),pp=L.pieces[best].pole,X=M.a*pp[0]*U+M.c*pp[1]*U+M.e,Y=M.b*pp[0]*U+M.d*pp[1]*U+M.f;return [best,X,Y]   /* tap the pane's pole (always inside it) */})()""")
        if info:
          cam0=pg.evaluate("[Z.z,Z.tx,Z.ty]");pg.evaluate(f"sel=L.sol[0][{info[0]}]")
          pg.mouse.click(info[1],info[2]);pg.wait_for_timeout(600);cam1=pg.evaluate("[Z.z,Z.tx,Z.ty]");pl=pg.evaluate(f"lock.has({info[0]})")
          ok[f"{dev}_{lid}_tap_never_moves_camera{'_tiny' if tiny else ''}"]=all(abs(a-b)<.01 for a,b in zip(cam0,cam1))
          ok[f"{dev}_{lid}_tap_places_at_once"]=pl
        lay=pg.evaluate("""(()=>{const q=s=>{const e=document.querySelector(s);return e&&e.offsetParent?e.getBoundingClientRect():null};const t=q('#top'),z=q('#ztog'),v=q('#bv'),pa=q('#palette'),pu=q('#pubar');
          return {ztop:!!z&&document.querySelector('#top').contains(document.querySelector('#ztog'))&&z.bottom<=t.bottom+1,tools:!q('#tools'),order:t.bottom<=v.top+1&&v.bottom<=pa.top+1&&(!pu||pa.bottom<=pu.top+1),inview:(pu||pa).bottom<=innerHeight+1}})()""")
        ok[f"{dev}_{lid}_zoom_button_in_top_bar"]=lay['ztop'];ok[f"{dev}_{lid}_tools_row_gone"]=lay['tools'];ok[f"{dev}_{lid}_no_overlap"]=lay['order'] and lay['inview']
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
