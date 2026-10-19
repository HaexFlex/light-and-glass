"""cleanup_level.py in.json out.json [rounds=3]: cleanup.py -> blobify.py -> degfix.py, repeated until no thin pane / arm is left (or no progress), then prints thin/arm counts.
Output has no starts/auto/clues: run rework.py (+ mechfirst.py for mechanic levels) next."""
import sys,os,json,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from cleanup import thin_count
H=os.path.dirname(os.path.abspath(__file__))
def counts(f):
  lv=json.load(open(f));G=[Polygon(p['p']) for p in lv['pieces']];sk=set(lv.get('detail',[]))|set(lv.get('gift',[]))
  return thin_count(G,['x' if i in sk else None for i in range(len(G))])+(len(G),max(len(n) for i,n in enumerate(lv['nb']) if i not in sk))
a,b=sys.argv[1:3];R=int(sys.argv[3]) if len(sys.argv)>3 else 3;tmp=b+'.w';c0=counts(a);cur=a;last=None
for r in range(R):
  for step,args in (('blobify.py',[]),('cleanup.py',[]),('degfix.py',[])):
    subprocess.run(['python3',os.path.join(H,step),cur,tmp+str(r)+step]+args,check=True,capture_output=True);cur=tmp+str(r)+step
  c=counts(cur);print('round',r,'thin,arms,panes,maxdeg',c,flush=True)
  if (c[0]==0 and c[1]==0) or c[:2]==last: break
  last=c[:2]
for step in ('blobify.py','degfix.py'):   # final tidy: cut remaining thin panes that have no same-colour neighbour
  subprocess.run(['python3',os.path.join(H,step),cur,tmp+'f'+step],check=True,capture_output=True);cur=tmp+'f'+step
c=counts(cur);print('final',c,flush=True)
lv=json.load(open(cur));lv['metrics'].update(thin_before=c0[0],arms_before=c0[1],thin_after=c[0],arms_after=c[1]);json.dump(lv,open(b,'w'))
print('CLEAN',lv['id'],'thin',c0[0],'->',c[0],'arms',c0[1],'->',c[1],'panes',c0[2],'->',c[2],'maxdeg',c[3])
