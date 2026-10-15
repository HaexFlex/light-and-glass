"""Find permissively licensed photos on Wikimedia Commons (CC0 / public domain / CC-BY) and download a working copy.
  python commons.py search "red fox snow" [n]   -> prints candidates (title, licence, size)
  python commons.py get "File:Name.jpg" out.jpg [width]
Attribution goes into levels/source/CREDITS.md."""
import sys,json,urllib.request,urllib.parse,re
API="https://commons.wikimedia.org/w/api.php"
UA={"User-Agent":"light-and-glass-levels/1.0 (puzzle game level sources)"}
def api(**kw):
  kw["format"]="json";r=urllib.request.Request(API+"?"+urllib.parse.urlencode(kw),headers=UA)
  return json.load(urllib.request.urlopen(r,timeout=30))
OK=re.compile(r"^(CC0|Public domain|PD|CC BY \d|CC-BY \d|CC BY-SA|Attribution)",re.I)
def search(q,n=8,share=False):
  d=api(action="query",generator="search",gsrsearch="filetype:bitmap "+q,gsrnamespace=6,gsrlimit=30,prop="imageinfo",iiprop="url|size|extmetadata|mime",iiurlwidth=500)
  out=[]
  for p in sorted(d.get("query",{}).get("pages",{}).values(),key=lambda p:p.get("index",0)):
    ii=p["imageinfo"][0];m=ii.get("extmetadata",{});lic=m.get("LicenseShortName",{}).get("value","?")
    if ii["mime"]!="image/jpeg" or ii["width"]<1200: continue
    if re.search(r"SA",lic) and not share: continue
    if not OK.match(lic): continue
    out.append(dict(title=p["title"],lic=lic,w=ii["width"],h=ii["height"],thumb=ii["thumburl"],artist=re.sub("<[^>]+>","",m.get("Artist",{}).get("value","?"))[:60]))
    if len(out)>=n: break
  return out
def get(title,out,width=1600):
  d=api(action="query",titles=title,prop="imageinfo",iiprop="url",iiurlwidth=width)
  u=list(d["query"]["pages"].values())[0]["imageinfo"][0]["thumburl"]
  open(out,"wb").write(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read())
if __name__=="__main__":
  if sys.argv[1]=="search":
    for c in search(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 8): print(c["title"],"|",c["lic"],"|",c["w"],c["h"],"|",c["artist"])
  else: get(sys.argv[2],sys.argv[3],int(sys.argv[4]) if len(sys.argv)>4 else 1600)
