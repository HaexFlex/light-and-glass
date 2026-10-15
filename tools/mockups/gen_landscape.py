"""Generate the 30-pane organic 'Sunset Lake' landscape for the Canvas mockups -> landscape30.json.
Layers are defined back-to-front with smooth curves, then subtracted so panes tile the 360x270 canvas exactly (shared lead lines)."""
import json,math,os
from shapely.geometry import Polygon,MultiPolygon,box
from shapely.ops import unary_union
W,H=360,270
def sm(pts,n=9):
    """Catmull-Rom smooth curve through pts"""
    P=[pts[0]]+list(pts)+[pts[-1]];out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
        for k in range(n):
            t=k/n;t2,t3=t*t,t*t*t
            out.append(tuple(.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in (0,1)))
    out.append(pts[-1]);return out
def circ(cx,cy,r,n=64): return Polygon([(cx+r*math.cos(2*math.pi*i/n),cy+r*math.sin(2*math.pi*i/n)) for i in range(n)])
def ell(cx,cy,rx,ry,n=64): return Polygon([(cx+rx*math.cos(2*math.pi*i/n),cy+ry*math.sin(2*math.pi*i/n)) for i in range(n)])
def wave(y,amp,ph,x0=-5,x1=W+5,step=6,k=34): return [(x,y+amp*math.sin(x/k+ph)+.4*amp*math.sin(x/(k*.45)+ph*2)) for x in range(x0,x1+1,step)]
SX,SY=185,140
L=[]
def add(n,c,g): L.append((n,c if isinstance(c,(list,tuple)) else [c],g))
# ---- sky
C=sm([(212,0),(207,50),(220,110),(213,176)])
add("Rose sky",["#f08c9c","#f6a35e"],None)  # placeholder replaced below
L.pop()
add("Rose sky","#f08c9c",Polygon([(-5,-5),(212,-5)]+C[1:]+[(-5,176)]))
add("Amber sky","#f6a35e",Polygon([(212,-5),(365,-5),(365,176),(213,176)]+C[::-1][1:]))
add("Dusk violet","#6a4fb8",Polygon([(-5,-5),(365,-5),(365,64)]+sm([(365,64),(300,56),(228,52),(160,60),(90,54),(-5,70)])[1:]))
add("Zenith","#2e3a96",Polygon([(-5,-5),(126,-5)]+sm([(126,-5),(116,22),(84,42),(40,52),(-5,58)])[1:]))
add("Blue haze","#3f78c9",Polygon([(246,-5),(365,-5),(365,52)]+sm([(365,52),(322,48),(284,30),(246,-5)])[1:]))
# ---- sun
lh=box(-5,-5,SX,H+5);rh=box(SX,-5,W+5,H+5)
add("Outer glow L","#ffc27a",ell(SX,SY,88,76).intersection(lh));add("Outer glow R","#ffad5c",ell(SX,SY,88,76).intersection(rh))
add("Halo L","#ffe08e",circ(SX,SY,52).intersection(lh));add("Halo R","#ffd36b",circ(SX,SY,52).intersection(rh))
add("Sun","#fff6cf",circ(SX,SY,28))
# ---- far hills (violet), tapering into the horizon
far=Polygon(sm([(-5,108),(28,94),(60,99),(92,114),(120,134),(142,149),(150,151)])+[(150,151)]+[(-5,151)])
farR=Polygon([(228,151)]+sm([(228,151),(248,134),(274,112),(300,98),(330,92),(352,100),(365,108)])[1:]+[(365,151)])
add("Far hills L","#6c4a9f",far);add("Far hills R","#8a4f98",farR)
# ---- lake
add("Horizon glow","#ffbd72",Polygon([(-5,150),(365,150)]+wave(163,2.2,0.5)[::-1]))
add("Lake shallows",["#4a86c9","#5b9ad6"],Polygon(wave(160,2.2,.5)+wave(198,4,1.2)[::-1]))
add("Lake mid",["#6b5cb4","#8a68b8"],Polygon(wave(196,4,1.2)+wave(234,4.5,2.4)[::-1]))
add("Lake deep",["#2a4f90","#35609e"],Polygon(wave(232,4.5,2.4)+[(365,275),(-5,275)]))
def column():
    l=[];r=[]
    for y in range(158,281,3):
        t=(y-158)/115;w=(3+60*t**1.05)*min(1,math.sqrt((y-158)/12))+3.0*math.sin(y/8.5)*min(.3+t,(y-158)/20)
        w=max(w,1.2);l.append((SX-w,y));r.append((SX+w+1.4*math.sin(y/7+1)*min(1,t*4),y))
    return Polygon(l+r[::-1])
col=column()
add("Reflection ember","#ff8f58",col)
add("Reflection gold","#ffd27c",col.intersection(Polygon(wave(212,6,.8)+[(365,100),(-5,100)])))
# ---- hills in front of the lake (flowing)
add("Mid hill L","#2f8f8a",Polygon(sm([(-5,134),(40,122),(86,129),(124,147),(150,166),(158,184)])+sm([(158,184),(118,196),(60,200),(-5,194)])[1:]))
add("Hill R","#3aa273",Polygon(sm([(224,176),(246,162),(280,150),(320,144),(365,148)])+[(365,276),(262,276)]+sm([(262,276),(258,236),(246,204),(224,176)])[1:]))
add("Meadow L","#e0b13c",Polygon(sm([(-5,168),(36,160),(84,172),(118,196),(126,218),(96,234),(40,238),(-5,232)])))
add("Bank L","#2a6a46",Polygon(sm([(-5,226),(44,230),(94,242),(122,276)])+[(-5,276)]))
add("Bank R","#1f4d3a",Polygon(sm([(365,246),(330,252),(300,260),(278,276)])+[(365,276)]))
# ---- organic tree (right bank)
TX=326
trunk=Polygon(sm([(TX-16,236),(TX-9,212),(TX-4,184),(TX-5,150)])+[(TX+7,150)]+sm([(TX+7,150),(TX+8,184),(TX+13,216),(TX+24,244)])[::1][:0]+sm([(TX+7,150),(TX+8,184),(TX+13,212),(TX+24,236)]))
add("Trunk","#6a3f26",trunk)
lobes=[(TX+34,138,22),(TX+40,118,24),(TX,112,31),(TX-24,124,22),(TX+26,122,23),(TX-12,90,22),(TX+16,88,23),(TX+2,138,19),(TX+36,100,15),(TX-34,100,15)]
crown=unary_union([circ(a,b,r) for a,b,r in lobes]).buffer(8).buffer(-8)
gold=Polygon([(0,0),(500,0),(500,60)]+sm([(500,84),(TX+50,92),(TX+14,104),(TX-14,98),(TX-60,84)])+[(0,0)])
red=Polygon(sm([(TX-70,92),(TX-30,104),(TX-6,122),(TX+4,150),(TX+8,200)])+[(TX-70,200)])
add("Crown green","#79c25a",crown)
add("Crown red","#e4572e",crown.intersection(Polygon(sm([(TX-70,86),(TX-30,100),(TX-8,120),(TX+2,150),(TX+6,200)])+[(TX-70,200)])).difference(box(-10,-10,500,0)))
add("Crown gold","#f4a93a",crown.intersection(Polygon(sm([(0,0),(0,0)])+[(0,0),(500,0),(500,84)]+sm([(500,84),(TX+50,92),(TX+14,104),(TX-14,98),(TX-60,84)])[1:]+[(0,84)])))
# ---- subtract front layers
panes=[];box_=box(0,0,W,H)
for i,(n,cols,g) in enumerate(L):
    g=g.buffer(0).intersection(box_)
    front=unary_union([x[2] for x in L[i+1:]]) if i<len(L)-1 else None
    r=g.difference(front) if front is not None else g
    geoms=[x for x in (r.geoms if hasattr(r,'geoms') else [r]) if x.area>1]
    geoms.sort(key=lambda x:x.centroid.x)
    for k,x in enumerate(geoms):
        x=x.simplify(.35)
        nm=n+((" L"," R")[k] if len(geoms)==2 else (f" {k+1}" if len(geoms)>2 else ""))
        panes.append(dict(name=nm,c=cols[min(k,len(cols)-1)],g=x,a=x.area))
# merge slivers
while True:
    sm_=[i for i,p in enumerate(panes) if p['a']<650]
    if not sm_: break
    i=sm_[0];best=None;bl=0
    for j,p in enumerate(panes):
        if j!=i:
            l=panes[i]['g'].buffer(.05).intersection(p['g'].boundary).length
            if l>bl: bl=l;best=j
    print("merge",panes[i]['name'],"->",panes[best]['name'] if best is not None else None)
    if best is not None:
        u=panes[best]['g'].union(panes[i]['g']).buffer(.01).buffer(-.01).simplify(.35)
        panes[best]['g']=u;panes[best]['a']=u.area
    del panes[i]
out=[]
for p in panes:
    g=p['g']
    if isinstance(g,MultiPolygon): g=max(g.geoms,key=lambda z:z.area)
    out.append(dict(name=p['name'],c=p['c'],p=[[round(a,1),round(b,1)] for a,b in g.exterior.coords[:-1]],a=round(g.area)))
print(len(out))
for p in out: print(p['a'],p['name'])
json.dump(out,open(os.path.dirname(os.path.abspath(__file__))+"/landscape30.json","w"))
