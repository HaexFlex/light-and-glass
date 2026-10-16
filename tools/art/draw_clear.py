"""Hand-designed flat illustrations for Clear-tier levels (drawn with PIL shapes, 5 flat colours, plain contrasting background).
usage: draw_clear.py <outdir>  -> cupcake.png, ladybird.png"""
import sys,os,math
from PIL import Image,ImageDraw
S=4;N=800*S
def new(bg):
  im=Image.new('RGB',(N,N),bg);return im,ImageDraw.Draw(im)
def P(pts): return [(x*S,y*S) for x,y in pts]
def E(d,cx,cy,rx,ry,fill): d.ellipse([(cx-rx)*S,(cy-ry)*S,(cx+rx)*S,(cy+ry)*S],fill=fill)
def cupcake(out):
  BG=(70,185,176);PINK=(245,130,170);CREAM=(255,236,214);ORG=(228,128,56);RED=(214,30,60)
  im,d=new(BG)
  # wrapper (trapezoid) with cream stripes
  d.polygon(P([(215,470),(585,470),(530,730),(270,730)]),fill=ORG)
  for x0,x1 in ((300,325),(385,415),(475,500)):
    d.polygon(P([(x0+(1-0)*0,470),(x1,470),(x1-12+((x0+x1)/2-400)*-0.05,730),(x0-12+((x0+x1)/2-400)*-0.05+12,730)]),fill=CREAM)
  # frosting: three swirl tiers
  E(d,400,455,225,70,PINK)
  E(d,400,385,175,65,PINK);E(d,400,320,120,58,PINK);E(d,400,262,66,50,PINK)
  # cream swirl highlights
  for cy,rx in ((455,185),(385,140),(320,92)):
    d.arc([(400-rx)*S,(cy-34)*S,(400+rx)*S,(cy+40)*S],start=20,end=160,fill=CREAM,width=16*S)
  # cherry
  E(d,400,205,46,46,RED);d.polygon(P([(404,170),(425,98),(440,100),(418,172)]),fill=(70,140,60) if False else RED)
  E(d,386,192,12,12,CREAM)
  im.resize((800,800),Image.LANCZOS).save(os.path.join(out,'cupcake.png'))
def ladybird(out):
  BG=(255,238,170);LEAF=(52,170,80);VEIN=(170,230,110);RED=(224,40,44);BLK=(24,24,32)
  im,d=new(BG)
  # leaf (pointed oval) with vein
  leaf=[]
  for i in range(0,181,4):
    a=math.radians(i);leaf.append((400+330*math.cos(a)*1.0,430-210*math.sin(a)*(1 if True else 1)))
  top=[(400+340*math.cos(math.radians(a)),440-230*math.sin(math.radians(a))) for a in range(0,181,5)]
  bot=[(400+340*math.cos(math.radians(a)),440-230*math.sin(math.radians(a))) for a in range(180,361,5)]
  d.polygon(P(top+bot),fill=LEAF)
  d.polygon(P([(60,440),(120,420),(740,430),(740,452),(120,462)]),fill=VEIN)
  for sx in (-1,1):
    for k in range(4):
      x=240+k*110;d.polygon(P([(x,440),(x+30,440),(x+95,440+sx*150),(x+60,440+sx*158)]),fill=VEIN)
  # ladybird body
  E(d,400,420,150,160,RED)
  d.rectangle([396*S,262*S,404*S,580*S],fill=BLK)
  E(d,400,262,95,72,BLK)
  E(d,370,250,22,22,BG);E(d,430,250,22,22,BG)
  E(d,370,252,10,10,BLK);E(d,430,252,10,10,BLK)
  for cx,cy,r in ((330,370,34),(470,370,34),(315,470,30),(485,470,30),(360,545,24),(440,545,24)): E(d,cx,cy,r,r,BLK)
  # re-draw midline over spots (visual), then antennae
  d.line([(370*S,200*S),(330*S,140*S)],fill=BLK,width=9*S);d.line([(430*S,200*S),(470*S,140*S)],fill=BLK,width=9*S)
  E(d,328,138,13,13,BLK);E(d,472,138,13,13,BLK)
  im.resize((800,800),Image.LANCZOS).save(os.path.join(out,'ladybird.png'))
if __name__=='__main__':
  o=sys.argv[1];os.makedirs(o,exist_ok=True);cupcake(o);ladybird(o)
