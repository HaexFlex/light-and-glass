"""compact.py [level.json ...]: compactness report. Per pane: aspect (long/short side of the min-area rectangle, also counting thin curved bands via area/(2*inradius)^2),
solidity = area / convex hull area, neighbours (degree) and degree per perimeter. Flag = aspect>MAXASP or solidity<MINSOL, tiny panes (area < TINY) excluded.
Importable: stats(lv) -> dict(worst_aspect, mean_aspect, worst_solidity, mean_solidity, flagged=[idx], max_deg_per_perim, ...)."""
import sys, os, json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from split_thin import metrics
MAXASP=3.0; MINSOL=0.7; TINY=0.0005
def pane(g,deg):
  asp=metrics(g)[0]; sol=g.area/max(g.convex_hull.area,1e-12); return asp,sol,deg/max(g.length,1e-9)
def stats(lv):
  G=[Polygon(p['p']) for p in lv['pieces']]; skip=set(lv.get('gift',[]))|set(lv.get('detail',[]))
  rows=[(i,)+pane(g,len(lv['nb'][i]))+(g.area,) for i,g in enumerate(G) if i not in skip]
  big=[r for r in rows if r[4]>=TINY]; fl=[r[0] for r in big if r[1]>MAXASP or r[2]<MINSOL]
  return dict(n=len(G),worst_aspect=round(max(r[1] for r in big),2),mean_aspect=round(sum(r[1] for r in big)/len(big),2),worst_solidity=round(min(r[2] for r in big),2),
    mean_solidity=round(sum(r[2] for r in big)/len(big),3),max_deg_per_perim=round(max(r[3] for r in big),1),mean_deg_per_perim=round(sum(r[3] for r in big)/len(big),1),flagged=fl,tiny=len(rows)-len(big))
if __name__=='__main__':
  import glob
  fs=sys.argv[1:] or sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../levels/data/*.json')))
  for f in fs:
    lv=json.load(open(f)); s=stats(lv); print(f"{lv['id']:13s} panes={s['n']} worstAsp={s['worst_aspect']} meanAsp={s['mean_aspect']} worstSol={s['worst_solidity']} meanSol={s['mean_solidity']} deg/perim max={s['max_deg_per_perim']} mean={s['mean_deg_per_perim']} flagged={len(s['flagged'])} tiny={s['tiny']}")
