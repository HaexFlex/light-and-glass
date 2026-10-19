#!/usr/bin/env python3
"""Run mechfirst.py over several seeds and keep the best result: quotas met first (all clues necessary), then most clues, then fewest lit.
usage: mfbest.py cur.json base.json out.json [nseeds]"""
import sys,subprocess,json,re,shutil,os
sys.path.insert(0,os.path.dirname(__file__))
from mechfirst import QUOTA
cur,base,out=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 8
best=None
for seed in range(n):
  o=f'{out}.s{seed}'
  r=subprocess.run([sys.executable,os.path.join(os.path.dirname(__file__),'mechfirst.py'),cur,base,o,str(seed)],capture_output=True,text=True,timeout=3000)
  line=[l for l in r.stdout.splitlines() if l.startswith('RESULT')]
  if not line: print('seed',seed,'failed',r.stderr[-300:]); continue
  lv=json.load(open(o)); m=lv['metrics']; q=QUOTA[lv['tier']]
  cnt={'not':m['nots'],'canes':m['canes'],'ros':m['ros']}
  short=sum(max(0,mn-cnt[t]) for t,(mn,mx,tg) in q.items())
  key=(not m['clues_necessary'],short,-sum(cnt.values()),len(lv['start']),seed)
  print('seed',seed,line[0][7:],'short',short,flush=True)
  if best is None or key<best[0]: best=(key,o,line[0])
shutil.copy(best[1],out); print('BEST',best[2])
