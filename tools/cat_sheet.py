"""Render a candidate level file in the game (injected, not in the manifest), play it to the end, screenshot the finished screen + a zoomed face crop. usage: cat_sheet.py level.json outdir"""
import sys,os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),".."));lv=json.load(open(sys.argv[1]));out=sys.argv[2];os.makedirs(out,exist_ok=True)
srv=subprocess.Popen(["python3","-m","http.server","8803","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
JS="""async(lv)=>{lv.clues=[];lv.n=12;lv.sol=[lv.sol];lv.loaded=true;lv.panes=lv.pieces.length;lv.nstart=lv.start.length;lv.ngift=(lv.gift||[]).length;lv.ndetail=(lv.detail||[]).length;LEVELS.push(lv);lv.fp=levelFP(lv);const i=LEVELS.length-1;load(i);AFN=0;await new Promise(r=>setTimeout(r,800));
 const sl=ms=>new Promise(r=>setTimeout(r,ms));let guard=0;while(!won&&guard++<900){const s=sunbeamRaw(pcSolve());if(s.length)for(const z of s)glowSet(0,z,L.sol[0][z]);await sl(60)}
 return {won,cracks,AFN,locked:lock.size,n:L.pieces.length,rev:[...REV]}}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    c=b.new_context(**p.devices['iPhone 13']);pg=c.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto("http://localhost:8803/index.html#preload&levels");pg.wait_for_timeout(400)
    pg.screenshot(path=out+'/dummy.png')
    # mid-game shot: before the end, to show unrevealed detail panes
    r=pg.evaluate(JS,lv);print(r,errs,flush=True)
    pg.evaluate("document.querySelector('.cell').ownerSVGElement.id='winsvg'");pg.wait_for_timeout(6000);pg.screenshot(path=out+'/finished.png')
    bb=pg.evaluate("(()=>{const r=document.querySelector('#winsvg').getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()");print(bb)
    json.dump(bb,open(out+'/bb.json','w'))
    # window only + face crop at high resolution (re-render the same finished page at larger scale)
    OV="""([w,flip])=>{const s=document.querySelector('.cell').ownerSVGElement,d=document.createElement('div');d.style.cssText='position:fixed;left:0;top:0;width:100vw;height:100vh;z-index:99999;background:#1b1512;display:flex;align-items:center;justify-content:center';
      const c=s.cloneNode(true);c.removeAttribute('id');c.style.cssText='width:'+w+'px;height:auto;max-width:none;max-height:none;position:static;transform:'+(flip?'scaleY(-1)':'none')+';display:block';c.querySelectorAll('#badges,#fx,.cr,.ct').forEach(e=>e.remove());d.appendChild(c);document.body.appendChild(d);return 1}"""
    pg.evaluate(OV,[360,1]);pg.screenshot(path=out+'/window.png')
    c2=b.new_context(viewport={'width':1500,'height':1100},device_scale_factor=2);pg2=c2.new_page();pg2.goto("http://localhost:8803/index.html#preload&levels");pg2.wait_for_timeout(400)
    pg2.evaluate(JS,lv);pg2.wait_for_timeout(5000);pg2.evaluate(OV,[1400,1]);pg2.screenshot(path=out+'/board_hi.png')
    from PIL import Image
    fx0,fy0,fx1,fy1=[float(v) for v in os.environ.get('FACE','0.60,0.34,0.86,0.60').split(',')]
    im=Image.open(out+'/board_hi.png');W,H=im.size;BW=2800;BH=int(BW/lv['aspect']);bx0=(W-BW)//2;by0=(H-BH)//2
    im.crop((bx0,by0,bx0+BW,by0+BH)).save(out+'/board_hi.png')
    im.crop((int(bx0+BW*fx0),int(by0+BH*fy0),int(bx0+BW*fx1),int(by0+BH*fy1))).save(out+'/face.png')
    b.close()
finally: srv.kill()
