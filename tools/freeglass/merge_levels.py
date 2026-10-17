"""Append finished raster.py outputs (levels/source/out_<id>.json) to the level set with a tier (levels/data/<id>.json + manifest). Existing levels are never touched.
usage: merge_levels.py id:tier [id:tier ...]"""
import json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import levelstore as ls
R=ls.ROOT
for a in sys.argv[1:]:
    i,t=a.split(':');o=json.load(open(os.path.join(R,f'levels/source/out_{i}.json')));o['tier']=int(t)
    assert not os.path.exists(os.path.join(ls.DATA,o['id']+'.json')),o['id']
    ls.save(o)
ls.rebuild()
