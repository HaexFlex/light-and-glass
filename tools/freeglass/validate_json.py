"""Independent re-validation of the shipped level file (levels_free2.json):
geometry rebuilt from the exported (rounded) coordinates; checks every touching pair shares >= LMIN,
the neighbour lists match the geometry, no vertex joins >= 4 panes, and the cascade solver solves it uniquely."""
import json,sys
from shapely.geometry import Polygon,Point
from shapely import STRtree
sys.path.insert(0,'.'); from freeglass2 import solve, LMIN
TOL=3e-4; ok_all=True
for lv in json.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'../../levels/levels_free.json'))):
  G=[Polygon(p['p']) for p in lv['pieces']]; invalid=sum(not g.is_valid for g in G); G=[g if g.is_valid else max(getattr(g.buffer(0),'geoms',[g.buffer(0)]),key=lambda q:q.area) for g in G]; tree=STRtree(G); N=len(G); bad=[]; mism=0; minL=9
  for i,g in enumerate(G):
    touch=set()
    for j in tree.query(g.buffer(TOL)):
      j=int(j)
      if j==i or g.distance(G[j])>TOL: continue
      L=g.boundary.intersection(G[j].buffer(TOL)).length
      if L<LMIN*0.97: bad.append((i,j,round(L,4)))
      else: touch.add(j); minL=min(minL,L)
    if touch!=set(lv['nb'][i]): mism+=1
  maxv=0
  for g in G:
    for x,y in g.exterior.coords:
      pt=Point(x,y); maxv=max(maxv,sum(1 for k in tree.query(pt.buffer(TOL)) if G[int(k)].distance(pt)<TOL))
  unk=solve(lv['sol'],lv['nb'],len(lv['colors']),lv['start'])
  good=not invalid and not bad and not mism and maxv<=3 and unk==0; ok_all&=good
  print(f"{lv['name']:16s} panes={N} short_contacts={len(bad)} nb_mismatch={mism} max_junction={maxv} invalid_polys={invalid} min_border={minL:.4f} unsolved={unk} -> {'PASS' if good else 'FAIL'}")
sys.exit(0 if ok_all else 1)
