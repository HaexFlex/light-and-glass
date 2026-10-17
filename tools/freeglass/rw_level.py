"""rw_level.py ID [--no-split] [--merge A,B] [--lit S] [--auto S]: rework one level in levels/data (split thin panes, optional colour merge, local starts + small auto clusters), write it back."""
import sys, json, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(HERE,'../../levels/data')
def main():
  a=sys.argv; lid=a[1]; src=os.path.join(D,lid+'.json'); cur=f'/tmp/rw_{lid}_0.json'; lv=json.load(open(src))
  if '--merge' in a:
    x,y=[int(v) for v in a[a.index('--merge')+1].split(',')]   # merge colour y into x
    import colorsys
    cx=lv['colors'][x]; cy=lv['colors'][y]; mix='#'+''.join('%02x'%round((int(cx[j:j+2],16)+int(cy[j:j+2],16))/2) for j in (1,3,5)); lv['colors'][x]=mix
    lv['sol']=[x if s==y else s for s in lv['sol']]; keep=[k for k in range(len(lv['colors'])) if k!=y]; mp={k:i for i,k in enumerate(keep)}
    lv['sol']=[mp[s] for s in lv['sol']]; lv['colors']=[lv['colors'][k] for k in keep]; lv['cnames']=[lv['cnames'][k] for k in keep]
    lv['metrics']['colours']=len(lv['colors'])
  json.dump(lv,open(cur,'w'))
  if '--no-split' not in a:
    subprocess.run(['python3',os.path.join(HERE,'split_thin.py'),cur,f'/tmp/rw_{lid}_1.json','3.0'],check=True); cur=f'/tmp/rw_{lid}_1.json'
  extra=[v for k in ('--lit','--auto','--group','--seeds') if k in a for v in (k,a[a.index(k)+1])]
  subprocess.run(['python3',os.path.join(HERE,'rework.py'),cur,f'/tmp/rw_{lid}_2.json']+extra,check=True)
  subprocess.run(['python3',os.path.join(HERE,'levelstore.py'),'add',f'/tmp/rw_{lid}_2.json'],check=True)
  subprocess.run(['python3',os.path.join(HERE,'validate_json.py'),os.path.join(D,lid+'.json')],check=True)
main()
