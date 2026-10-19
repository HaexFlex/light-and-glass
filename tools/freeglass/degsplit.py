"""degsplit.py in.json out.json [md=10]: any pane (not gift/detail) with more than md neighbours that degfix could not fix is cut into k compact pieces of the same colour
(k-means partition, k=2.. until every piece has <=md neighbours). Colour map unchanged; start/auto dropped like blobify."""
import sys,json,math,os,random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon
from shapely.ops import polylabel
import freeglass3
freeglass3.STRICT_SPIKES=False
from freeglass3 import check,ring,export
from split_thin import parts,insert_pts
from blobify import bad,MINPIECE
def main(a,b,md=10,seed=0):
  md=int(md);lv=json.load(open(a));G=[Polygon(p['p']) for p in lv['pieces']];sol=list(lv['sol']);n0=len(G);rnd=random.Random(int(seed))
  sk=set(lv.get('detail',[]))|set(lv.get('gift',[]));freeglass3.set_frame(1.0,1/lv.get('aspect',1));nb=lv['nb'];cuts=0
  for _ in range(20):
    over=[i for i in range(len(G)) if i not in sk and len(nb[i])>md]
    if not over: break
    i=max(over,key=lambda i:len(nb[i]));g=G[i];done=False
    for k in range(2,8):
      best=None
      for tr in range(10):
        q=parts(g,k,rnd,pp=tr>0)
        if not q or len(q)!=k or min(p.area for p in q)<MINPIECE: continue
        pts=[tuple(c) for p in q for c in ring(p)];H=list(G);H[i]=q[0];H+=q[1:]
        for j in range(len(G)):
          if j!=i and G[j].distance(g)<1e-5: H[j]=insert_pts(G[j],pts)
        try: H2,_=export(H);ok,nb2,v=check(H2)
        except Exception: continue
        if not ok or not all(nb2): continue
        mx=max(len(nb2[x]) for x in [i]+list(range(len(G),len(H2))));sc=(mx>md,max(bad(p) for p in q))
        if best is None or sc<best[0]: best=(sc,H2,nb2)
      if best and not best[0][0]:
        G=best[1];nb=best[2];sol=sol+[sol[i]]*(k-1);cuts+=1;done=True;break
    if not done: print('could not split',i,len(nb[i]));sk.add(i)
  ok,nb,v=check(G);P=[]
  det=set(lv.get('detail',[]))
  for i,g in enumerate(G):
    p=dict(lv['pieces'][i]) if i in det else {}
    p['p']=[list(x) for x in ring(g)];pl=polylabel(g,1e-4);p['pole']=[round(pl.x,5),round(pl.y,5)];p['rin']=round(g.exterior.distance(pl),5);P.append(p)
  lv['pieces']=P;lv['sol']=sol;lv['nb']=nb;lv.pop('auto',None);lv['metrics']=dict(lv.get('metrics',{}),pieces=len(G))
  json.dump(lv,open(b,'w'));print('degsplit cuts',cuts,'panes',n0,'->',len(G),'maxdeg',max(len(nb[i]) for i in range(len(G)) if i not in set(lv.get('detail',[]))|set(lv.get('gift',[]))))
if __name__=='__main__': main(*sys.argv[1:3],*sys.argv[3:5])
