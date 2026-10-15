"""Append finished raster.py outputs (levels/source/out_<id>.json) to levels/levels_free.json with a tier. Existing entries are never touched.
usage: merge_levels.py id:tier [id:tier ...]"""
import json,sys,os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../..')
P=os.path.join(R,'levels/levels_free.json');L=json.load(open(P))
raw=open(P).read()
for a in sys.argv[1:]:
    i,t=a.split(':');o=json.load(open(os.path.join(R,f'levels/source/out_{i}.json')));o['tier']=int(t)
    assert not any(l['id']==o['id'] for l in L),o['id']
    L.append(o)
compact=json.dumps(L[:11],separators=(',',':'))
sep=(',',':') if raw.startswith('[{"') else None
open(P,'w').write(json.dumps(L,separators=sep) if sep else json.dumps(L))
