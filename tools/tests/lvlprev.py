"""quick flat preview of a level json: coloured panes with dark lead lines.  usage: lvlprev.py level.json out.png [width]"""
import sys,json
from PIL import Image,ImageDraw
lv=json.load(open(sys.argv[1])); W=int(sys.argv[3]) if len(sys.argv)>3 else 1200; H=round(W/lv['aspect'])
im=Image.new('RGB',(W,H),(30,25,20)); d=ImageDraw.Draw(im)
for i,p in enumerate(lv['pieces']):
  pts=[(x*W,(1/lv['aspect']-y)*W) for x,y in p['p']]; c=lv['colors'][lv['sol'][i]]
  d.polygon(pts,fill=c,outline=(40,28,18))
  d.line(pts+[pts[0]],fill=(40,28,18),width=3)
im.save(sys.argv[2])
