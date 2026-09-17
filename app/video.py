import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent.parent
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def wrap(text, width=26):
    words=text.split(); lines=[]; cur=""
    for w in words:
        if len(cur)+len(w)+1 > width:
            lines.append(cur); cur=w
        else: cur=(cur+" "+w).strip()
    if cur: lines.append(cur)
    return lines

def make_cards(lines, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    font=ImageFont.truetype(FONT, 64); small=ImageFont.truetype(FONT, 28)
    paths=[]
    for i,txt in enumerate(lines or ["NOIR//NULL"]):
        img=Image.new("RGB",(1080,1920),(5,5,7)); d=ImageDraw.Draw(img)
        d.text((70,100),"NOIR//NULL",font=small,fill=(0,229,255))
        y=760
        for line in wrap(txt,24):
            b=d.textbbox((0,0),line,font=font)
            d.text(((1080-(b[2]-b[0]))/2,y),line,font=font,fill=(245,245,245)); y+=82
        p=outdir/f"scene_{i:02d}.png"; img.save(p); paths.append(p)
    return paths

def make_srt(lines,dur):
    def ts(x):
        h=int(x//3600); m=int((x%3600)//60); s=int(x%60); ms=int((x-int(x))*1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    out=[]
    for i,t in enumerate(lines):
        out.append(f"{i+1}\n{ts(i*dur)} --> {ts((i+1)*dur)}\n{t}\n")
    return "\n".join(out)

def render(lines, output, audio=None):
    output = Path(output)
    work=ROOT/"renders"/"frames"/output.stem; frames=make_cards(lines,work)
    dur=max(2.5,min(5.0,55/max(1,len(frames))))
    concat=work/"concat.txt"
    concat.write_text("\n".join([f"file '{p.as_posix()}'\nduration {dur}" for p in frames])+f"\nfile '{frames[-1].as_posix()}'\n")
    srt=work/"captions.srt"; srt.write_text(make_srt(lines,dur),encoding="utf-8")
    vf=f"subtitles={srt.as_posix()}:force_style='FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00101010&,Outline=3,Alignment=2,MarginV=140'"
    cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat)]
    if audio: cmd += ["-i",str(audio)]
    cmd += ["-vf",vf,"-r","30","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart"]
    cmd += ["-c:a","aac","-b:a","128k","-shortest"] if audio else ["-an"]
    cmd += [str(output)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode!=0: raise RuntimeError(p.stderr[-3000:])
    return output
