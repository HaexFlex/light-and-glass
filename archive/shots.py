from playwright.sync_api import sync_playwright
U="file:///workspace/puzzle-studio/light-glass/index.html"
D="/workspace/puzzle-studio/light-glass/"
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
  def page(h):
    ctx=b.new_context(**{**p.devices["iPhone 13"],"device_scale_factor":2});pg=ctx.new_page();pg.goto(U+h);pg.wait_for_timeout(600);return pg
  pg=page("");pg.screenshot(path=D+"shot_menu.png")
  for name,l in (("rose",1),("balloon",2),("swan",3)):
    pg=page(f"#lvl={l}");pg.screenshot(path=D+f"shot_{name}_start.png")
    if name=="swan":
      # mid-play: fill ~45% of panes (bottom part of window) with correct glass, plus one wrong pane, then Check
      pg.evaluate("(()=>{for(let r=0;r<L.n;r++)for(let c=0;c<L.n;c++)if(r<7&&(r*5+c*3)%4!=0)grid[r][c]=L.sol[r][c];grid[7][3]=(L.sol[7][3]+1)%5;sel=3;render()})()")
      pg.locator('#check').tap();pg.wait_for_timeout(500);pg.screenshot(path=D+"shot_swan_mid.png")
    pg=page(f"#lvl={l}&solve&instant");pg.wait_for_timeout(800);pg.screenshot(path=D+f"shot_{name}_win.png")
