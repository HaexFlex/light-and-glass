"""mechfirst.py cur.json base.json out.json [seed=0]: mechanics-first clue placement (Tinted bubbles / Stained canes+bubbles / Jewel rosettes+canes+bubbles).
cur.json = the level as stored (geometry, auto); base.json = the same level before any mechanic clues (its lit starts are the starting point).
1) clues FIRST, to the tier quota: repeatedly take away the lit start whose loss hurts most and patch the gap with clues of the type still below quota
   (round-robin over types); 2) then remove lit starts (Jewel: then auto panes) while the level stays solvable, i.e. barely unique and no-guess;
3) every clue must be NECESSARY: an unneeded clue is dropped and replaced by a new one that pays for removing another lit start; 2) and 3) repeat until stable.
Model = one badge at a time (freeglass2.solve_direct reads bubbles, canes and rosette tags); implies unique + no-guess for the game's solver.
Readability: bubbles only on panes >= 1.2x median inner radius; canes only on borders >= 0.03 of the window; rosettes 3-6 panes incl. one roomy pane."""
import sys,json,random,os,math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from freeglass2 import solve, solve_direct
from autofill import tap_stats
from add_not import cands
QUOTA={2:{'not':(3,5,4)},3:{'canes':(5,8,6),'not':(2,3,2)},4:{'ros':(4,6,5),'canes':(2,3,2),'not':(1,3,2)}}   # type: (min, max, target)
def necessary_report(lv,S=None):
  sol=lv['sol'];nb=lv['nb'];K=len(lv['colors']);kw=dict(gift=lv.get('gift',[]),detail=lv.get('detail',[]),auto=lv.get('auto',[]))
  nt=lv.get('not',{}) or {};cn=lv.get('canes',[]) or [];rs=lv.get('ros',[]) or []
  f=lambda n,c,r:solve_direct(sol,nb,K,lv['start'],nots=n,canes=c,ros=r,**kw)
  bad=[('not',k) for k in nt if f({x:v for x,v in nt.items() if x!=k},cn,rs)==0]+[('cane',c) for c in cn if f(nt,[x for x in cn if x!=c],rs)==0]+[('ros',r['panes']) for r in rs if f(nt,cn,[x for x in rs if x is not r])==0]
  return bad
def main(cur,base,out,seed=0):
  lv=json.load(open(cur)); b0=json.load(open(base)); assert b0['sol']==lv['sol'] and len(b0['pieces'])==len(lv['pieces'])
  sol=lv['sol']; nb=lv['nb']; K=len(lv['colors']); gift=lv.get('gift',[]); det=lv.get('detail',[]); auto=list(lv.get('auto',[])); tier=lv.get('tier',2)
  Q=QUOTA[tier]; rnd=random.Random(int(seed)); start=list(b0['start']); lit0=len(start); auto0=len(auto)
  rin=[P['rin'] for P in lv['pieces']]; med=sorted(rin)[len(rin)//2]; cen=[tuple(P['pole']) for P in lv['pieces']]; Pt=[[tuple(x) for x in P['p']] for P in lv['pieces']]
  def shared(p,q):
    eb={frozenset((Pt[q][i],Pt[q][(i+1)%len(Pt[q])])) for i in range(len(Pt[q]))}
    return sum(math.dist(Pt[p][i],Pt[p][(i+1)%len(Pt[p])]) for i in range(len(Pt[p])) if frozenset((Pt[p][i],Pt[p][(i+1)%len(Pt[p])])) in eb)
  cpool=[(p,q) for p in range(len(sol)) for q in nb[p] if q>p and sol[p]!=sol[q] and shared(p,q)>=0.03]
  st={'not':{},'canes':[],'ros':[]}
  def S(starts,c=None,au=None):
    c=c or st; return solve_direct(sol,nb,K,starts,gift=gift,detail=det,auto=auto if au is None else au,nots=c['not'],canes=c['canes'],ros=c['ros'])
  def full(starts): return solve(sol,nb,K,starts,gift=gift,detail=det,auto=auto,nots=st['not'],canes=st['canes'],ros=st['ros'])
  def used(c): return set(starts_now)|set(gift)|set(det)|set(auto)|{x for r in c['ros'] for x in r['panes']}|{int(k) for k in c['not']}
  def rpool(ban):
    out=[];seen=set()
    for s0 in range(len(sol)):
      if s0 in ban: continue
      g=[s0]
      while len(g)<6:
        ext={q for x in g for q in nb[x] if q not in g and q not in ban}
        if not ext: break
        mx=sum(cen[x][0] for x in g)/len(g); my=sum(cen[x][1] for x in g)/len(g); g.append(min(ext,key=lambda q:math.dist(cen[q],(mx,my))))
        if len(g)>=3 and max(rin[x] for x in g)>=med:
          k=frozenset(g)
          if k not in seen: seen.add(k); out.append(sorted(g))
    return out
  def options(typ,c):
    if typ=='not':
      C=cands(sol,nb,K,used(c),3,rin); return [('not',(str(p),cs)) for p,cs in C.items() if str(p) not in c['not']]
    if typ=='canes': return [('canes',x) for x in cpool if x not in c['canes']]
    rp=rpool(used(c)); rnd.shuffle(rp); return [('ros',{'panes':g,'cols':sorted({sol[x] for x in g})}) for g in rp[:250]]
  def withc(c,o):
    n={'not':dict(c['not']),'canes':list(c['canes']),'ros':list(c['ros'])}; t,v=o
    if t=='not': n['not'][v[0]]=v[1]
    else: n[t].append(v)
    return n
  def count(c,t): return len(c[t])
  def below(c): return [t for t,(mn,mx,tg) in Q.items() if count(c,t)<tg]
  def room(c): return [t for t,(mn,mx,tg) in Q.items() if count(c,t)<mx]
  def patch(starts,c,types,budget=2):
    unk=S(starts,c)
    for _ in range(budget):
      if not unk: break
      best=None
      for t in types:
        for o in options(t,c):
          u=S(starts,withc(c,o))
          if best is None or u<best[0]: best=(u,o)
      if best is None or best[0]>=unk: break
      c=withc(c,best[1]); unk=best[0]
    return unk,c
  starts_now=start
  LITF={2:4,3:3,4:2}[tier]; AUTOF={2:0.25,3:0.12,4:0.0}[tier]; body=len(sol)-len(gift)-len(det)
  def prune():   # keep only necessary clues (adding a clue can make an older one redundant)
    while True:
      bad=necessary_report(dict(lv,start=starts_now,auto=auto,**{'not':st['not'],'canes':st['canes'],'ros':st['ros']}))
      if not bad: return
      typ,key=bad[0]
      if typ=='not': st['not'].pop(key,None)
      elif typ=='cane': st['canes']=[x for x in st['canes'] if x!=key]
      else: st['ros']=[x for x in st['ros'] if x['panes']!=key]
      print('  unneeded',typ,'dropped',flush=True)
  def hints():   # hints that may still be taken away, lit starts first, then auto panes
    h=[('start',x) for x in starts_now] if len(starts_now)>LITF else []
    if (len(auto)-1)>=AUTOF*body: h+=[('auto',x) for x in auto]
    return h
  def without(h):
    return ([x for x in starts_now if x!=h[1]],auto) if h[0]=='start' else (starts_now,[x for x in auto if x!=h[1]])
  if S(start): u,c=patch(start,st,room(st),20); assert u==0,'base not solvable'; st.update(c)
  # 0) build from scratch: a few weak, spread-out lit starts, then mechanic clues (types below quota first) bridge the gaps; a start is added only when no clue helps
  BUILD=os.environ.get('MF_BUILD')=='1'   # off by default: on these boards one start usually ignites the whole one-badge cascade, so building from scratch ends at 1 lit + 1 clue
  free_panes=[x for x in range(len(sol)) if x not in set(gift)|set(det)|set(auto)]
  cov={x:len(sol)-S([x],{'not':{},'canes':[],'ros':[]}) for x in free_panes}
  N=len(sol); vals=sorted(v for v in cov.values() if 1<v<N)   # a start that solves the whole level alone would make every clue pointless
  lo,hi=(vals[len(vals)//10],vals[len(vals)*2//5]) if vals else (1,1)
  weak=[x for x in free_panes if lo<=cov[x]<=hi] or [x for x in free_panes if cov[x]<N] or free_panes
  bstarts=[rnd.choice(weak)] if BUILD else list(starts_now)
  while BUILD and len(bstarts)<LITF: bstarts.append(max(weak,key=lambda x:(min(math.dist(cen[x],cen[y]) for y in bstarts),rnd.random())))
  if BUILD: starts_now=bstarts; st={'not':{},'canes':[],'ros':[]}
  unk=S(starts_now)
  while BUILD and unk:
    best=None
    for typ in (below(st) or room(st)):
      for o in options(typ,st):
        u=S(starts_now,withc(st,o))
        if best is None or u<best[0]: best=(u,o)
    if best and best[0]<unk: st=withc(st,best[1]); unk=best[0]; print('  build +',best[1][0],'->',unk,flush=True); continue
    cand=[x for x in free_panes if x not in starts_now and cov[x]<N] or [x for x in free_panes if x not in starts_now]
    bs=min(cand,key=lambda x:(S(starts_now+[x]),rnd.random())); starts_now=starts_now+[bs]; unk=S(starts_now); print('  build +start',bs,'->',unk,flush=True)
  if BUILD: prune()
  ch=BUILD
  while ch:
    ch=False
    for x in sorted(starts_now,key=lambda _:rnd.random()):
      ns=[y for y in starts_now if y!=x]
      if S(ns)==0: starts_now=ns; ch=True; print('  build -start',x,flush=True); break
  if BUILD: print('  built',{k:len(v) for k,v in st.items()},'lit',len(starts_now),flush=True)
  # 1) clues first, to quota, each paid for by taking away a hint (lit starts first)
  guard=0; fails=set(); use_auto=False
  while below(st) and guard<120:
    guard+=1; types=[t for t in below(st) if t not in fails]
    if not types:
      if not use_auto: use_auto=True; fails=set(); continue
      break
    typ=types[guard%len(types)]; H=hints()
    if not H: print('  no hints left to trade for',typ,flush=True); break
    if not use_auto and any(h[0]=='start' for h in H): H=[h for h in H if h[0]=='start']
    elif use_auto and any(h[0]=='auto' for h in H): H=[h for h in H if h[0]=='auto']
    sc=[]
    for h in (H if len(H)<=24 else rnd.sample(H,24)):
      ns,na=without(h); sc.append((solve_direct(sol,nb,K,ns,gift=gift,detail=det,auto=na,nots=st['not'],canes=st['canes'],ros=st['ros']),rnd.random(),h))
    if sc and all(x[0]==0 for x in sc):   # every hint is redundant: take one away (prefer starts) and look again
      h=sc[0][2]; starts_now,auto=without(h); print('  free',h,flush=True); continue
    sc=[x for x in sc if x[0]>0]; sc.sort(); done=False   # free hints are left for step 2: only a hint whose loss hurts can pay for a clue
    for u,_,h in sc[:12]:
      ns,na=without(h); sv=auto; auto=na
      opts=sorted(((S(ns,withc(st,o)),rnd.random(),o) for o in options(typ,st)),key=lambda x:x[:2])
      ok=None
      for u1,_,o in opts[:25]:      # single clue that solves and leaves every older clue necessary
        if u1: break
        c=withc(st,o)
        if not necessary_report(dict(lv,start=ns,auto=na,**{'not':c['not'],'canes':c['canes'],'ros':c['ros']})): ok=c; break
      if ok is None:                # else best pair, still all necessary
        for u1,_,o in opts[:8]:
          c1=withc(st,o); u2,c=patch(ns,c1,[typ],1)
          if u2==0 and not necessary_report(dict(lv,start=ns,auto=na,**{'not':c['not'],'canes':c['canes'],'ros':c['ros']})): ok=c; break
      auto=sv
      if ok is not None: starts_now,auto=ns,na; st.update(ok); done=True; fails=set(); use_auto=False; print('  ',h,'->',typ,{k:len(v) for k,v in st.items()},flush=True); break
    if not done: print('  could not trade a hint for',typ,'(auto)' if use_auto else '',flush=True); fails.add(typ)
  # 2) barely unique: take away every hint still removable (lit starts to the floor first, then auto to its floor); clues stay necessary (hint removal never makes a clue redundant)
  ch=True
  while ch:
    ch=False
    for h in sorted(hints(),key=lambda h:(h[0]!='start',rnd.random())):
      ns,na=without(h)
      if (h[0]=='start' and len(starts_now)<=LITF) or (h[0]=='auto' and len(auto)-1<AUTOF*body): continue
      if solve_direct(sol,nb,K,ns,gift=gift,detail=det,auto=na,nots=st['not'],canes=st['canes'],ros=st['ros'])==0: starts_now,auto=ns,na; ch=True; print('  drop',h,flush=True)
  prune()
  assert S(starts_now)==0 and full(starts_now)==0
  bad=necessary_report(dict(lv,start=starts_now,auto=auto,**{'not':st['not'],'canes':st['canes'],'ros':st['ros']}))
  lv['start']=starts_now; lv['auto']=sorted(auto)
  for key in ('not','canes','ros'):
    v=st[key]
    if key=='not': v={k:v[k] for k in sorted(v,key=int)}
    elif key=='canes': v=sorted([list(x) for x in v])
    else: v=sorted(v,key=lambda r:r['panes'][0])
    if v: lv[key]=v
    else: lv.pop(key,None)
  ts=tap_stats(sol,nb,K,starts_now,gift,det,lv['auto'],lv.get('not'),lv.get('canes'),lv.get('ros'))
  m=lv['metrics']; m.update(starts=len(starts_now),lit_share=round(len(starts_now)/body,4),auto=len(lv['auto']),auto_share=round(len(lv['auto'])/body,4),nots=len(lv.get('not',{})),canes=len(lv.get('canes',[])),ros=len(lv.get('ros',[])),clues_necessary=not bad,lit_before=lit0)
  for k in ('max_chain','mean_chain','max_depth','settle','taps','chains','stalls'): m[k]=ts[k]
  json.dump(lv,open(out,'w'))
  print('RESULT',lv['id'],'tier',tier,'bubbles',m['nots'],'canes',m['canes'],'ros',m['ros'],'lit',lit0,'->',len(starts_now),'auto',auto0,'->',len(lv['auto']),'%.1f%%'%(100*len(lv['auto'])/body),'chains',ts['mean_chain'],ts['max_chain'],'necessary',not bad,flush=True)
if __name__=='__main__': main(*sys.argv[1:5])
