"""Render original ANOMALIA’Z PRIGIMALIA raster assets and Windows icons.
Source material is generated here, without modifying third-party asset packs.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64, hashlib, math

ROOT=Path(__file__).resolve().parents[1]
GOLD=(210,180,130)
CREAM=(237,234,226)
DARK=(12,17,22)

def font(size):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "C:/Windows/Fonts/arialbd.ttf",
                 "/Library/Fonts/Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name,size)
        except OSError:
            continue
    return ImageFont.load_default()

def center_text(d,y,content,size,fill,width,spacing=0):
    ft=font(size)
    box=d.textbbox((0,0),content,font=ft,stroke_width=0)
    text_w=box[2]-box[0]
    d.text(((width-text_w)/2,y),content,font=ft,fill=fill)

def symbol(size):
    im=Image.new("RGB",(size,size),DARK)
    d=ImageDraw.Draw(im)
    for i in range(1,14):
        inset=i*size/64
        intensity=int(20+40*(1-i/14))
        d.rounded_rectangle((inset,inset,size-inset,size-inset),
            radius=size*.11,outline=(intensity,intensity+10,intensity+14),width=2)
    k=size/700
    hexagon=[(350,76),(581,200),(581,470),(350,610),(119,470),(119,200)]
    d.line([(int(a*k),int(b*k)) for a,b in hexagon+[hexagon[0]]],fill=(127,145,141),width=max(2,int(8*k)),joint="curve")
    center_text(d,int(218*k),"A’Z",int(169*k),GOLD,size)
    d.line((int(190*k),int(422*k),int(510*k),int(422*k)),fill=GOLD,width=max(2,int(5*k)))
    center_text(d,int(442*k),"PRIGIMALIA",int(35*k),CREAM,size)
    return im

def backdrop():
    w,h=1920,1080
    im=Image.new("RGB",(w,h),DARK)
    pix=im.load()
    for y in range(h):
        for x in range(w):
            dx=(x-w*.5)/w;dy=(y-h*.48)/h
            falloff=max(0,1-math.sqrt(dx*dx+dy*dy)*1.7)
            pix[x,y]=(int(10+22*falloff),int(16+31*falloff),int(20+32*falloff))
    d=ImageDraw.Draw(im)
    d.line([(350,820),(1550,820)],fill=GOLD,width=3)
    center_text(d,340,"ANOMALIA’Z",136,CREAM,w)
    center_text(d,560,"PRIGIMALIA",110,GOLD,w)
    center_text(d,840,"L’EXTINCTION N’ÉTAIT QUE LE COMMENCEMENT",36,(186,195,197),w)
    return im

def save(image,relative,quality=92):
    out=ROOT/relative
    out.parent.mkdir(parents=True,exist_ok=True)
    image.save(out,quality=quality,optimize=True)
    print(relative,out.stat().st_size)
    
def approved_installed_logo():
    # Rasterized from the user-approved molten stone / red orb game logo.
    # Encoded source is a compact icon-scale copy, not the older A’Z monogram.
    source=ROOT/"assets/branding/approved-prigimalia-installed-icon-96.jpg.base64"
    if not source.exists():
        raise RuntimeError("Approved PRIGIMALIA image missing: "+str(source))
    data=base64.b64decode(source.read_text(encoding="ascii").strip(),validate=True)
    expected="737d45cc1a8f63ffb93643903f9105523ea7009bf3ac4aceb4dcf6609604f163"
    if hashlib.sha256(data).hexdigest()!=expected:
        raise RuntimeError("Approved PRIGIMALIA logo has unexpected checksum")
    img=Image.open(BytesIO(data)).convert("RGB")
    if img.size!=(96,96):
        raise RuntimeError("Unexpected source icon dimensions")
    return img.resize((700,700),Image.Resampling.LANCZOS)

def main():
    icon=approved_installed_logo()
    save(icon,"build/prigimalia-logo-small.jpg")
    save(icon,"public/prigimalia-logo.jpg")
    save(icon,"unreal/SourceAssets/Branding/prigimalia-installed-logo.jpg")
    save(icon,"unreal/SourceAssets/Branding/prigimalia-workshop-logo.jpg")
    wide=backdrop()
    save(wide,"unreal/SourceAssets/Branding/prigimalia-menu-backdrop.jpg",quality=89)
    for rel in ("build/icon.ico","unreal/Build/Windows/Application.ico"):
        target=ROOT/rel;target.parent.mkdir(parents=True,exist_ok=True)
        icon.resize((256,256),Image.Resampling.LANCZOS).save(
            target,format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
        print(rel,target.stat().st_size)
if __name__=="__main__":
    main()
