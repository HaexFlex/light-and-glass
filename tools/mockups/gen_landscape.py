"""Generate the 30-pane 'Sunset Lake' landscape for the Canvas mockups -> landscape30.json.
Panes are defined back-to-front, then subtracted so they tile the 360x270 canvas exactly (shared lead lines)."""
import json,math,os
import numpy as np
from shapely.geometry import Polygon,MultiPolygon,box
from shapely.ops import unary_union
W,H=360,270
def circ(cx,cy,r,n=48): return Polygon([(cx+r*math.cos(2*math.pi*i/n),cy+r*math.sin(2*math.pi*i/n)) for i in range(n)])
def ell(cx,cy,rx,ry,n=48): return Polygon([(cx+rx*math.cos(2*math.pi*i/n),cy+ry*math.sin(2*math.pi*i/n)) for i in range(n)])
def ridge(pts,bottom,step=6):
    xs=[p[0] for p in pts];ys=[p[1] for p in pts];out=[]
    for x in range(int(xs[0]),int(xs[-1])+1,step):
        i=max(j for j in range(len(xs)-1) if xs[j]<=x) if x<xs[-1] else len(xs)-2
        t=(x-xs[i])/(xs[i+1]-xs[i]);t=(1-math.cos(math.pi*t))/2
        out.append((x,ys[i]+(ys[i+1]-ys[i])*t))
    out.append((xs[-1],ys[-1]))
    return Polygon(out+[(xs[-1],bottom),(xs[0],bottom)])
def band(y0pts,y1pts):
    top=[(x,y) for x,y in y0pts];bot=[(x,y) for x,y in y1pts][::-1]
    return Polygon(top+bot)
def wave(y,amp,ph,x0=0,x1=W,step=10): return [(x,y+amp*math.sin(x/38+ph)) for x in range(x0,x1+1,step)]
SX,SY=185,138
left=box(-1,-1,SX,H+1);right=box(SX,-1,W+1,H+1)
def halfp(p,pt,d):  # half-plane through pt, normal d
    big=1000;nx,ny=d;tx,ty=-ny,nx
    return Polygon([(pt[0]+tx*big,pt[1]+ty*big),(pt[0]+tx*big+nx*big,pt[1]+ty*big+ny*big),(pt[0]-tx*big+nx*big,pt[1]-ty*big+ny*big),(pt[0]-tx*big,pt[1]-ty*big)])
L=[]  # (name,colour,geom) back to front
def add(n,c,g): L.append((n,c,g))
# sky
add("Zenith","#2e3a96",Polygon([(0,0),(120,0),(92,55),(0,70)]))
add("Dusk violet","#6a4fb8",Polygon([(120,0),(240,0),(215,48),(92,55)]))
add("Blue haze","#3f78c9",Polygon([(240,0),(W,0),(W,58),(290,52),(215,48)]))
add("Rose sky L","#f08c9c",Polygon([(0,70),(92,55),(215,48),(215,170),(0,170)]))
add("Amber sky R","#f6a35e",Polygon([(215,48),(290,52),(W,58),(W,170),(215,170)]))
# sun + halos
tilt=(0.35,1)
add("Outer glow L","#ffc27a",circ(SX,SY,76).intersection(halfp(0,(SX,SY),(-1,0.0))))
add("Outer glow R","#ffad5c",circ(SX,SY,76).intersection(halfp(0,(SX,SY),(1,0.0))))
add("Halo L","#ffe08e",circ(SX,SY,50).intersection(halfp(0,(SX,SY),(-1,0))))
add("Halo R","#ffd36b",circ(SX,SY,50).intersection(halfp(0,(SX,SY),(1,0))))
add("Sun","#fff6cf",circ(SX,SY,27))
# far hills (violet) split at sun
far=ridge([(0,112),(40,94),(85,112),(125,134),(185,147),(245,134),(285,108),(325,90),(W,106)],200)
add("Far hills L","#6c4a9f",far.intersection(left));add("Far hills R","#8a4f98",far.intersection(right))
# lake
add("Horizon glow","#ffbd72",box(-1,149,W+1,163))
add("Lake shallows","#4a86c9",box(-1,160,W+1,198))
add("Lake mid","#6b5cb4",Polygon(wave(193,4,1)+[(W,232),(0,232)]) )
add("Lake deep","#2a4f90",Polygon(wave(228,4,2)+[(W+1,H+1),(-1,H+1)]))
wedgeA=Polygon([(178,160),(192,160),(222,212),(148,212)])
wedgeB=Polygon([(148,212),(222,212),(252,H+1),(118,H+1)])
add("Reflection gold","#ffd27c",wedgeA);add("Reflection ember","#ff8f58",wedgeB)
# mid hills
add("Mid hill L","#2f8f8a",Polygon([(0,136),(55,126),(110,145),(150,176),(125,196),(0,198)]))
add("Mid hill R","#3aa273",Polygon([(W,134),(310,124),(262,148),(222,176),(240,196),(W,198)]))
add("Meadow L","#e0b13c",Polygon([(0,170),(55,164),(110,190),(128,214),(70,236),(0,232)]))
add("Bank L","#2a6a46",Polygon([(0,228),(70,232),(120,H+1),(-1,H+1)]))
add("Bank R","#1f4d3a",Polygon([(W+1,236),(300,240),(250,H+1),(W+1,H+1)]))
# tree on right
add("Trunk","#6a3f26",Polygon([(308,238),(313,190),(316,150),(326,150),(329,190),(336,238)]))
crown=ell(321,114,46,40)
add("Crown red","#e4572e",crown.intersection(Polygon([(0,108),(322,100),(322,300),(0,300)])))
add("Crown gold","#f4a93a",crown.intersection(Polygon([(0,0),(500,0),(500,92),(322,100),(0,108)])))
add("Crown green","#79c25a",crown.intersection(Polygon([(322,100),(500,92),(500,300),(322,300)])))
# subtract front layers
panes=[]
for i,(n,c,g) in enumerate(L):
    g=g.intersection(box(0,0,W,H))
    front=unary_union([x[2] for x in L[i+1:]]) if i<len(L)-1 else None
    r=g.difference(front) if front else g
    geoms=list(r.geoms) if isinstance(r,MultiPolygon) else [r]
    geoms=[x for x in geoms if x.area>60]
    for k,x in enumerate(geoms):
        x=x.simplify(.4)
        panes.append(dict(name=n+(f" {k+1}" if len(geoms)>1 else ""),c=c,p=[[round(a,1),round(b,1)] for a,b in x.exterior.coords[:-1]],a=x.area))
# merge slivers into the neighbour they share the longest edge with
import shapely
geo=[Polygon(p['p']) for p in panes]
while True:
    sm=[i for i,p in enumerate(panes) if p['a']<1000]
    if not sm: break
    i=sm[0];best=None;bl=0
    for j,g in enumerate(geo):
        if j!=i:
            l=geo[i].buffer(.05).intersection(g.boundary).length
            if l>bl: bl=l;best=j
    u=geo[best].union(geo[i]).buffer(.01).buffer(-.01).simplify(.4)
    geo[best]=u;panes[best]['p']=[[round(a,1),round(b,1)] for a,b in u.exterior.coords[:-1]];panes[best]['a']=u.area
    del geo[i];del panes[i]
print(len(panes))
for p in panes: print(round(p['a']),p['name'])
out=os.path.dirname(os.path.abspath(__file__))+"/landscape30.json"
json.dump(panes,open(out,"w"))
