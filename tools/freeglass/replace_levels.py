"""Replace a level slot with a newly rasterised level of a different id/name; tier and list position are kept.  usage: replace_levels.py old=new:Name ..."""
import json,sys,os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../..');P=os.path.join(R,'levels/levels_free.json');L=json.load(open(P))
for a in sys.argv[1:]:
    old,rest=a.split('=');new,name=rest.split(':',1);o=json.load(open(os.path.join(R,f'levels/source/out_{new}.json')))
    k=[j for j,l in enumerate(L) if l['id']==old][0];o['name']=name;o['tier']=L[k]['tier'];L[k]=o
json.dump(L,open(P,'w'),separators=(',',':'))
