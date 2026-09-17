from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent.parent
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def ft(n,b=True): return ImageFont.truetype(FONT if b else REG,n)
def wrap(t,n):
    out=[]; cur=""
    for w in t.split():
        if len(cur)+len(w)+1>n: out.append(cur); cur=w
        else: cur=(cur+" "+w).strip()
    if cur: out.append(cur)
    return out
def make_thumbnail(title,topic,outpath):
    im=Image.new("RGB",(1280,720),(7,8,12)); d=ImageDraw.Draw(im)
    for x in range(0,1280,80): d.line((x,0,x,720),fill=(22,25,32))
    for y in range(0,720,80): d.line((0,y,1280,y),fill=(22,25,32))
    v=sum(map(ord,topic))%3; cx=1030 if v!=1 else 250
    d.ellipse((cx-190,170,cx+190,550),outline=(0,180,215),width=5)
    d.text((55,42),"NOIR//NULL",font=ft(30),fill=(0,220,245))
    x=65 if v!=1 else 500; y=150 if v!=2 else 95
    for line in wrap(title.upper(),21)[:4]:
        d.text((x,y),line,font=ft(62),fill=(245,245,245),stroke_width=2,stroke_fill=(0,0,0)); y+=72
    d.text((65,650),"FLORΞXIA  •  EXPLAINED",font=ft(22,False),fill=(150,150,160))
    p=Path(outpath); p.parent.mkdir(parents=True,exist_ok=True); im.save(p,quality=94); return p
def make_banner(outpath,channel="NOIR//NULL"):
    im=Image.new("RGB",(2560,1440),(5,6,9)); d=ImageDraw.Draw(im)
    for x in range(0,2560,128): d.line((x,0,x,1440),fill=(18,21,28),width=2)
    for y in range(0,1440,128): d.line((0,y,2560,y),fill=(18,21,28),width=2)
    d.ellipse((1830,360,2370,900),outline=(0,190,220),width=8)
    d.text((180,520),channel,font=ft(125),fill=(245,245,245))
    d.text((188,675),"THE INTERNET, EXPLAINED DIFFERENTLY",font=ft(42,False),fill=(130,220,235))
    p=Path(outpath); p.parent.mkdir(parents=True,exist_ok=True); im.save(p,quality=95); return p
