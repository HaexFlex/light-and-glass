"""Gold leaf shop (Collection > Power-ups): gold leaf is the currency (common 2, medium 4, rare 8; cap 5 each). Buy, cap block, insufficient panes,
persistence, balance + counter, earning gold leaf on a win. Real touch taps on iPhone 13 and SE."""
import os,json,subprocess,time
from playwright.sync_api import sync_playwright
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));D=R+"/docs/screenshots/"
srv=subprocess.Popen(["python3","-m","http.server","8769","-d",R],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U="http://localhost:8769/index.html";ok={};ERR=[]
INV0={"lantern":0,"cloth":0,"sunbeam":0,"colour":0,"bolt":0,"sunflare":0}
def mk(b,p,dev,inv,panes):
  c=b.new_context(**p.devices[dev]);pg=c.new_page();pg.on("pageerror",lambda e:ERR.append(str(e)));pg.goto(U);pg.wait_for_timeout(250)
  pg.evaluate("([i,n])=>localStorage.setItem('lightglass.powerups.v1',JSON.stringify({v:1,inv:i,rewarded:[],lv:{},hint:1,gold:n}))",[dict(INV0,**inv),panes]);pg.reload();pg.wait_for_timeout(250);return c,pg
def stored(pg): return pg.evaluate("JSON.parse(localStorage.getItem('lightglass.powerups.v1'))")
def buy(pg,k): pg.locator(f'.buy[data-k="{k}"]').scroll_into_view_if_needed();pg.locator(f'.buy[data-k="{k}"]').tap(force=True,timeout=3000);pg.wait_for_timeout(150)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for dev,tag in (("iPhone 13","13"),("iPhone SE","se")):
    K=lambda s:f"{tag}_{s}"
    c,pg=mk(b,p,dev,{"cloth":5,"sunbeam":4},10)
    ok[K("menu_counter")]="⚜ 10" in pg.locator('#collBtn').inner_text()
    pg.locator('#collBtn').tap();pg.wait_for_timeout(200)
    ok[K("balance_shown")]=pg.locator('#bal').inner_text().replace("\n"," ").startswith("⚜ 10")
    ok[K("prices")]=pg.evaluate("[...document.querySelectorAll('.buy')].map(b=>b.textContent)")==["Buy · 2 ⚜","Full","Buy · 4 ⚜","Buy · 4 ⚜","Buy · 4 ⚜","Buy · 8 ⚜"]
    pg.screenshot(path=D+f"shop_collection_{tag}.png")
    buy(pg,"lantern");s=stored(pg);ok[K("buy_common")]=s["inv"]["lantern"]==1 and s["gold"]==8
    buy(pg,"colour");s=stored(pg);ok[K("buy_medium")]=s["inv"]["colour"]==1 and s["gold"]==4
    buy(pg,"cloth");s=stored(pg);ok[K("cap_block_button_disabled")]=pg.locator('.buy[data-k="cloth"]').is_disabled() and s["inv"]["cloth"]==5 and s["gold"]==4
    ok[K("cap_block_logic")]=pg.evaluate("puBuy('cloth')")==False and stored(pg)["gold"]==4
    buy(pg,"sunbeam");s=stored(pg);ok[K("buy_to_cap")]=s["inv"]["sunbeam"]==5 and s["gold"]==0
    ok[K("insufficient_disabled")]=pg.locator('.buy[data-k="sunflare"]').is_disabled() and "Need 8" in pg.locator('.buy[data-k="sunflare"]').inner_text()
    ok[K("insufficient_logic")]=pg.evaluate("puBuy('sunflare')")==False and pg.evaluate("puBuy('bolt')")==False and stored(pg)["inv"]["sunflare"]==0
    ok[K("balance_updates")]=pg.locator('#bal').inner_text().replace("\n"," ").startswith("⚜ 0")
    pg.screenshot(path=D+f"shop_after_{tag}.png")
    pg.reload();pg.wait_for_timeout(250)
    ok[K("persist")]=pg.evaluate("[PU.gold,PU.inv.lantern,PU.inv.colour,PU.inv.sunbeam,PU.inv.cloth]")==[0,1,1,5,5]
    ok[K("save_v1_untouched")]=pg.evaluate("localStorage.getItem('lightglass.save.v1')===null||Object.values(JSON.parse(localStorage.getItem('lightglass.save.v1')).levels).every(s=>!('panes' in s))")
    # in-level counter + bought item usable
    pg.locator('.card[data-id="daisy"]').tap();pg.wait_for_timeout(500)
    ok[K("hud_counter")]=pg.locator('#pcount').inner_text()=="⚜ 0" and pg.locator('#pcount').is_visible()
    pg.locator('#pubar .pu[data-k="lantern"]').tap();ok[K("bought_usable")]=pg.evaluate("PUMODE")=="lantern"
    c.close()
    # earning: first win of a level pays panes once
    c,pg=mk(b,p,dev,{},0);pg.on("dialog",lambda d:d.accept())
    pg.locator('.card[data-id="firstlight"]').tap();pg.wait_for_timeout(500)
    pg.evaluate("()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}");pg.wait_for_timeout(6000)
    n=pg.evaluate("Math.ceil(L.pieces.length/10)+2");ok[K("earn_flawless")]=stored(pg)["gold"]==n and pg.evaluate("n=>curN(n)",n) in pg.locator('#rwCard').inner_text()
    pg.locator('#replay').tap();pg.wait_for_timeout(500);pg.evaluate("()=>{L.pieces.forEach((_,i)=>{if(!lock.has(i))glowSet(0,i,L.sol[0][i])})}");pg.wait_for_timeout(6000)
    ok[K("earn_once_only")]=stored(pg)["gold"]==n
    c.close()
    # fresh player gets starter panes
    c=b.new_context(**p.devices[dev]);pg=c.new_page();pg.goto(U);pg.wait_for_timeout(250);ok[K("starter_panes")]=stored(pg)["gold"]==4;c.close()
  # legacy key migration (panes -> gold) and no "pane" wording for the currency anywhere in the shop UI
  c=b.new_context(**p.devices["iPhone 13"]);pg=c.new_page();pg.goto(U);pg.wait_for_timeout(200)
  pg.evaluate("()=>localStorage.setItem('lightglass.powerups.v1',JSON.stringify({v:1,inv:{},rewarded:[],lv:{},hint:1,panes:7}))");pg.reload();pg.wait_for_timeout(200)
  ok["migrate_panes_to_gold"]=pg.evaluate("PU.gold")==7 and "gold" in stored(pg) and "panes" not in stored(pg)
  pg.locator('#collBtn').tap();pg.wait_for_timeout(200)
  txt=(pg.locator('#bal').inner_text()+" "+" ".join(pg.evaluate("[...document.querySelectorAll('.buy')].map(b=>b.textContent)"))).lower()
  ok["no_pane_word_for_currency"]="pane" not in txt and "gold leaf" in txt and pg.evaluate("CUR.name")=="gold leaf"
  ok["menu_no_pane_word"]="pane" not in pg.locator('#collBtn').inner_text().lower()
  c.close()
  ok["errors"]=ERR;b.close()
finally: srv.terminate()
bad=[k for k,v in ok.items() if v is False]
print(json.dumps(ok,indent=1));print("FAILED:",bad);raise SystemExit(1 if bad or ERR else 0)
