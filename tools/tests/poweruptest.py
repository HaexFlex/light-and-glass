"""Power-ups: real touch taps on iPhone 13 and iPhone SE. Layout (palette right under the window, bar at the very bottom), starters + one-time hint,
lantern, cloth, sunbeam (checked against an independent Python solver), colour hint, bolt, sunflare, flawless rules, once-per-level rewards,
cap 9, reward card vs floor picture, collection screen, save/fingerprint safety, and a soundness sweep of the solver over every level."""
import os,sys,json,subprocess,time,random
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
sys.path.insert(0,R+"/tools/freeglass")
from solver2 import line_poss
srv=subprocess.Popen(["python3","-m","http.server","8768","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8768/index.html";ok={}
FPS={'freeflower':'jblccv','freekoi':'1iousos','freeswan':'151d14k','freefox':'c7g8jk','alpinelake':'188ch1m','firstlight':'1gjm0e6','eveningstar':'1b83oik','moonwater':'1pmn45','daisy':'1ezt13d','butterfly':'zjw8nw','cottage':'1w76xto'}
SAVE_KEYS={'placed','cracks','z','tx','ty','fp','solved','flawless','t'}
INV0={"lantern":0,"cloth":0,"sunbeam":0,"colour":0,"bolt":0,"sunflare":0}
def mk(b,p,dev,inv=None,hint=1,scheme="dark"):
  c=b.new_context(**p.devices[dev],color_scheme=scheme);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)));pg.on("dialog",lambda d:d.accept())
  pg.goto(U);pg.wait_for_timeout(250)
  if inv is not None:
    pg.evaluate("([i,h])=>localStorage.setItem('lightglass.powerups.v1',JSON.stringify({v:1,inv:i,rewarded:[],lv:{},hint:h}))",[dict(INV0,**inv),hint]);pg.reload();pg.wait_for_timeout(250)
  return c,pg
def lvl(pg,id):
  pg.locator(f'.card[data-id="{id}"]').tap();pg.wait_for_timeout(500)
  pg.evaluate("()=>{Z.z=1;commit();centre();apply()}");pg.wait_for_timeout(100)
def pt(pg,i): return pg.evaluate(f"(()=>{{const P=L.pieces[{i}],m=cells[{i}].getScreenCTM(),u=L.n*cs;const q=new DOMPoint(P.pole[0]*u,P.pole[1]*u).matrixTransform(m);return[q.x,q.y]}})()")
def vis(pg,i):
  x,y=pt(pg,i); return pg.evaluate(f"(()=>{{const v=document.querySelector('#bv').getBoundingClientRect();return {x}>v.x+4&&{x}<v.right-4&&{y}>v.y+4&&{y}<v.bottom-4&&document.elementFromPoint({x},{y})===cells[{i}]}})()")
def tap(pg,i): x,y=pt(pg,i);pg.touchscreen.tap(x,y);pg.wait_for_timeout(120)
def front(pg): 
  lit=set(pg.evaluate("[...lock]"));nb=pg.evaluate("L.nb");return [j for j in range(len(nb)) if j not in lit and any(k in lit for k in nb[j]) and vis(pg,j)]
def dark_vis(pg,exclude=()):
  lit=set(pg.evaluate("[...lock].concat([...LAMPS])"));return [j for j in range(pg.evaluate("L.pieces.length")) if j not in lit and j not in exclude and vis(pg,j)]
def pu(pg,k): pg.locator(f'#pubar .pu[data-k="{k}"]').tap();pg.wait_for_timeout(150)
inv=lambda pg:pg.evaluate("PU.inv")
solve_all="()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}"
def place_real(pg):
  j=front(pg)[0];sol=pg.evaluate("L.sol[0]");pg.locator('.sw').nth(sol[j]).tap();tap(pg,j);return j
def oracle(pg):
  st=pg.evaluate("({lock:[...lock],lamps:[...LAMPS],nb:L.nb,sol:L.sol[0],K:L.colors.length})");K=st['K'];N=len(st['sol'])
  Dm=[set(range(K)) for _ in range(N)]
  for s in st['lock']:Dm[s]={st['sol'][s]}
  src=set(st['lock'])|set(st['lamps']);ch=True
  while ch:
    ch=False
    for p in src:
      cnt=[0]*K
      for q in st['nb'][p]:cnt[st['sol'][q]]+=1
      Pp=line_poss([Dm[q] for q in st['nb'][p]],cnt)
      for ii,q in enumerate(st['nb'][p]):
        if Pp[ii]!=Dm[q]:Dm[q]=Pp[ii];ch=True
  return Dm,st
ERR=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for dev,tag in (("iPhone 13","13"),("iPhone SE","se")):
    K=lambda s:f"{tag}_{s}"
    # ---------- T0 starters, one-time hint, layout ----------
    c,pg=mk(b,p,dev,inv=None);
    ok[K("starter_inv")]=inv(pg)=={"lantern":2,"cloth":1,"sunbeam":1,"colour":0,"bolt":0,"sunflare":0}
    ok[K("fps_identical")]=pg.evaluate("Object.fromEntries(LEVELS.map(l=>[l.id,l.fp]))")==FPS
    lvl(pg,"eveningstar");pg.wait_for_timeout(300)
    ok[K("hint_shown")]=pg.evaluate("document.querySelector('#puhint').classList.contains('on')&&/power-up/.test(document.querySelector('#puhintTxt').textContent)")
    ok[K("hint_no_spoiler")]=not any(w in pg.locator('#puhintTxt').inner_text().lower() for w in ("flip","upside","invert","upright"))
    pg.screenshot(path=D+f"pu_hud_hint_{tag}.png")
    pg.locator('#phX').tap();pg.wait_for_timeout(100)
    ok[K("hint_dismiss_persists")]=pg.evaluate("PU.hint==1&&JSON.parse(localStorage.getItem('lightglass.powerups.v1')).hint==1&&!document.querySelector('#puhint').classList.contains('on')")
    pg.reload();pg.wait_for_timeout(250);lvl(pg,"eveningstar");pg.wait_for_timeout(200)
    ok[K("hint_not_again")]=not pg.evaluate("document.querySelector('#puhint').classList.contains('on')")
    r=pg.evaluate("""()=>{const q=s=>document.querySelector(s).getBoundingClientRect(),bv=q('#bv'),pal=q('#palette'),bar=q('#pubar'),vs=['#palette','#tools','#hint','#msg'].map(s=>document.querySelector(s)).filter(e=>e.offsetParent).map(e=>e.getBoundingClientRect().bottom);
      return{gap:pal.top-bv.bottom,barTop:bar.top,palBottom:pal.bottom,barBottom:bar.bottom,maxAbove:Math.max(...vs),H:innerHeight,W:innerWidth,barL:bar.left,barR:bar.right,n:document.querySelectorAll('#pubar .pu').length,
        labels:[...document.querySelectorAll('#pubar .pu label')].map(e=>e.textContent),counts:[...document.querySelectorAll('#pubar .pu .n')].map(e=>+e.textContent),zero:[...document.querySelectorAll('#pubar .pu.zero')].length,
        tiny:[...document.querySelectorAll('#pubar .pu')].every(e=>e.getBoundingClientRect().width>=40)}}""")
    ok[K("palette_under_window")]=-1<=r['gap']<=30
    ok[K("bar_at_very_bottom")]=r['maxAbove']<=r['barTop']+1 and r['barBottom']<=r['H']+0.5 and r['H']-r['barBottom']<40
    ok[K("bar_fits_width")]=r['barL']>=0 and r['barR']<=r['W']+.5 and r['tiny']
    ok[K("bar_six")]=r['n']==6 and r['counts']==[2,1,1,0,0,0] and r['zero']==3
    pg.screenshot(path=D+f"pu_hud_{tag}_dark.png");c.close()
    c,pg=mk(b,p,dev,inv={"lantern":3,"cloth":2,"sunbeam":1,"colour":2,"bolt":1,"sunflare":1},scheme="light");lvl(pg,"daisy")
    pg.screenshot(path=D+f"pu_hud_{tag}_light.png");c.close()
    # ---------- T1 lantern ----------
    c,pg=mk(b,p,dev,inv={"lantern":3,"cloth":2});lvl(pg,"daisy")
    save0=pg.evaluate("localStorage.getItem('lightglass.save.v1')")
    pu(pg,"lantern");ok[K("lantern_mode")]=pg.evaluate("PUMODE=='lantern'")and pg.locator('#pucap').is_visible()and pg.locator('#pubar .pu.act').count()==1
    lit=set(pg.evaluate("[...lock]"));nbad=pg.locator('#badges g.bdg').count()
    j=[x for x in dark_vis(pg) if x not in lit][0];tap(pg,j);pg.wait_for_timeout(300)
    ok[K("lantern_lit")]=pg.evaluate(f"LAMPS.has({j})&&grid[0][{j}]==-1&&!lock.has({j})")
    ok[K("lantern_badges")]=pg.locator('#badges g.bdg').count()==nbad+1
    ok[K("lantern_spent")]=inv(pg)["lantern"]==2 and pg.evaluate("PUMODE===null")
    ok[K("lantern_keeps_flawless")]=pg.evaluate("!ASSIST&&cracks==0")
    pg.screenshot(path=D+f"pu_lantern_{tag}.png")
    pu(pg,"lantern");tap(pg,j);ok[K("lantern_lit_pane_not_spent")]=inv(pg)["lantern"]==2 and pg.evaluate("PUMODE=='lantern'")
    k0=pg.evaluate("[...lock][0]");tap(pg,k0) if vis(pg,k0) else 0
    ok[K("lantern_placed_pane_not_spent")]=inv(pg)["lantern"]==2
    pu(pg,"lantern");ok[K("lantern_cancel")]=pg.evaluate("PUMODE===null")
    pg.reload();pg.wait_for_timeout(250);lvl(pg,"daisy")
    ok[K("lantern_persist")]=pg.evaluate(f"LAMPS.has({j})")and pg.locator('#badges g.bdg').count()==nbad+1
    s=pg.evaluate("JSON.parse(localStorage.getItem('lightglass.save.v1')||'{}').levels||{}").get("daisy")
    ok[K("save_v1_format_same")]=s is None or set(s)<=SAVE_KEYS
    c.close()
    # ---------- T2 cloth ----------
    c,pg=mk(b,p,dev,inv={"cloth":2});lvl(pg,"daisy")
    pu(pg,"cloth");ok[K("cloth_none_to_clean")]=inv(pg)["cloth"]==2
    jj=front(pg)[0];sol=pg.evaluate("L.sol[0]");wrong=(sol[jj]+1)%pg.evaluate("L.colors.length")
    pg.locator('.sw').nth(wrong).tap();tap(pg,jj);pg.wait_for_timeout(250)
    ok[K("crack_made")]=pg.evaluate("cracks")==1 and 'crack' in pg.locator('#lvsub').inner_text()
    pu(pg,"cloth");pg.wait_for_timeout(200)
    ok[K("cloth_removes_one")]=pg.evaluate("cracks")==0 and inv(pg)["cloth"]==1 and 'crack' not in pg.locator('#lvsub').inner_text()
    ok[K("cloth_flawless_kept")]=pg.evaluate("!ASSIST")
    pg.evaluate(solve_all);pg.wait_for_timeout(500)
    sv=pg.evaluate("JSON.parse(localStorage.getItem('lightglass.save.v1')).levels.daisy")
    ok[K("cloth_win_flawless")]=sv["flawless"]==True and sv["solved"]==True
    c.close()
    # ---------- T3 sunbeam ----------
    c,pg=mk(b,p,dev,inv={"sunbeam":2});lvl(pg,"cottage")
    pu(pg,"sunbeam");pg.wait_for_timeout(150)
    done=0
    for _ in range(40):
      if pg.locator('.cell.sunb').count():break
      pg.evaluate("()=>{const f=[...L.pieces.keys()].filter(i=>!lock.has(i)&&L.nb[i].some(j=>lock.has(j)));if(f.length)glowSet(0,f[0],L.sol[0][f[0]])}");done+=1
      if done%2==0:
        pu(pg,"sunbeam")
    n=pg.locator('.cell.sunb').count();ok[K("sunbeam_highlights")]=1<=n<=3 and inv(pg)["sunbeam"]==1
    hs=pg.evaluate("[...document.querySelectorAll('.cell.sunb')].map(e=>+e.dataset.c)");Dm,st=oracle(pg)
    ok[K("sunbeam_oracle_agrees")]=all(len(Dm[h])==1 and list(Dm[h])[0]==st['sol'][h] and h not in st['lock'] for h in hs)
    ok[K("sunbeam_no_colour_given")]=all(pg.evaluate(f"grid[0][{h}]==-1") and pg.evaluate(f"!cells[{h}].classList.contains('f')") for h in hs)
    ok[K("sunbeam_keeps_flawless")]=pg.evaluate("!ASSIST&&cracks==0")
    pg.screenshot(path=D+f"pu_sunbeam_{tag}.png")
    # place one highlighted pane by real taps with the right colour
    h=hs[0];
    if vis(pg,h): pg.locator('.sw').nth(st['sol'][h]).tap();tap(pg,h);ok[K("sunbeam_pane_correct_by_tap")]=pg.evaluate(f"grid[0][{h}]=={st['sol'][h]}")and pg.evaluate("cracks")==0
    else: ok[K("sunbeam_pane_correct_by_tap")]="not visible"
    c.close()
    # ---------- T4 colour hint ----------
    c,pg=mk(b,p,dev,inv={"colour":2});lvl(pg,"daisy")
    pu(pg,"colour");ok[K("colour_mode")]=pg.evaluate("PUMODE=='colour'")
    k0=pg.evaluate("[...lock][0]")
    if vis(pg,k0): tap(pg,k0);ok[K("colour_placed_pane_not_spent")]=inv(pg)["colour"]==2
    j=[x for x in dark_vis(pg)][0];tap(pg,j);pg.wait_for_timeout(300)
    ok[K("colour_revealed_correct")]=pg.evaluate(f"grid[0][{j}]==L.sol[0][{j}]&&lock.has({j})")and inv(pg)["colour"]==1
    ok[K("colour_breaks_flawless")]=pg.evaluate("ASSIST")and pg.evaluate("JSON.parse(localStorage.getItem('lightglass.powerups.v1')).lv.daisy.assisted")==1
    pg.evaluate(solve_all);pg.wait_for_timeout(600)
    sv=pg.evaluate("JSON.parse(localStorage.getItem('lightglass.save.v1')).levels.daisy")
    ok[K("colour_win_not_flawless")]=sv["solved"]==True and not sv["flawless"] and 'flawless' not in pg.locator('#winTxt').inner_text()
    pg.wait_for_timeout(5500);rw=pg.evaluate("RWD")
    ok[K("assisted_no_bonus")]=rw is not None and sum(i["n"] for i in rw["items"])==1 and not rw["flaw"]
    c.close()
    # ---------- T5 bolt ----------
    c,pg=mk(b,p,dev,inv={"bolt":2});lvl(pg,"daisy")
    pu(pg,"bolt");ok[K("bolt_not_on_first_move")]=inv(pg)["bolt"]==2 and pg.evaluate("LAMPS.size")==0
    place_real(pg);pg.wait_for_timeout(200)
    pu(pg,"bolt");pg.wait_for_timeout(250)
    path=pg.evaluate("[...LAMPS]");nb=pg.evaluate("L.nb")
    ok[K("bolt_struck")]=len(path)>=3 and inv(pg)["bolt"]==1
    ok[K("bolt_path_connected")]=all(path[i+1] in nb[path[i]] for i in range(len(path)-1))
    ok[K("bolt_no_colours")]=all(pg.evaluate(f"grid[0][{i}]==-1&&!lock.has({i})") for i in path)
    ok[K("bolt_badges")]=pg.locator('#badges g.bdg').count()==pg.evaluate("lock.size")+len(path)
    ok[K("bolt_consistent")]=pg.evaluate("pcSolve([...LAMPS]).every((d,q)=>d&&(d>>L.sol[0][q]&1))")
    ok[K("bolt_fx")]=pg.locator('#fx .bolt').count()==1
    ok[K("bolt_breaks_flawless")]=pg.evaluate("ASSIST")
    pg.screenshot(path=D+f"pu_bolt_{tag}.png")
    Dm,st=oracle(pg);ok[K("bolt_oracle_consistent")]=all(st['sol'][q] in Dm[q] for q in range(len(Dm)))
    c.close()
    # ---------- T6 sunflare ----------
    c,pg=mk(b,p,dev,inv={"sunflare":2});lvl(pg,"freeflower")
    pu(pg,"sunflare");ok[K("sunflare_mode")]=pg.evaluate("PUMODE=='sunflare'")
    j=dark_vis(pg)[0];tap(pg,j);ok[K("sunflare_window_tap_ignored")]=inv(pg)["sunflare"]==2 and pg.evaluate("PUMODE=='sunflare'")
    kk=pg.evaluate("(()=>{const c={};L.sol[0].forEach((k,i)=>{if(!lock.has(i))c[k]=(c[k]||0)+1});return +Object.keys(c).sort((a,b)=>c[b]-c[a])[0]})()")
    before=set(pg.evaluate("[...lock]"));pg.screenshot(path=D+f"pu_sunflare_pick_{tag}.png")
    pg.locator('.sw').nth(kk).tap();pg.wait_for_timeout(300)
    after=set(pg.evaluate("[...lock]"));new=sorted(after-before);nb=pg.evaluate("L.nb");sol=pg.evaluate("L.sol[0]")
    ok[K("sunflare_filled")]=2<=len(new)<=4 and inv(pg)["sunflare"]==1
    ok[K("sunflare_right_colour")]=all(sol[i]==kk and pg.evaluate(f"grid[0][{i}]")==kk for i in new)
    ok[K("sunflare_non_touching")]=all(j not in nb[i] for i in new for j in new)
    ok[K("sunflare_no_wrong_anywhere")]=pg.evaluate("grid[0].every((v,i)=>v<0||v==L.sol[0][i])")and pg.evaluate("cracks")==0
    ok[K("sunflare_breaks_flawless")]=pg.evaluate("ASSIST")
    ok[K("sunflare_mode_ended")]=pg.evaluate("PUMODE===null")
    pg.screenshot(path=D+f"pu_sunflare_{tag}.png");c.close()
    # ---------- T7 rewards, replay farming, cap, card vs floor picture ----------
    c,pg=mk(b,p,dev,inv=None,hint=1)
    pg.evaluate("()=>{const d=JSON.parse(localStorage.getItem('lightglass.powerups.v1'));d.hint=1;localStorage.setItem('lightglass.powerups.v1',JSON.stringify(d))}");pg.reload();pg.wait_for_timeout(250)
    i0=inv(pg);lvl(pg,"firstlight");pg.evaluate(solve_all);pg.wait_for_timeout(6500)
    i1=inv(pg);ok[K("reward_beginner_flawless_bonus")]=sum(i1.values())-sum(i0.values())==2 and all(i1[k]==i0[k] for k in ("sunbeam","colour","bolt","sunflare"))
    ok[K("reward_card_visible")]=pg.locator('#rwCard').is_visible()
    g=pg.evaluate("""()=>{const q=s=>document.querySelector(s).getBoundingClientRect(),c=q('#rwCard'),f=q('#rvFloor'),w=q('#winBar'),win=q('#rvWin');
      const x=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;return{card:[c.top,c.bottom,c.left,c.right],floor:[f.top,f.bottom],hitFloor:x(c,f),hitWin:x(c,win),hitBar:x(c,w),inside:c.left>=0&&c.right<=innerWidth&&c.bottom<=innerHeight,floorInside:f.left>=0&&f.right<=innerWidth}}""")
    ok[K("reward_card_not_over_floor")]=not g["hitFloor"] and not g["hitWin"] and not g["hitBar"] and g["inside"]
    pg.screenshot(path=D+f"pu_reward_{tag}.png")
    st=pg.evaluate("PU.rewarded");ok[K("rewarded_recorded")]=st==["firstlight"]
    pg.locator('#replay').tap();pg.wait_for_timeout(600);pg.evaluate(solve_all);pg.wait_for_timeout(6500)
    ok[K("replay_no_farming")]=inv(pg)==i1 and pg.evaluate("PU.rewarded")==["firstlight"] and not pg.evaluate("document.querySelector('#rwCard').classList.contains('has')")
    pg.locator('#toMenu').tap();pg.wait_for_timeout(300)
    # gardens, with one crack -> no bonus, tier kinds only
    i2=inv(pg);lvl(pg,"daisy")
    jj=front(pg)[0];sol=pg.evaluate("L.sol[0]");pg.locator('.sw').nth((sol[jj]+1)%pg.evaluate("L.colors.length")).tap();tap(pg,jj);pg.wait_for_timeout(200)
    pg.evaluate(solve_all);pg.wait_for_timeout(6500);i3=inv(pg)
    d=[k for k in i3 if i3[k]!=i2[k]];ok[K("reward_gardens_no_bonus")]=sum(i3.values())-sum(i2.values())==1 and set(d)<={"sunbeam","colour","bolt"}
    pg.locator('#toMenu').tap();pg.wait_for_timeout(300)
    lvl(pg,"freeflower");pg.evaluate(solve_all);pg.wait_for_timeout(6500);i4=inv(pg)
    ok[K("reward_showpiece_sunflare")]=i4["sunflare"]-i3["sunflare"]==2 and sum(i4.values())-sum(i3.values())==2
    pg.screenshot(path=D+f"pu_reward_rare_{tag}.png")
    ok[K("fps_after")]=pg.evaluate("Object.fromEntries(LEVELS.map(l=>[l.id,l.fp]))")==FPS
    ok[K("save_v1_keys")]=pg.evaluate("Object.values(JSON.parse(localStorage.getItem('lightglass.save.v1')).levels).every(s=>Object.keys(s).every(k=>['placed','cracks','z','tx','ty','fp','solved','flawless','t'].includes(k)))")
    # collection from the reward card
    pg.locator("#rwCard").tap();pg.wait_for_timeout(400)
    ok[K("collection_from_card")]=pg.locator('#coll').is_visible() and pg.evaluate("!document.body.classList.contains('playing')")
    ok[K("collection_counts")]=pg.evaluate("[...document.querySelectorAll('#collBody .crow .n')].map(e=>+e.textContent)")==[inv(pg)[k] for k in ("lantern","cloth","sunbeam","colour","bolt","sunflare")]
    pg.screenshot(path=D+f"pu_collection_{tag}.png")
    pg.locator('#collTabs button[data-tab="windows"]').tap();pg.wait_for_timeout(150)
    ok[K("collection_windows_tab")]=pg.evaluate("document.querySelectorAll('#collBody .crow').length")==11 and 'flawless' in pg.locator('#collBody').inner_text()
    pg.locator('#collBack').tap();pg.locator('#collBtn').tap();ok[K("collection_from_menu")]=pg.locator('#coll').is_visible();pg.locator('#collBack').tap()
    c.close()
    # cap 9
    c,pg=mk(b,p,dev,inv={"lantern":9,"cloth":9});lvl(pg,"firstlight");pg.evaluate(solve_all);pg.wait_for_timeout(6500)
    ok[K("cap_nine")]=inv(pg)["lantern"]==9 and inv(pg)["cloth"]==9 and 'full' in pg.locator('#rwCard').inner_text()
    c.close()
    # themes (light) reward screenshot
    c,pg=mk(b,p,dev,inv={"lantern":1},scheme="light");lvl(pg,"eveningstar");pg.evaluate(solve_all);pg.wait_for_timeout(6500);pg.screenshot(path=D+f"pu_reward_light_{tag}.png");c.close()
  # ---------- soundness sweep over every level (page-level, once) ----------
  c,pg=mk(b,p,"iPhone 13",inv={"lantern":1})
  res=pg.evaluate("""()=>{const out={};for(let li=0;li<LEVELS.length;li++){load(li);let bad=0,n=0,raw=0;
    for(let rep=0;rep<6;rep++){load(li);const N=L.pieces.length,order=[...Array(N).keys()].sort(()=>Math.random()-.5),take=Math.floor(N*(.1+.8*Math.random()));
      // grow a connected region from the start panes by random frontier picks, plus random lantern panes
      const seen=new Set(L.start);while(seen.size<take+L.start.length&&seen.size<N){const f=[...seen].flatMap(i=>L.nb[i]).filter(j=>!seen.has(j));if(!f.length)break;seen.add(f[Math.random()*f.length|0])}
      seen.forEach(i=>{if(!lock.has(i)){grid[0][i]=L.sol[0][i];lock.add(i)}});
      LAMPS=new Set();for(let k=0;k<4;k++){const i=order[k];if(!lock.has(i))LAMPS.add(i)}
      const D=pcSolve(),r=sunbeamRaw(D);raw+=r.length;r.forEach(i=>{n++;if(D[i]!=1<<L.sol[0][i])bad++});
      for(let i=0;i<N;i++)if(!(D[i]>>L.sol[0][i]&1))bad++; // the true colour must always stay possible
      if(sunbeamPicks().length!=r.length)bad++}
    out[L.id]={bad,raw}}return out}""")
  ok["sweep_never_wrong"]=all(v["bad"]==0 for v in res.values());ok["sweep_found_picks"]=sum(v["raw"] for v in res.values())>0
  ok["sweep_detail"]=res;c.close()
  ok["errors"]=ERR;b.close()
finally: srv.terminate()
bad=[k for k,v in ok.items() if v is False]
print(json.dumps(ok,indent=1));print("FAILED:",bad);raise SystemExit(1 if bad or ERR else 0)
