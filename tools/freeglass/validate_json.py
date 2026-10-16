"""Independent re-validation of levels/levels_free.json (v3 natural-shape rules), from the exported coordinates:
valid simple polygons, exact partition of the window, adjacency = shared border length > 0 (corner/point touches are
not neighbours), no ambiguous contacts (0 < shared < LSNAP), no jaggy spikes, nb lists match geometry, cascade solves uniquely."""
import json,sys,os
from shapely.geometry import Polygon
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass3 import adjacency, spikes_of, ring, angles
from freeglass2 import solve
from autofill import simulate
AF_CAP=3   # max autofill events per level (the game reveals one deadlock-breaking pane each time)
from shapely.ops import unary_union
ok_all=True
for lv in json.load(open(os.path.join(os.path.dirname(__file__),'../../levels/levels_free.json'))):
  G=[Polygon(p['p']) for p in lv['pieces']]
  invalid=sum(not g.is_valid for g in G); A=1/lv.get('aspect',1); cover=abs(unary_union(G).area-A); overlap=abs(sum(g.area for g in G)-A)
  nb,amb,corner,minL=adjacency(G); mism=sum(set(a)!=set(b) for a,b in zip(nb,lv['nb']))
  sp=sum(spikes_of(ring(g)) for g in G); mina=min(min(angles(ring(g))) for g in G)
  unk0=solve(lv['sol'],lv['nb'],len(lv['colors']),lv['start']); af=[]; unk=unk0
  if unk0: af,unk=simulate(lv['sol'],lv['nb'],len(lv['colors']),lv['start'],cap=AF_CAP+1)
  if len(af)>AF_CAP: unk=max(unk,1)
  good=not invalid and cover<1e-4 and overlap<1e-4 and not amb and not mism and not sp and unk==0; ok_all&=good
  print(f"{lv['name']:16s} panes={len(G)} invalid={invalid} cover_err={cover:.1e} ambiguous={len(amb)} corner_touches={corner} nb_mismatch={mism} spikes={sp} min_angle={mina:.1f} min_border={minL:.4f} unsolved={unk} autofill={len(af)} -> {'PASS' if good else 'FAIL'}")
sys.exit(0 if ok_all else 1)
