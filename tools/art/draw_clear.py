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
def REL(d,cx,cy,rx,ry,ang,fill):
  pts=[];a=math.radians(ang)
  for i in range(0,360,4):
    u=rx*math.cos(math.radians(i));v=ry*math.sin(math.radians(i));pts.append((cx+u*math.cos(a)-v*math.sin(a),cy+u*math.sin(a)+v*math.cos(a)))
  d.polygon(P(pts),fill=fill)
def teapot(out):
  BG=(110,184,226);POT=(214,70,140);CRM=(255,243,224);GLD=(245,184,40);GRN=(56,160,84)
  im,d=new(BG)
  # table line + flowers with leaves
  d.rectangle([0,640*S,N,N],fill=(70,140,196))
  for fx,fy,rot in ((110,560,0),(722,590,20)):
    d.line([(fx*S,(fy+20)*S),(fx*S,700*S)],fill=GRN,width=14*S)
    REL(d,fx-50,fy+120,55,22,-35,GRN);REL(d,fx+50,fy+150,55,22,35,GRN)
    for k in range(6):
      a=math.radians(rot+k*60);REL(d,fx+62*math.cos(a),fy+62*math.sin(a),42,26,rot+k*60,CRM)
    E(d,fx,fy,34,34,GLD)
  # teapot: body, lid, knob, spout, handle
  d.arc([480*S,335*S,725*S,575*S],start=0,end=360,fill=POT,width=40*S)
  d.polygon(P([(215,430),(205,520),(110,400),(80,330),(125,315)]),fill=POT)
  E(d,102,322,28,28,POT)
  E(d,400,470,215,170,POT)
  E(d,400,300,125,48,POT);d.rectangle([275*S,296*S,525*S,336*S],fill=POT)
  d.rectangle([265*S,326*S,535*S,346*S],fill=GLD)
  E(d,400,242,34,34,GLD)
  for cx,cy in ((330,430),(430,410),(500,480),(300,520),(400,540),(480,360)): E(d,cx,cy,27,27,CRM)
  im.resize((800,800),Image.LANCZOS).save(os.path.join(out,'teapot.png'))
def hummingbird(out):
  BG=(176,200,246);TEAL=(18,160,140);DARK=(10,92,100);RED=(228,36,64);CRM=(250,246,232);BLK=(34,30,44);PINK=(255,92,160);YEL=(255,206,40);GRN=(70,170,76)
  im,d=new(BG)
  # flower (hibiscus) lower right with stem and leaves
  d.line([(600*S,560*S),(650*S,780*S)],fill=GRN,width=16*S);REL(d,700,700,70,26,-30,GRN);REL(d,560,700,70,26,200,GRN)
  for k in range(5):
    a=math.radians(k*72-20);REL(d,600+70*math.cos(a),540+70*math.sin(a),68,46,k*72-20,PINK)
  E(d,600,540,38,38,YEL)
  # tail + wings (behind body)
  d.polygon(P([(250,430),(90,640),(150,660),(230,610),(290,520)]),fill=DARK)
  d.polygon(P([(330,340),(160,90),(110,130),(150,220),(260,340)]),fill=DARK)
  d.polygon(P([(300,350),(70,230),(60,290),(140,360),(250,410)]),fill=TEAL)
  # body, belly, head, throat
  REL(d,330,400,120,66,48,TEAL);REL(d,360,430,70,40,48,CRM)
  E(d,415,310,58,56,TEAL);REL(d,430,350,34,24,40,RED)
  # long thin beak toward the flower
  d.polygon(P([(452,300),(570,488),(548,502),(440,345)]),fill=BLK)
  E(d,430,298,13,13,CRM);E(d,433,298,6,6,BLK)
  im.resize((800,800),Image.LANCZOS).save(os.path.join(out,'hummingbird.png'))
def toadstool(out):
  BG=(140,200,245);GRASS=(58,160,84);CAP=(222,40,52);WHT=(255,255,255);STEM=(240,186,110)
  im,d=new(BG)
  E(d,400,860,520,230,GRASS)
  d.polygon(P([(330,390),(470,390),(500,700),(300,700)]),fill=STEM)
  import math
  pts=[(400+270*math.cos(math.radians(a)),385-215*math.sin(math.radians(a))) for a in range(0,181,3)]
  pts+=[(400+270*math.cos(math.radians(a)),385-50*math.sin(math.radians(a))) for a in range(180,361,3)]
  d.polygon(P(pts),fill=CAP)
  for cx,cy,rx,ry in ((400,255,58,42),(255,330,44,32),(548,335,48,34)): E(d,cx,cy,rx,ry,WHT)
  im.resize((800,800),Image.LANCZOS).save(os.path.join(out,'toadstool.png'))
def moonowl(out):
  BG=(26,38,104);MOON=(190,222,255);BRN=(160,104,56);DBR=(104,62,34);CRM=(246,224,180);YEL=(255,186,8);BLK=(18,16,24);ORG=(240,126,32);GRN=(60,160,80)
  im,d=new(BG)
  E(d,665,160,92,92,MOON);E(d,655,140,100,100,BG) if False else None
  # branch + leaves
  d.polygon(P([(0,640),(800,610),(800,668),(0,700)]),fill=DBR)
  pass
  # ear tufts, body, wings, head
  d.polygon(P([(255,200),(290,95),(345,180)]),fill=BRN);d.polygon(P([(545,200),(510,95),(455,180)]),fill=BRN)
  E(d,400,480,175,200,BRN)
  REL(d,252,490,62,150,12,DBR);REL(d,548,490,62,150,-12,DBR)
  E(d,400,305,160,125,BRN)
  E(d,400,520,105,150,CRM)
  # face
  E(d,335,305,70,68,CRM);E(d,465,305,70,68,CRM)
  E(d,335,305,44,44,YEL);E(d,465,305,44,44,YEL);E(d,335,305,20,20,BLK);E(d,465,305,20,20,BLK)
  d.polygon(P([(400,330),(372,375),(428,375)]),fill=ORG)
  # feet
  for fx in (350,450): E(d,fx,665,38,26,ORG)
  im.resize((800,800),Image.LANCZOS).save(os.path.join(out,'moonowl.png'))
if __name__=='__main__':
  o=sys.argv[1];os.makedirs(o,exist_ok=True);cupcake(o);ladybird(o);teapot(o);hummingbird(o);toadstool(o);moonowl(o)
