"""Small hand-designed levels (Beginner / Gardens). Same pipeline as freeglass3.build; picks the first seed whose pane count,
start count and mono share fit the target. python small_levels.py [id ...]  -> lvs_<id>.json"""
import json, math, sys, random
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
from shapely import affinity
from freeglass import ell, UNIT, wavy_below
import freeglass3
def heart(cx,cy,s,rot=0):
  pts=[(cx+s*16*math.sin(t)**3,cy-s*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))) for t in [i*2*math.pi/160 for i in range(160)]]
  return affinity.rotate(Polygon(pts),rot,origin=(cx,cy))
def star(cx,cy,R,r,n=5,rot=-90):
  return Polygon([(cx+(R if k%2==0 else r)*math.cos(math.radians(rot+k*180/n)),cy+(R if k%2==0 else r)*math.sin(math.radians(rot+k*180/n))) for k in range(2*n)])
def firstlight():
  C={"C":"#f6e7c8","R":"#e8527c"}
  return "firstlight","First Light",C,[("C",UNIT,.30),("R",heart(.5,.5,.021),.2)],[]
def evening_star():
  C={"N":"#2a3a82","G":"#f5c542","M":"#f4ecd6"}
  return "eveningstar","Evening Star",C,[("N",UNIT,.27),("G",star(.5,.52,.4,.17),.25),("M",Point(.5,.52).buffer(.06),1),("M",Point(.17,.17).buffer(.045),1),("M",Point(.84,.2).buffer(.035),1)],[]
def moon_water():
  C={"N":"#27346e","M":"#f3ead0","W":"#2b86a6","H":"#14213f"}
  sky=box(-.1,-.1,1.1,.62); water=wavy_below(.62,.01,2.0,.4)
  hills=Polygon([(-.1,.64),(-.1,.5),(.12,.44),(.3,.5),(.5,.56),(.7,.5),(.9,.43),(1.1,.5),(1.1,.64)])
  refl=unary_union([ell(.5,.72,.1,.03),ell(.5,.81,.065,.026),ell(.5,.9,.04,.022)])
  return "moonwater","Moon over Water",C,[("N",UNIT,.2),("W",water,.17),("H",hills,.2),("M",Point(.5,.28).buffer(.15),.13),("M",refl,1)],[]
def daisy():
  C={"S":"#8ec9ee","W":"#fbf7ee","Y":"#f3b81f","G":"#4e9a49"}
  cx,cy=.5,.38
  petals=unary_union([ell(cx+.17*math.cos(a),cy+.17*math.sin(a),.12,.05,math.degrees(a)) for a in [i*math.pi/4 for i in range(8)]])
  stem=LineString([(cx,cy+.15),(cx-.02,.7),(cx+.01,1.02)]).buffer(.03)
  leaves=unary_union([ell(.35,.77,.11,.04,-30),ell(.65,.7,.11,.04,30)])
  return "daisy","Little Daisy",C,[("S",UNIT,.19),("G",unary_union([stem,leaves]),.12),("W",petals,.1),("Y",Point(cx,cy).buffer(.09),.2)],[]
def butterfly():
  C={"T":"#7fc8c0","O":"#f08a3c","V":"#8a5cc0","K":"#3a2a33","C":"#fbefd6"}
  def wing(sx,cx,cy,rx,ry,rot): return ell(.5+sx*cx,cy,rx,ry,sx*rot)
  up=unary_union([wing(1,.2,.36,.2,.15,-28),wing(-1,.2,.36,.2,.15,-28)])
  lo=unary_union([wing(1,.15,.62,.14,.11,28),wing(-1,.15,.62,.14,.11,28)])
  body=ell(.5,.5,.03,.2); spots=unary_union([Point(.5+s*.2,.34).buffer(.035) for s in (-1,1)]+[Point(.5+s*.14,.62).buffer(.025) for s in (-1,1)])
  return "butterfly","Butterfly",C,[("T",UNIT,.2),("O",up,.14),("V",lo,.12),("C",spots,1),("K",body,.2)],[]
def cottage():
  C={"S":"#86bde6","G":"#5fa04a","W":"#ecdcb8","R":"#b5472f","H":"#e8527c","D":"#6b4226"}
  wall=box(.2,.5,.8,.86); roof=Polygon([(.14,.52),(.5,.2),(.86,.52)]); grass=wavy_below(.84,.012,1.5)
  return "cottage","Cottage",C,[("S",UNIT,.22),("G",grass,.18),("W",wall,.15),("R",roof,.13),("D",box(.6,.66,.72,.86),1),("H",heart(.38,.62,.0065),1)],[]
DESIGNS={f().__getitem__(0) if False else d()[0]:d for d in (firstlight,evening_star,moon_water,daisy,butterfly,cottage)}
TARGET={"firstlight":(12,18,1,.8),"eveningstar":(18,28,2,.6),"moonwater":(26,38,2,.5),"daisy":(30,42,2,.5),"butterfly":(36,48,2,.5),"cottage":(34,48,2,.5)}
def run(key):
  lo,hi,maxst,maxmono=TARGET[key]; best=None
  for seed in range(1,60):
    for sp in (1.0,):
      try: lv=freeglass3.build(DESIGNS[key],seed,rmin=.03)
      except (SystemExit,AssertionError,Exception) as e: continue
      if maxst==1 and lv['metrics']['starts']>1:   # exhaustive: is there a single pane that solves everything?
        from freeglass2 import solve
        K=len(lv['colors']); sing=[i for i in range(len(lv['sol'])) if not solve(lv['sol'],lv['nb'],K,[i])]
        if sing:
          i=max(sing,key=lambda i:len(lv['nb'][i])); lv['start']=[i]; _,st=solve(lv['sol'],lv['nb'],K,[i],True)
          lv['metrics'].update(starts=1,**st,mono_share=round(st['mono']/max(1,st['determined']),2),combined_share=round(st['combined']/max(1,st['determined']),2))
      m=lv['metrics']; ok=lo<=m['pieces']<=hi and m['starts']<=maxst and m['mono_share']<=maxmono
      print(key,'seed',seed,m['pieces'],'starts',m['starts'],'mono',m['mono_share'],'comb',m['combined_share'],'rounds',m['rounds'],'OK' if ok else '',flush=True)
      if ok: lv['metrics']['seed']=seed; return lv
  raise SystemExit(key+': no seed fits')
if __name__=="__main__":
  for k in (sys.argv[1:] or DESIGNS):
    try: lv=run(k)
    except SystemExit as e: print(e); continue
    json.dump(lv,open(f"lvs_{k}.json","w")); print("saved",k,json.dumps(lv['metrics']),flush=True)
