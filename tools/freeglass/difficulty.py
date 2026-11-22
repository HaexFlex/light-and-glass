"""1–5 difficulty score from a one-badge player trace.

python3 tools/freeglass/difficulty.py levels/data/genlorikeet.json
python3 tools/freeglass/difficulty.py levels/data/gen*.json

The tracer plays like a person: at each step it takes a single-clue move (one lit
badge, no mechanic) when one exists, else a mechanic-assisted move (is-not / cane /
rosette), else a two-badge combination. Autos, gifts and detail panes cascade for
free. Lowest pane index wins ties, so the score is deterministic.

Five 0–1 ratings are averaged, then scaled so Lorikeet lands at 3 (floor 1, cap 5):
  decided   — how much of the window the player colours (share and count)
  hard      — share of those moves that need a mechanic or two clues
  stall     — longest run of steps with no single-clue move
  tightness — how little choice there is among easy moves
  mechanics — how many is-not bubbles, canes and rosettes sit on the glass
"""
import json, os, sys, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solver2 import line_poss

# Frozen Lorikeet raw (average of the five 0–1 ratings). Re-check if the tracer changes.
LORIKEET_RAW = 0.7418516932010185  # genlorikeet, frozen 2026-11-22
DECIDED_CAP = 140
HARD_FULL = 0.10
STALL_FULL = 6.0
EASY_SCALE = 6.0
MECH_FULL = 10.0

def _cascade(known, lit, nb, gift, det, auto, skip):
  ch = True
  while ch:
    ch = False
    for d in det:
      if d not in known and any(q in lit for q in nb[d]):
        known.add(d); ch = True
    for a in auto:
      if a not in lit and any(q in lit for q in nb[a]):
        lit.add(a); known.add(a); ch = True
    for q in list(known):
      if q not in skip and q not in lit:
        lit.add(q); ch = True

def _dom(q, T, known, sol, FULL, rc, ex, cp):
  if q in known:
    return {sol[q]}
  d = set(FULL)
  if 'ros' in T: d &= rc[q]
  if 'not' in T: d -= ex[q]
  if 'cane' in T: d -= {sol[r] for r in cp[q] if r in known}
  return d

def _all_forced(T, known, lit, sol, nb, K, FULL, rc, ex, cp, ros, skip):
  found = set(); N = len(sol)
  for p in lit:
    if all(q in known for q in nb[p]):
      continue
    cnt = [0] * K
    for q in nb[p]:
      cnt[sol[q]] += 1
    P = line_poss([_dom(q, T, known, sol, FULL, rc, ex, cp) for q in nb[p]], cnt)
    for i, q in enumerate(nb[p]):
      if q not in known and len(P[i]) == 1:
        found.add(q)
  if 'ros' in T:
    for r in ros:
      kc = {sol[p] for p in r['panes'] if p in known}
      unk = [p for p in r['panes'] if p not in known]
      for c in set(r['cols']) - kc:
        cand = [p for p in unk if c in _dom(p, T, known, sol, FULL, rc, ex, cp)]
        if len(cand) == 1:
          found.add(cand[0])
      for p in unk:
        if len(_dom(p, T, known, sol, FULL, rc, ex, cp)) == 1:
          found.add(p)
  if T:
    for q in range(N):
      if q not in known and q not in skip and len(_dom(q, T, known, sol, FULL, rc, ex, cp)) == 1:
        found.add(q)
  return found

def _two_badges(known, lit, sol, nb, K, FULL, rc, ex, cp):
  found = set(); C = {}
  for p in lit:
    if all(q in known for q in nb[p]):
      continue
    cnt = [0] * K
    for q in nb[p]:
      cnt[sol[q]] += 1
    P = line_poss([_dom(q, (), known, sol, FULL, rc, ex, cp) for q in nb[p]], cnt)
    C[p] = ({q: P[i] for i, q in enumerate(nb[p]) if q not in known}, cnt)
  for p, (cp_, cnt) in C.items():
    for r, (cr, _) in C.items():
      if r == p or not set(cp_) & set(cr):
        continue
      P = line_poss([{sol[q]} if q in known else cr.get(q, FULL) for q in nb[p]], cnt)
      for i, q in enumerate(nb[p]):
        if q not in known and len(P[i]) == 1:
          found.add(q)
  return found

def trace(lv):
  """Replay the level and return move counts plus the five rating ingredients."""
  sol = lv['sol']; nb = lv['nb']; K = len(lv['colors']); N = len(sol)
  FULL = set(range(K))
  gift = set(lv.get('gift', []) or []); det = set(lv.get('detail', []) or [])
  skip = gift | det; auto = set(lv.get('auto', []) or [])
  nots = lv.get('not', {}) or {}; canes = lv.get('canes', []) or []; ros = lv.get('ros', []) or []
  ex = [set() for _ in range(N)]
  for p, cs in nots.items():
    for q in nb[int(p)]:
      ex[q] |= set(cs)
  cp = [[] for _ in range(N)]
  for a, b in canes:
    cp[a].append(b); cp[b].append(a)
  rc = [set(FULL) for _ in range(N)]
  for r in ros:
    for p in r['panes']:
      rc[p] &= set(r['cols'])
  types = [t for t, v in (('not', nots), ('cane', canes), ('ros', ros)) if v]
  combos = [c for n in range(1, len(types) + 1) for c in itertools.combinations(types, n)]
  known = set(lv['start']) | gift; lit = set(lv['start'])
  _cascade(known, lit, nb, gift, det, auto, skip)
  kinds = []; easy_n = []; first = None
  while len(known | skip) < N:
    E = _all_forced((), known, lit, sol, nb, K, FULL, rc, ex, cp, ros, skip)
    easy_n.append(len(E))
    if E:
      kind = 'single'; q = min(E)
    else:
      q = None; kind = None
      for c in combos:
        F = _all_forced(c, known, lit, sol, nb, K, FULL, rc, ex, cp, ros, skip)
        if F:
          kind = '+'.join(c); q = min(F); break
      if q is None:
        F = _two_badges(known, lit, sol, nb, K, FULL, rc, ex, cp)
        if F:
          kind = 'combined'; q = min(F)
    if q is None:
      return dict(stuck=True, id=lv.get('id'), known=len(known), kinds=kinds, easy_n=easy_n)
    if first is None:
      first = (q, kind)
    kinds.append(kind)
    known.add(q)
    _cascade(known, lit, nb, gift, det, auto, skip)
  run = best = 0
  for k in kinds:
    if k == 'single':
      run = 0
    else:
      run += 1; best = max(best, run)
  counts = {}
  for k in kinds:
    counts[k] = counts.get(k, 0) + 1
  decided = len(kinds)
  hard = sum(1 for k in kinds if k != 'single')
  body = N - len(gift) - len(det)
  mean_easy = (sum(easy_n) / len(easy_n)) if easy_n else 0.0
  return dict(
    stuck=False, id=lv.get('id'), name=lv.get('name'), tier=lv.get('tier'),
    panes=N, body=body, start=len(lv['start']), auto=len(auto),
    decided=decided, decided_share=decided / body if body else 0.0,
    kinds=counts, hard=hard, hard_share=hard / decided if decided else 0.0,
    longest_stall=best, mean_easy=mean_easy,
    mech_items=len(nots) + len(canes) + len(ros), mech_types=len(types),
    first=first, easy_n=easy_n,
  )

def ratings(t):
  """Five 0–1 ratings from a trace() result (or a stuck result is rejected)."""
  if t.get('stuck'):
    raise ValueError('trace is stuck; no score')
  D = 0.5 * t['decided_share'] + 0.5 * min(t['decided'] / DECIDED_CAP, 1.0)
  H = min(t['hard_share'] / HARD_FULL, 1.0)
  S = min(t['longest_stall'] / STALL_FULL, 1.0)
  T = 1.0 / (1.0 + t['mean_easy'] / EASY_SCALE)
  M = min((t['mech_items'] + 2 * t['mech_types']) / MECH_FULL, 1.0)
  raw = (D + H + S + T + M) / 5.0
  return dict(decided=D, hard=H, stall=S, tightness=T, mechanics=M, raw=raw)

def score_from_raw(raw, lorikeet_raw=None):
  cal = LORIKEET_RAW if lorikeet_raw is None else lorikeet_raw
  if not cal:
    raise RuntimeError('LORIKEET_RAW is not set')
  s = 1.0 + 2.0 * raw / cal
  s = max(1.0, min(5.0, round(s, 1)))
  return s

def analyse(lv):
  t = trace(lv)
  if t.get('stuck'):
    return t
  r = ratings(t)
  t = dict(t)
  t['ratings'] = {k: round(r[k], 4) for k in r}
  t['score'] = score_from_raw(r['raw'])
  t['decided_share'] = round(t['decided_share'], 4)
  t['hard_share'] = round(t['hard_share'], 4)
  t['mean_easy'] = round(t['mean_easy'], 2)
  t.pop('easy_n', None)
  return t

def _print_row(t, hdr=False):
  cols = [
    ('id', 16, lambda t: t.get('id') or ''),
    ('score', 5, lambda t: '—' if t.get('stuck') else f"{t['score']:.1f}"),
    ('tier', 4, lambda t: str(t.get('tier') or '')),
    ('decided', 8, lambda t: f"{t.get('decided','')}"),
    ('share', 6, lambda t: f"{t.get('decided_share',0):.3f}" if not t.get('stuck') else ''),
    ('hard', 6, lambda t: f"{t.get('hard_share',0):.3f}" if not t.get('stuck') else ''),
    ('stall', 5, lambda t: str(t.get('longest_stall','') if not t.get('stuck') else '')),
    ('easy', 6, lambda t: f"{t.get('mean_easy',0):.2f}" if not t.get('stuck') else ''),
    ('mech', 8, lambda t: f"{t.get('mech_items',0)}/{t.get('mech_types',0)}" if not t.get('stuck') else ''),
    ('raw', 6, lambda t: f"{t['ratings']['raw']:.3f}" if not t.get('stuck') else ''),
  ]
  if hdr:
    print(' '.join(n.upper().ljust(w) for n, w, _ in cols))
  print(' '.join(fn(t).ljust(w) for n, w, fn in cols))

def main(argv=None):
  argv = list(sys.argv[1:] if argv is None else argv)
  as_json = False
  if '--json' in argv:
    as_json = True; argv.remove('--json')
  if not argv:
    sys.exit('usage: difficulty.py [--json] level.json ...')
  rows = []
  for f in argv:
    lv = json.load(open(f))
    rows.append(analyse(lv))
  if as_json:
    print(json.dumps(rows, indent=2))
    return
  for i, t in enumerate(rows):
    _print_row(t, hdr=(i == 0))
    if t.get('stuck'):
      print('  stuck after', t.get('known'), 'known')

if __name__ == '__main__':
  main()
