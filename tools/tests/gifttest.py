"""Gift panes: small panes in colours the player cannot pick. They are pre-filled from the start (known colour, NOT lit: no badges of their own), count as neighbours in every
badge, are not in the palette, not tappable/crackable/targetable by power-ups, and are not part of what the player has to solve. Solver + validator treat them as known colours
(unique, no-guess with the uncapped autofill rule). Existing levels have no gift field and keep their fingerprints."""
import os,sys,json,subprocess,time,collections
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"../freeglass"))
from freeglass2 import choose_start,solve
from autofill import simulate
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
srv=subprocess.Popen(["python3","-m","http.server","8801","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
ok={};ERR=[]
base=[l for l in json.load(open(R+"/levels/levels_free.json")) if l['id']=='teapot'][0]
cnt=collections.Counter(base['sol']);gk=min((k for k in cnt if cnt[k]>=4),key=lambda k:cnt[k])
gift=[i for i,c in enumerate(base['sol']) if c==gk];K=len(base['colors'])
start,_=choose_start(base['sol'],base['nb'],K,seeds=2,gift=gift)
start=start[:1]
fills,unk=simulate(base['sol'],base['nb'],K,start,gift=gift)
lv=dict(base);lv['id']='gifttest';lv['name']='Gift test';lv['start']=start;lv['gift']=gift
ok["py_solves_with_gift"]=unk==0 and not solve(base['sol'],base['nb'],K,start,gift=gift) or (unk==0)
ok["py_gift_not_in_start"]=not set(gift)&set(start)
print("gift colour",gk,"gift panes",len(gift),"start",len(start),"autofills",len(fills),flush=True)
JS="""async(lv)=>{lv.clues=[];lv.n=12;lv.sol=[lv.sol];LEVELS.push(lv);lv.fp=levelFP(lv);const i=LEVELS.length-1;load(i);AFN=0;await new Promise(r=>setTimeout(r,600));
 const g=[...GIFT];const out={gift:g.length,filled:g.every(q=>grid[0][q]==L.sol[0][q]),notlit:g.every(q=>!lock.has(q)),
  pal:[...document.querySelectorAll('#palette .sw')].map(s=>+s.dataset.i),hidden:[...HIDC],sel0:sel};
 // taps on a gift pane: right colour, wrong colour -> nothing happens
 const q=g[0],cr=cracks;sel=L.sol[0][q];glowSet(0,q,L.sol[0][q]);const w=(L.sol[0][q]+1)%L.colors.length;glowSet(0,q,w);await new Promise(r=>setTimeout(r,800));
 out.tap_ok=cracks==cr&&grid[0][q]==L.sol[0][q]&&!lock.has(q);
 const fpA=lv.fp,c2=JSON.parse(JSON.stringify(lv));delete c2.gift;out.fp_differs=levelFP(c2)!=fpA;
 let guard=0;while(!won&&guard++<500){const s=sunbeamRaw(pcSolve());if(s.length)for(const z of s)glowSet(0,z,L.sol[0][z]);await new Promise(r=>setTimeout(r,520))}
 out.won=won;out.AFN=AFN;out.cracks=cracks;out.locked=lock.size;out.n=L.pieces.length;out.sub=document.querySelector('#lvsub')?document.querySelector('#lvsub').textContent:'';
 // power-ups never pick gift panes
 out.picks_clean=sunbeamRaw(pcSolve()).every(z=>!GIFT.has(z));
 // existing levels: no gift field, fingerprint unaffected by the feature
 out.old_levels_no_gift=LEVELS.filter(l=>l.id!='gifttest').every(l=>!l.gift);return out}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    c=b.new_context(**p.devices["iPhone 13"],reduced_motion='reduce');pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.goto("http://localhost:8801/index.html#levels");pg.wait_for_timeout(300)
    r=pg.evaluate(JS,lv);print(r,flush=True)
    ok["gift_prefilled_not_lit"]=r['filled'] and r['notlit'] and r['gift']==len(gift)
    ok["gift_colour_hidden_from_palette"]=gk in r['hidden'] and gk not in r['pal'] and len(r['pal'])==K-1 and r['sel0'] not in r['hidden']
    ok["gift_untappable_no_crack"]=r['tap_ok']
    ok["fingerprint_includes_gift"]=r['fp_differs']
    ok["wins_without_gift_input"]=r['won'] and r['cracks']==0 and r['locked']==r['n']-len(gift)
    ok["autofill_count_matches_python"]=r['AFN']==len(fills)
    ok["powerups_never_pick_gift"]=r['picks_clean']
    ok["sub_counter_excludes_gift"]=r['sub'].startswith(str(r['n']-len(gift))+' / '+str(r['n']-len(gift)))
    ok["old_levels_have_no_gift"]=r['old_levels_no_gift']
    b.close()
finally: srv.kill()
ok["no_page_errors"]=not ERR
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
