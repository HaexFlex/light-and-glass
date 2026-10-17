"""Finished screen of a candidate level on iPhone 13 (injected, not in the manifest) + face crops of window and floor. usage: cat_finish_shots.py repo_dir level.json outdir [port]"""
import sys,os,json,subprocess,time
from playwright.sync_api import sync_playwright
from PIL import Image
repo,lvf,out=sys.argv[1:4];port=sys.argv[4] if len(sys.argv)>4 else '8805';lv=json.load(open(lvf));os.makedirs(out,exist_ok=True)
srv=subprocess.Popen(["python3","-m","http.server",port,"-d",repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
JS="""async(lv)=>{lv.clues=[];lv.n=12;lv.sol=[lv.sol];lv.loaded=true;lv.panes=lv.pieces.length;lv.nstart=lv.start.length;lv.ngift=(lv.gift||[]).length;lv.ndetail=(lv.detail||[]).length;LEVELS.push(lv);lv.fp=levelFP(lv);const i=LEVELS.length-1;load(i);AFN=0;await new Promise(r=>setTimeout(r,800));
 const sl=ms=>new Promise(r=>setTimeout(r,ms));let guard=0;while(!won&&guard++<900){const s=sunbeamRaw(pcSolve());if(s.length)for(const z of s)glowSet(0,z,L.sol[0][z]);await sl(60)}
 return {won,cracks,AFN}}"""
fx0,fy0,fx1,fy1=0.60,0.34,0.86,0.60;D=3
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    c=b.new_context(**{**p.devices['iPhone 13'],'device_scale_factor':D});pg=c.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(f"http://localhost:{port}/index.html#preload&levels");pg.wait_for_timeout(400)
    print(pg.evaluate(JS,lv),errs,flush=True);pg.wait_for_timeout(7000)
    R=pg.evaluate("revealLayout()");pg.screenshot(path=out+'/finished.png');json.dump(R,open(out+'/R.json','w'));print(R)
    im=Image.open(out+'/finished.png');A=lv['aspect']
    def crop(x,y,w,h,flipy,name):
      cr=im.crop((int(D*(x+w*fx0)),int(D*(y+h*(1-fy1 if flipy else fy0))),int(D*(x+w*fx1)),int(D*(y+h*(1-fy0 if flipy else fy1)))))
      if flipy: cr=cr.transpose(Image.FLIP_TOP_BOTTOM)
      cr.save(out+'/'+name)
    crop(R['wx'],R['wy'],R['ws'],R['wh'],True,'face_window.png'); crop(R['fx'],R['fy'],R['fs'],R['fh'],False,'face_floor.png')
    b.close()
finally: srv.kill()
