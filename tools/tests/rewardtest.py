"""Random rewards: fixed-odds power-up rolls (same for every level), three claim slots per level (completion / <5 cracks / flawless gold leaf),
cap 5 with re-roll among non-capped types and a graceful 'full', saved rolls (reload cannot re-roll), and the kaleidoscope reveal
(confined to the reward card, tap to skip, reduced motion). Real touch taps on iPhone 13 and iPhone SE."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8795","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8795/index.html#levels";ok={};ERR=[]
KS=["lantern","cloth","sunbeam","colour","bolt","sunflare"];INV0={k:0 for k in KS}
solve="()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}"
def mk(b,p,dev,inv=None,rm=True,scheme="dark"):
  c=b.new_context(**p.devices[dev],color_scheme=scheme,reduced_motion='reduce' if rm else 'no-preference');pg=c.new_page()
  pg.on("pageerror",lambda e:ERR.append(str(e)));pg.on("dialog",lambda d:d.accept());pg.goto(U);pg.wait_for_timeout(250)
  if inv is not None:
    pg.evaluate("i=>localStorage.setItem('lightglass.powerups.v1',JSON.stringify({v:1,inv:i,claims:{},lv:{},hint:1,gold:0}))",dict(INV0,**inv));pg.reload();pg.wait_for_timeout(250)
  return c,pg
inv=lambda pg:pg.evaluate("PU.inv");gold=lambda pg:pg.evaluate("PU.gold")
def opn(pg,id): pg.locator(f'.card[data-id="{id}"]').tap();pg.wait_for_timeout(600)
def win(pg,cr=0,wait=1200):
  pg.evaluate(f"()=>{{cracks={cr}}}");pg.evaluate(solve);pg.wait_for_timeout(wait)
def S(pg,id): return pg.evaluate(f"PU.claims.{id}&&PU.claims.{id}.s")
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  # ---------- distribution + cap (pure roll function, many samples) ----------
  c,pg=mk(b,p,"iPhone 13")
  EXP={"lantern":.25,"cloth":.25,"sunbeam":.15,"colour":.12,"bolt":.15,"sunflare":.08}
  ok["odds_const"]=pg.evaluate("ODDS")=={k:round(v*100) for k,v in EXP.items()} and sum(pg.evaluate("Object.values(ODDS)"))==100
  r=pg.evaluate("()=>{const o={};for(let i=0;i<60000;i++){const k=rollPU(PU.inv);o[k]=(o[k]||0)+1}return o}")
  dist={k:round(r.get(k,0)/60000,3) for k in KS};ok["dist_matches_fixed_odds"]=all(abs(dist[k]-EXP[k])<.01 for k in KS);ok["dist_detail"]=dist
  # independent of section: the roll takes no level/tier input, and wins in every section draw from all six types
  ok["no_section_gating"]=pg.evaluate("rollPU.length")==2 and "tierOf" not in pg.evaluate("rollPU.toString()")
  capd=lambda ks:{k:(5 if k in ks else 0) for k in KS}
  r=pg.evaluate("inv=>{const o={};for(let i=0;i<20000;i++){const k=rollPU(inv);o[k]=(o[k]||0)+1}return o}",capd(["lantern","cloth"]))
  ok["cap_reroll_skips_capped"]="lantern" not in r and "cloth" not in r and sum(r.values())==20000 and abs(r["sunbeam"]/20000-.15/.5)<.015
  r=pg.evaluate("inv=>{const o={};for(let i=0;i<5000;i++){const k=rollPU(inv);o[k]=(o[k]||0)+1}return o}",capd([k for k in KS if k!="cloth"]))
  ok["cap_only_one_left"]=r=={"cloth":5000}
  ok["cap_all_full_null"]=pg.evaluate("inv=>rollPU(inv)",capd(KS)) is None
  c.close()
  for dev,tag in (("iPhone 13","13"),("iPhone SE","se")):
    K=lambda s:f"{tag}_{s}"
    # ---------- slots across replays ----------
    c,pg=mk(b,p,dev,{});g0=gold(pg)
    opn(pg,"firstlight");win(pg,5)
    ok[K("slot1_only_at_5_cracks")]=S(pg,"firstlight")==[1,0,0] and sum(inv(pg).values())==1 and gold(pg)-g0==1
    pg.screenshot(path=D+f"reward_slot1_{tag}.png")
    rw=pg.evaluate("RWD");ok[K("card_shows_one")]=rw["slots"]==[1] and sum(i["n"] for i in rw["items"])==1
    pg.locator('#replay').tap();pg.wait_for_timeout(600);g1=gold(pg);n1=sum(inv(pg).values());win(pg,4)
    ok[K("slot2_under_5_cracks")]=S(pg,"firstlight")==[1,1,0] and sum(inv(pg).values())-n1==1 and gold(pg)==g1
    pg.locator('#replay').tap();pg.wait_for_timeout(600);n2=sum(inv(pg).values());win(pg,0)
    ok[K("slot3_flawless_gold_only")]=S(pg,"firstlight")==[1,1,1] and sum(inv(pg).values())==n2 and gold(pg)-g1==1
    ok[K("slot3_card_text")]=pg.evaluate("RWD.slots")==[3] and "Flawless" in pg.locator('#rwCard').inner_text() and "+1 gold leaf" in pg.locator('#rwCard').inner_text()
    pg.screenshot(path=D+f"reward_slot3_{tag}.png")
    pg.locator('#replay').tap();pg.wait_for_timeout(600);st=(inv(pg),gold(pg));win(pg,0,800)
    ok[K("all_claimed_no_card")]=(inv(pg),gold(pg))==st and pg.evaluate("RWD")is None and not pg.evaluate("document.querySelector('#rwCard').classList.contains('has')")
    c.close()
    # flawless first win: all three slots at once (2 power-ups, 1 base + tier-1 bonus 1 gold)
    c,pg=mk(b,p,dev,{});g0=gold(pg);opn(pg,"firstlight");win(pg,0)
    ok[K("reward_card_tier_label")]="clear" in pg.locator('#rwCard em').inner_text().lower()
    ok[K("first_flawless_all_three")]=S(pg,"firstlight")==[1,1,1] and sum(inv(pg).values())==2 and gold(pg)-g0==2
    c.close()
    # ---------- full bar: graceful, slots stay open until there is room ----------
    c,pg=mk(b,p,dev,{k:5 for k in KS});opn(pg,"firstlight");win(pg,0)
    t=pg.locator('#rwCard').inner_text()
    ok[K("full_message")]="full" in t.lower() and pg.locator('#rwCard').is_visible() and all(v==5 for v in inv(pg).values())
    ok[K("full_slots_left_open")]=S(pg,"firstlight")==[0,0,1]
    pg.screenshot(path=D+f"reward_full_{tag}.png")
    pg.evaluate("()=>{PU.inv.lantern=0;puSave()}");pg.locator('#replay').tap();pg.wait_for_timeout(600);win(pg,2)
    ok[K("full_then_room_claims")]=S(pg,"firstlight")==[1,1,1] and inv(pg)["lantern"]==2
    c.close()
    # ---------- saved roll: reload cannot re-roll ----------
    c,pg=mk(b,p,dev,{});opn(pg,"firstlight");win(pg,0,300)
    snap=lambda:pg.evaluate("[JSON.stringify(PU.inv),PU.gold,JSON.stringify(PU.claims.firstlight)]")
    s0=snap();t0=pg.evaluate("RWD")
    ok[K("roll_persisted")]=json.loads(s0[2])["last"]["items"]==t0["items"]
    same=True;txt0=None
    for q in range(3):
      pg.reload();pg.wait_for_timeout(300);opn(pg,"firstlight");pg.wait_for_timeout(900)
      same&=snap()==s0 and pg.evaluate("RWD")["items"]==t0["items"] and pg.evaluate("RWD")["gold"]==t0["gold"]
    ok[K("reload_cannot_reroll")]=same
    pg.reload();pg.wait_for_timeout(300);opn(pg,"firstlight");pg.wait_for_timeout(900)
    ok[K("reload_card_same")]=pg.locator('#rwCard').is_visible() or pg.evaluate("document.querySelector('#rwCard').classList.contains('has')")
    c.close()
    # reload immediately after the win (before the card even shows)
    c,pg=mk(b,p,dev,{});opn(pg,"firstlight");win(pg,0,100);s0=snap();pg.reload();pg.wait_for_timeout(300);opn(pg,"firstlight");pg.wait_for_timeout(900)
    ok[K("reload_instant_cannot_reroll")]=snap()==s0
    c.close()
    # ---------- kaleidoscope: runs, confined to the card, tap skips ----------
    c,pg=mk(b,p,dev,{},rm=False);opn(pg,"firstlight");win(pg,0,200)
    pg.wait_for_timeout(4900)
    m=pg.evaluate("""()=>{const q=s=>{const e=document.querySelector(s);return e&&e.getBoundingClientRect()},c=q('#rwCard'),s=q('#rwCard .kalsvg'),f=q('#rvFloor'),w=q('#rvWin'),bar=q('#winBar');
      const x=(a,b)=>a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top;
      return{on:KAL.on,svg:!!s,inCard:s&&s.left>=c.left-1&&s.right<=c.right+1&&s.top>=c.top-1&&s.bottom<=c.bottom+1,hitFloor:x(c,f),hitWin:x(c,w),hitBar:x(c,bar),
       hidden:getComputedStyle(document.querySelector('#rwCard .ics')).opacity,shards:document.querySelectorAll('#rwCard .kalsvg polygon').length}}""")
    ok[K("kal_running")]=m["on"] and m["svg"] and m["shards"]>=20 and float(m["hidden"])<.2
    ok[K("kal_confined_never_over_floor")]=bool(m["inCard"]) and not m["hitFloor"] and not m["hitWin"] and not m["hitBar"]
    ok[K("kal_uses_level_colours")]=pg.evaluate("[...new Set([...document.querySelectorAll('#rwCard .kalsvg polygon')].map(e=>e.getAttribute('fill')))].every(c=>L.colors.includes(c))")
    pg.screenshot(path=D+f"reward_kal_mid_{tag}.png")
    bx=pg.locator('#rwCard').bounding_box();pg.touchscreen.tap(bx["x"]+bx["width"]/2,bx["y"]+bx["height"]/2);pg.wait_for_timeout(700)
    ok[K("kal_tap_skips")]=not pg.evaluate("KAL.on") and not pg.evaluate("!!document.querySelector('#rwCard .kalsvg')") and float(pg.evaluate("getComputedStyle(document.querySelector('#rwCard .ics')).opacity"))>.9
    ok[K("kal_skip_tap_not_navigation")]=not pg.locator('#coll').is_visible() and pg.evaluate("document.body.classList.contains('playing')")
    pg.screenshot(path=D+f"reward_kal_done_{tag}.png")
    pg.touchscreen.tap(bx["x"]+bx["width"]/2,bx["y"]+bx["height"]/2);pg.wait_for_timeout(500)
    ok[K("card_tap_opens_collection_after")]=pg.locator('#coll').is_visible()
    c.close()
    # runs to the end by itself, with the flare
    c,pg=mk(b,p,dev,{},rm=False);opn(pg,"firstlight");win(pg,0,200);pg.wait_for_timeout(6900)
    ok[K("kal_finishes_alone")]=not pg.evaluate("KAL.on") and float(pg.evaluate("getComputedStyle(document.querySelector('#rwCard .ics')).opacity"))>.9 and not pg.evaluate("!!document.querySelector('#rwCard .kalsvg')")
    c.close()
    # reduced motion: no animation at all, reward immediately visible
    c,pg=mk(b,p,dev,{},rm=True);opn(pg,"firstlight");win(pg,0,200);pg.wait_for_timeout(5300)
    ok[K("reduced_motion_no_kal")]=not pg.evaluate("KAL.on") and not pg.evaluate("!!document.querySelector('#rwCard .kalsvg')") and not pg.evaluate("document.querySelector('#rwCard').classList.contains('kal')") and pg.locator('#rwCard').is_visible()
    c.close()
    # leaving mid-animation cleans up
    c,pg=mk(b,p,dev,{},rm=False);opn(pg,"firstlight");win(pg,0,200);pg.wait_for_timeout(5000);pg.locator('#toMenu').tap();pg.wait_for_timeout(500)
    ok[K("kal_cleanup_on_leave")]=not pg.evaluate("KAL.on") and not pg.evaluate("!!document.querySelector('#rwCard .kalsvg')")
    c.close()
    # light theme reward screenshot
    c,pg=mk(b,p,dev,{},rm=False,scheme="light");opn(pg,"eveningstar");win(pg,0,200);pg.wait_for_timeout(5400);pg.screenshot(path=D+f"reward_kal_light_{tag}.png")
    pg.wait_for_timeout(1800);pg.screenshot(path=D+f"reward_done_light_{tag}.png");c.close()
  # flawless gold leaf bonus = the level's difficulty tier (1-4), stored per level in the level data
  TIERS={'firstlight':1,'eveningstar':1,'moonwater':1,'daisy':2,'butterfly':2,'cottage':2,'freeflower':3,'freekoi':3,'freeswan':3,'freefox':3,'alpinelake':4}
  c,pg=mk(b,p,"iPhone 13",{})
  ok["tier_field_per_level"]=(lambda d:{k:v for k,v in d.items() if k in TIERS})(pg.evaluate("Object.fromEntries(LEVELS.map(l=>[l.id,l.tier]))"))==TIERS
  for lid,tt in (("daisy",2),("freeflower",3),("alpinelake",4)):
    g0=pg.evaluate("PU.gold");pg.evaluate("i=>{load(LEVELS.findIndex(l=>l.id==i))}",lid);pg.wait_for_timeout(400);win(pg,0,600)
    ok[f"flawless_gold_equals_tier_{lid}"]=pg.evaluate("PU.gold")-g0==1+tt and pg.evaluate("RWD.gold")==1+tt and S(pg,lid)==[1,1,1]
  ok["tier_names_defined"]=pg.evaluate("TIERN")=={"1":"Clear","2":"Tinted","3":"Stained","4":"Jewel"}
  pg.evaluate("()=>menu()");pg.wait_for_timeout(200)
  ok["level_cards_show_tier_name"]=(lambda d:{k:v for k,v in d.items() if k in TIERS})(pg.evaluate("Object.fromEntries([...document.querySelectorAll('.card')].map(c=>[c.dataset.id,c.querySelector('.tn').textContent]))"))=={k:["","Clear","Tinted","Stained","Jewel"][v] for k,v in TIERS.items()}
  NL=pg.evaluate("LEVELS.length");ok["levels_total_30"]=NL==30
  ok["tier_distribution"]=pg.evaluate("[1,2,3,4].map(t=>LEVELS.filter(l=>l.tier==t).length)")==[8,8,8,6]
  ok["menu_sections_by_tier_then_size"]=pg.evaluate("""()=>{const o=[...document.querySelectorAll('#cards > *')];const heads=o.filter(e=>e.classList.contains('sect')).map(e=>e.textContent);
    let t=0,last=0,okk=true;o.forEach(e=>{if(e.classList.contains('sect'))return;const l=LEVELS.find(x=>x.id==e.dataset.id);if(l.tier<t)okk=false;if(l.tier!=t){t=l.tier;last=0}const n=l.pieces.length;if(n<last)okk=false;last=n});
    return okk&&heads.join()=='Clear,Tinted,Stained,Jewel'&&o.find(e=>!e.classList.contains('sect')).dataset.id=='firstlight'}""")
  ok["every_level_has_distinct_palette_symbols"]=pg.evaluate("LEVELS.every(l=>new Set(l.colors).size==l.colors.length&&l.colors.length>=2)")
  pg.screenshot(path=D+"tier_names_levels_13.png")
  c.close()
  ok["fps_unchanged"]=True
  c,pg=mk(b,p,"iPhone 13")
  FPS={'freeflower':'jblccv','freekoi':'1iousos','freeswan':'151d14k','freefox':'c7g8jk','alpinelake':'188ch1m','firstlight':'1gjm0e6','eveningstar':'1b83oik','moonwater':'1pmn45','daisy':'1ezt13d','butterfly':'zjw8nw','cottage':'1w76xto'}
  ok["fps_unchanged"]=(lambda d:{k:v for k,v in d.items() if k in FPS})(pg.evaluate("Object.fromEntries(LEVELS.map(l=>[l.id,l.fp]))"))==FPS
  # migration of the old once-per-level list
  pg.evaluate("()=>localStorage.setItem('lightglass.powerups.v1',JSON.stringify({v:1,inv:{lantern:1},rewarded:['daisy'],lv:{},hint:1,gold:3}))");pg.reload();pg.wait_for_timeout(250)
  ok["migrate_rewarded_to_slot1"]=pg.evaluate("PU.claims.daisy.s")==[1,0,0] and "rewarded" not in pg.evaluate("JSON.parse(localStorage.getItem('lightglass.powerups.v1'))") and pg.evaluate("PU.gold")==3
  c.close();ok["errors"]=ERR;b.close()
finally: srv.terminate()
bad=[k for k,v in ok.items() if v is False]
print(json.dumps(ok,indent=1));print("FAILED:",bad);raise SystemExit(1 if bad or ERR else 0)
