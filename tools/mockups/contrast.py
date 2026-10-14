"""Contrast mockups on the real Autumn Fox board (default zoom): A = light lead on dark glass, B = milky unlit glass, dark lead."""
import os
from playwright.sync_api import sync_playwright
H=os.path.dirname(os.path.abspath(__file__));R=os.path.abspath(H+"/../..");OUT=R+"/docs/mockups/"
CSS={"A":"""
.cell{stroke:#e4cf98;stroke-width:2.2!important}
.cell:not(.f){fill:#16141a}
#board svg>g:first-of-type{filter:drop-shadow(0 0 1.6px #f5dc9a99)}
#board{background:#0b0a0b}
""","B":"""
.cell{stroke:#1d1612;stroke-width:3!important}
.cell:not(.f){fill:url(#milk)}
#board{background:#1d1612}
.cell.f{filter:drop-shadow(0 0 4px var(--c)) brightness(1.05)}
"""}
DEFS="""()=>{const s=board.querySelector('svg defs');s.insertAdjacentHTML('beforeend',`
<filter id="frost" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 .55  0 0 0 0 .52  0 0 0 0 .5  0 0 0 .09 0"/></filter>
<radialGradient id="milk" cx=".35" cy=".3" r=".9"><stop offset="0" stop-color="#ebe7df"/><stop offset=".6" stop-color="#d3cdc3"/><stop offset="1" stop-color="#b9b2a7"/></radialGradient>`);
 const svg=board.querySelector('svg');const w=svg.getAttribute('width');const g=board.querySelector('svg>g:nth-of-type(2)');
 g.insertAdjacentHTML('beforebegin',`<rect width="${w}" height="${w}" filter="url(#frost)" pointer-events="none" style="mix-blend-mode:multiply"/>`)}"""
MID="""()=>{const seen=new Set(L.start),q=[...L.start];while(q.length&&seen.size<Math.round(L.pieces.length*.3)){const i=q.shift();for(const j of L.nb[i])if(!seen.has(j)){seen.add(j);q.push(j)}}
 seen.forEach(i=>{grid[0][i]=L.sol[0][i];lock.add(i)});render();
 const c=[...seen].map(i=>L.pieces[i].pole).reduce((a,p)=>[a[0]+p[0]/seen.size,a[1]+p[1]/seen.size],[0,0]),U=L.n*cs;Z.tx=BV.w/2-(c[0]*U+padF);Z.ty=BV.h/2-(c[1]*U+padF);clamp();apply()}"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
  for v in "AB":
    for st in ["start","mid"]:
      c=b.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True);pg=c.new_page()
      pg.goto(f"file://{R}/index.html#lvl=3");pg.wait_for_timeout(500)
      if st=="mid": pg.evaluate(MID)
      pg.add_style_tag(content=CSS[v])
      if v=="B": pg.evaluate(DEFS)
      pg.wait_for_timeout(300);pg.screenshot(path=f"{OUT}contrast_{v}_{st}.png");c.close()
  b.close()
