"""Independent re-validation of every level in levels/data (via levels/manifest.json) (v3 natural-shape rules), from the exported coordinates:
valid simple polygons, exact partition of the window, adjacency = shared border length > 0 (corner/point touches are
not neighbours), no ambiguous contacts (0 < shared < LSNAP), no jaggy spikes, nb lists match geometry, cascade solves uniquely."""
import json,sys,os
from shapely.geometry import Polygon
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass3 import adjacency, spikes_of, ring, angles
from freeglass2 import solve
from autofill import simulate, tap_stats
from shapely.ops import unary_union
import compact
ok_all=True
def _levels():
  if len(sys.argv)>1:   # validate_json.py out_x.json ... : check single level files
    return [json.load(open(f)) for f in sys.argv[1:]]
  import levelstore; return levelstore.load_all()
for lv in _levels():
  G=[Polygon(p['p']) for p in lv['pieces']]
  invalid=sum(not g.is_valid for g in G); A=1/lv.get('aspect',1); cover=abs(unary_union(G).area-A); overlap=abs(sum(g.area for g in G)-A)
  nb,amb,corner,minL=adjacency(G); mism=sum(set(a)!=set(b) for a,b in zip(nb,lv['nb']))
  sp=sum(spikes_of(ring(g)) for g in G); mina=min(min(angles(ring(g))) for g in G)
  gift=lv.get('gift',[]); det=lv.get('detail',[]); detbad=any(not 0<=g<len(G) for g in det) or len(set(det))!=len(det) or bool(set(det)&set(gift)) or any(s in set(det) for s in lv['start']) or any(not lv['pieces'][g].get('detail') for g in det if 0<=g<len(G)); giftbad=any(not 0<=g<len(G) for g in gift) or len(set(gift))!=len(gift) or any(s in set(gift) for s in lv['start'])
  auto=lv.get('auto',[]); autobad=any(not 0<=a<len(G) for a in auto) or len(set(auto))!=len(auto) or bool((set(auto)|set()) & (set(gift)|set(det)|set(lv['start'])))
  nots=lv.get('not',{}); K=len(lv['colors']); notbad=not isinstance(nots,dict) or any(not k.isdigit() or not 0<=int(k)<len(G) or int(k) in set(lv['start'])|set(gift)|set(det) or not v or len(set(v))!=len(v) or any(not isinstance(c,int) or not 0<=c<K or any(lv['sol'][q]==c for q in lv['nb'][int(k)]) for c in v) for k,v in (nots.items() if isinstance(nots,dict) else []))
  if notbad: nots={}
  canes=lv.get('canes',[]); P=[[tuple(x) for x in pc['p']] for pc in lv['pieces']]
  def _edge(a,b):
    eb={frozenset((P[b][i],P[b][(i+1)%len(P[b])])) for i in range(len(P[b]))}; return any(frozenset((P[a][i],P[a][(i+1)%len(P[a])])) in eb for i in range(len(P[a])))
  canebad=not isinstance(canes,list) or len({frozenset(c) for c in canes})!=len(canes) or any(len(c)!=2 or not all(isinstance(x,int) and 0<=x<len(G) for x in c) or c[1] not in lv['nb'][c[0]] or lv['sol'][c[0]]==lv['sol'][c[1]] or not _edge(c[0],c[1]) for c in canes)
  if canebad: canes=[]
  ros=lv.get('ros',[]); used=set()
  def _contig(ps):
    ps=set(ps); seen={next(iter(ps))}; st=list(seen)
    while st:
      x=st.pop()
      for y in lv['nb'][x]:
        if y in ps and y not in seen: seen.add(y); st.append(y)
    return seen==ps
  rosbad=not isinstance(ros,list)
  for r in (ros if not rosbad else []):
    ps=r.get('panes',[]); cs=r.get('cols',[])
    if not 3<=len(ps)<=6 or len(set(ps))!=len(ps) or any(not isinstance(x,int) or not 0<=x<len(G) for x in ps) or set(ps)&(used|set(lv['start'])|set(gift)|set(det)) or not _contig(ps) or sorted(set(cs))!=sorted({lv['sol'][x] for x in ps}) or len(cs)!=len(set(cs)): rosbad=True; break
    used|=set(ps)
  if rosbad: ros=[]
  unk0=solve(lv['sol'],lv['nb'],len(lv['colors']),lv['start'],gift=gift,detail=det,auto=auto,nots=nots,canes=canes,ros=ros); af=[]; unk=unk0
  if unk0: af,unk=simulate(lv['sol'],lv['nb'],len(lv['colors']),lv['start'],gift=gift,detail=det,auto=auto,nots=nots,canes=canes,ros=ros)
  ts=tap_stats(lv['sol'],lv['nb'],len(lv['colors']),lv['start'],gift,det,auto,nots,canes,ros) if auto else None
  chainbad=bool(ts) and ts['settle']>1.5*len(lv['start'])+3
  cs=compact.stats(lv); maxdeg=max(len(x) for i,x in enumerate(lv['nb']) if i not in set(det)); degbad=maxdeg>10   # detail panes (art inside) are exempt
  good=not invalid and cover<1e-4 and overlap<1e-4 and not amb and not mism and unk==0 and not degbad and not giftbad and not detbad and not autobad and not chainbad and not notbad and not canebad and not rosbad; ok_all&=good
  print(f"{lv['name']:16s} panes={len(G)} invalid={invalid} cover_err={cover:.1e} ambiguous={len(amb)} corner_touches={corner} nb_mismatch={mism} spikes={sp} min_angle={mina:.1f} min_border={minL:.4f} unsolved={unk} autofill={len(af)} gift={len(gift)} detail={len(det)} auto={len(auto)} not={len(nots)} canes={len(canes)} ros={len(ros)} maxdeg={maxdeg}"+(f" max_chain={ts['max_chain']} mean_chain={ts['mean_chain']} depth={ts['max_depth']} settle={ts['settle']} taps={ts['taps']} chains={ts['chains']}" if ts else "")+f" compact: worstAsp={cs['worst_aspect']} meanAsp={cs['mean_aspect']} worstSol={cs['worst_solidity']} meanSol={cs['mean_solidity']} flagged={len(cs['flagged'])}"+f" -> {'PASS' if good else 'FAIL'}")
sys.exit(0 if ok_all else 1)
