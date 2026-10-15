"""Replace existing level entries (same id/name/tier/position) with freshly rasterised levels/source/out_<id>.json. usage: rebuild_levels.py id [id ...]"""
import json,sys,os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../..');P=os.path.join(R,'levels/levels_free.json');L=json.load(open(P))
for i in sys.argv[1:]:
    o=json.load(open(os.path.join(R,f'levels/source/out_{i}.json')));k=[j for j,l in enumerate(L) if l['id']==i][0]
    o['name']=L[k]['name'];o['tier']=L[k]['tier'];L[k]=o
json.dump(L,open(P,'w'),separators=(',',':'))
