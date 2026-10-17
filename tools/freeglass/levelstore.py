"""Per-level storage: levels/data/<id>.json (one level each, same fields as the old levels_free.json entries) + levels/manifest.json
(small index used by the menu, cards and rewards: id, name, tier, panes, ncolors, nstart, ngift, aspect, fp, file, bytes).
The manifest order is the menu/test index order (LEVELS[i]); new levels are appended.
usage: python3 levelstore.py rebuild        # regenerate manifest.json from levels/data (fingerprints via node, same function as the game)
       python3 levelstore.py add out.json [--tier N] [--id ID] # copy a raster output into levels/data and rebuild the manifest"""
import json, os, subprocess, sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')); DATA=os.path.join(ROOT,'levels/data'); MAN=os.path.join(ROOT,'levels/manifest.json')
def dump(o): return json.dumps(o,separators=(',',':'))
def manifest(): return json.load(open(MAN))
def load(lid): return json.load(open(os.path.join(DATA,lid+'.json')))
def load_all(): return [load(m['id']) for m in manifest()]
def save(lv):
  os.makedirs(DATA,exist_ok=True); open(os.path.join(DATA,lv['id']+'.json'),'w').write(dump(lv))
def fingerprints(ids):
  out=subprocess.run(['node',os.path.join(ROOT,'tools/freeglass/levelfp.js')]+[os.path.join(DATA,i+'.json') for i in ids],capture_output=True,text=True,check=True).stdout
  return json.loads(out)
def rebuild(order=None):
  if order is None:
    order=[m['id'] for m in manifest()] if os.path.exists(MAN) else []
  have=sorted(f[:-5] for f in os.listdir(DATA) if f.endswith('.json'))
  order=[i for i in order if i in have]+[i for i in have if i not in order]
  fps=fingerprints(order); M=[]
  for i in order:
    p=os.path.join(DATA,i+'.json'); lv=json.load(open(p))
    M.append(dict(id=i,name=lv['name'],mode=lv.get('mode','free'),tier=lv.get('tier',3),panes=len(lv['pieces']),ncolors=len(lv['colors']),nstart=len(lv['start']),ngift=len(lv.get('gift',[])),
                  aspect=lv.get('aspect',1),fp=fps[i],file='levels/data/%s.json'%i,bytes=os.path.getsize(p)))
  open(MAN,'w').write(json.dumps(M,separators=(',',':'),indent=None).replace('},{','},\n{')+'\n'); return M
def build_page(outdir,extras=()):
  """Temporary playable copy for candidate sheets/tests: index.html + levels/data in outdir with extra (unpublished) levels appended to the manifest.
  Serve or open outdir/index.html; extra level k is LEVELS[len(manifest)+k]."""
  import shutil
  d=os.path.join(outdir,'levels/data'); shutil.rmtree(os.path.join(outdir,'levels'),ignore_errors=True); os.makedirs(d)
  for m in manifest(): os.symlink(os.path.join(DATA,m['id']+'.json'),os.path.join(d,m['id']+'.json'))
  for lv in extras: open(os.path.join(d,lv['id']+'.json'),'w').write(dump(lv))
  ids=[m['id'] for m in manifest()]+[lv['id'] for lv in extras]
  out=subprocess.run(['node',os.path.join(ROOT,'tools/freeglass/levelfp.js')]+[os.path.join(d,i+'.json') for i in ids],capture_output=True,text=True,check=True).stdout; fps=json.loads(out)
  M=[]
  for i in ids:
    lv=json.load(open(os.path.join(d,i+'.json')))
    M.append(dict(id=i,name=lv['name'],mode=lv.get('mode','free'),tier=lv.get('tier',3),panes=len(lv['pieces']),ncolors=len(lv['colors']),nstart=len(lv['start']),ngift=len(lv.get('gift',[])),fp=fps[i],file='levels/data/%s.json'%i))
  open(os.path.join(outdir,'index.html'),'w').write(open(os.path.join(ROOT,'src/template.html')).read().replace('__MANIFEST__',json.dumps(M,separators=(',',':'))))
  return M
if __name__=='__main__':
  c=sys.argv[1] if len(sys.argv)>1 else 'rebuild'
  if c=='add':
    lv=json.load(open(sys.argv[2])); a=sys.argv
    if '--tier' in a: lv['tier']=int(a[a.index('--tier')+1])
    if '--id' in a: lv['id']=a[a.index('--id')+1]
    save(lv)
  M=rebuild(); print(len(M),'levels,',sum(m['bytes'] for m in M),'bytes of level data')
