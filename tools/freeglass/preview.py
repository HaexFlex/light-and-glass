import json,sys
from PIL import Image,ImageDraw
fs=sys.argv[1:]; S=300; im=Image.new('RGB',(S*len(fs),S+0),(20,17,15))
for k,f in enumerate(fs):
  lv=json.load(open(f)); d=ImageDraw.Draw(im)
  for i,P in enumerate(lv['pieces']):
    pts=[(k*S+x*S,S-y*S*1) for x,y in P['p']]  # flip back upright
    d.polygon(pts,fill=lv['colors'][lv['sol'][i]],outline=(30,20,10))
    if i in lv['start']: d.ellipse([k*S+P['pole'][0]*S-4,S-P['pole'][1]*S-4,k*S+P['pole'][0]*S+4,S-P['pole'][1]*S+4],outline=(255,255,255))
im.save('/tmp/prev.png')
