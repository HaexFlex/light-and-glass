"""Replace existing levels (same id/name/tier/position) with freshly rasterised levels/source/out_<id>.json. usage: rebuild_levels.py id [id ...]"""
import json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import levelstore as ls
for i in sys.argv[1:]:
    old=ls.load(i);o=json.load(open(os.path.join(ls.ROOT,f'levels/source/out_{i}.json')));o['name']=old['name'];o['tier']=old['tier'];ls.save(o)
ls.rebuild()
