"""Start-ease for every playable fresh level (python, no browser): initial state = lit starts + gift + designed autofill applied.
 - lit starts form ONE tight cluster (connected when panes up to 2 adjacency steps apart count as linked);
 - first forced deduction depth (clues combined, see tools/freeglass/startease.py): Clear = 1 with >=3 such moves; Tinted <= 2; Stained/Jewel >= 1 forced move;
 - LOCAL start (Haex: "how am I supposed to know where to start if it is not next to a lit pane?"): a forced move on a pane DIRECTLY touching the lit cluster
   (cluster = lit starts + autofilled panes touching them), using only that cluster's badges and clues on/touching the cluster; Clear needs >=3 such one-badge moves, other tiers depth <= 2."""
import os,sys,json
R=os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."));sys.path.insert(0,os.path.join(R,'tools/freeglass'))
from startease import ease
ok={};rows=[]
for l in json.load(open(os.path.join(R,'levels/manifest.json'))):
  if l.get('set')!='fresh': continue
  lv=json.load(open(os.path.join(R,l['file'])));nb=lv['nb'];S=lv['start'];t=lv.get('tier',3)
  N2=[set(nb[x])|{z for y in nb[x] for z in nb[y]} for x in range(len(nb))]
  seen={S[0]};st=[S[0]]
  while st:
    x=st.pop()
    for y in S:
      if y not in seen and y in N2[x]: seen.add(y);st.append(y)
  e=ease(lv);L=ease(lv,True);e.update({k:v for k,v in L.items() if k!='cl'});i=l['id']
  ok[i+"_one_tight_lit_cluster"]=len(seen)==len(set(S))
  ok[i+"_first_move_tier_target"]=(L['ld']==1 and L['ln1']>=3) if t==1 else L['ld'] in (1,2)
  ok[i+"_first_move_adjacent_to_cluster"]=L['dist']==1
  rows.append((i,t,e))
for r in rows: print(r[0],r[1],r[2])
print(json.dumps(ok,indent=1));print("FAILED:",[k for k,v in ok.items() if not v]);sys.exit(1 if any(not v for v in ok.values()) else 0)
