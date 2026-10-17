"""Replace a level slot with a newly rasterised level of a different id/name; tier and list position are kept.  usage: replace_levels.py old=new:Name ..."""
import json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import levelstore as ls
order=[m['id'] for m in ls.manifest()]
for a in sys.argv[1:]:
    old,rest=a.split('=');new,name=rest.split(':',1);o=json.load(open(os.path.join(ls.ROOT,f'levels/source/out_{new}.json')))
    o['name']=name;o['tier']=ls.load(old)['tier'];ls.save(o);os.remove(os.path.join(ls.DATA,old+'.json'));order[order.index(old)]=new
ls.rebuild(order)
