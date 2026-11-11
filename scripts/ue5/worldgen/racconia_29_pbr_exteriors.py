#!/usr/bin/env python3
"""RACCONIA 29-site authored architectural upgrade (NEW 3D PBR EXTERIORS).

Original 29 source GLBs are low-poly untextured blockouts, not quality models.
Make 29 separately importable 3D architectural shells with actual window/door
openings and original locality identities. Includes PBR textures, architectural
features and a machine-readable QA manifest. Original archive stays unchanged.

This is an *architectural exterior V1*, NOT 491 finished interiors / 187 solved
puzzles / a UE5 playable map / verified photogrammetry. It is not a Minecraft
cube replacement: the output includes material texture maps and substantial
non-box architectural geometry. No proprietary Resident Evil 3D assets are used.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import argparse, hashlib, io, json, math, random, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

MATERIALS=('brick','limestone','concrete','plaster','darkstone','wood','rust','steel','roof','glass','paint','copper','glassblue','trim','darkwood','gold','floor')
BASE={
 'brick':(120,61,48),'limestone':(166,153,131),'concrete':(113,123,120),'plaster':(163,153,132),
 'darkstone':(79,87,84),'wood':(104,77,53),'rust':(98,79,64),'steel':(71,84,93),
 'roof':(65,73,78),'glass':(47,76,87),'paint':(124,137,135),'copper':(75,112,107),
 'glassblue':(44,98,120),'trim':(204,192,169),'darkwood':(55,48,43),'gold':(171,139,75),'floor':(113,102,86)
}


def textures(seed=20261111):
    """Shared tiled PBR materials. Texture is authored procedural dirt/roughness,
    not a plain color. Color and metal-roughness textures are exported into GLBs.
    """
    rng=np.random.default_rng(seed)
    results={}
    n=256
    yy,xx=np.mgrid[0:n,0:n]
    for idx,name in enumerate(MATERIALS):
        base=np.array(BASE[name],float)
        a=np.zeros((n,n,3),float)+base[None,None,:]
        noise=rng.normal(0,9,(n,n))
        coarse=rng.normal(0,6,(16,16)).repeat(16,axis=0).repeat(16,axis=1)
        grain=(noise+coarse)
        if name in ('brick','limestone','darkstone'):
            height=22 if name=='brick' else 32
            width=62 if name=='brick' else 75
            row=yy//height
            offset=(row%2)*(width//2)
            joint=(yy%height<2)|((xx+offset)%width<2)
            stain=np.sin((xx+2*yy)/17)+np.sin((xx-yy)/31)
            a+=grain[:,:,None]*.8+stain[:,:,None]*2
            a[joint]=a[joint]*.46
        elif name in ('roof','rust','steel','copper','glass','glassblue'):
            a+=grain[:,:,None]*.5
            if name=='roof': a[(yy%26)<2]*=.60
            elif name in ('glass','glassblue'):
                a+=np.where((xx%32<2)|(yy%32<2),8.,0.)[:,:,None]
            elif name=='rust':
                pat=np.maximum(0,rng.normal(0,1,(n,n))+.75*np.sin(xx/12)*np.cos(yy/17))
                a+=pat[:,:,None]*np.array([14,1,-5])
        elif name in ('wood','darkwood'):
            a+=(np.sin(xx/2.8)*4+np.cos(xx/9)*3)[:,:,None]+grain[:,:,None]*.6
            a[:,::38,:]*=.80
        elif name in ('concrete','plaster'):
            a+=grain[:,:,None]
            a+=np.where(yy>180, -(yy-180)/5, 0)[:,:,None]
            a[(yy%127)<2]*=.82
        else:
            a+=grain[:,:,None]*.45
        a=np.uint8(np.clip(a,0,255))
        image=Image.fromarray(a,'RGB')
        metallic=220 if name in ('rust','steel','copper','gold') else 0
        rough=60 if name in ('glass','glassblue') else 155 if name in ('steel','gold') else 215
        mr=np.zeros((n,n,3),dtype=np.uint8)
        mr[:,:,1]=np.uint8(np.clip(rough+rng.normal(0,8,(n,n)),0,255))
        mr[:,:,2]=metallic
        mat=PBRMaterial(name='RACCONIA_PBR_'+name,baseColorTexture=image,
                metallicRoughnessTexture=Image.fromarray(mr,'RGB'),
                metallicFactor=1.0 if metallic else 0.,roughnessFactor=1.,
                doubleSided=(name in ('glass','glassblue')),
                alphaMode='OPAQUE')
        results[name]=mat
    return results


class Geometry:
    def __init__(self, mats):
        self.mats=mats
        self.v={n:[] for n in mats};self.f={n:[] for n in mats};self.uv={n:[] for n in mats}
        self.count=Counter()

    def quad(self,name,a,b,c,d,tile=(1,1)):
        vs=self.v[name];i=len(vs)
        vs.extend([tuple(a),tuple(b),tuple(c),tuple(d)])
        self.f[name].extend([(i,i+1,i+2),(i,i+2,i+3)])
        u,v=tile
        self.uv[name].extend([(0,0),(u,0),(u,v),(0,v)])
        self.count[name]+=2

    def box(self,name,center,size,tiling=2):
        x,y,z=center;w,d,h=size
        if min(w,d,h)<=.002:return
        x0,x1=x-w/2,x+w/2;y0,y1=y-d/2,y+d/2;z0,z1=z-h/2,z+h/2
        # Each face given repeat UV scaled by physical span.
        k=max(.2,tiling)
        self.quad(name,(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(w/k,h/k))
        self.quad(name,(x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(w/k,h/k))
        self.quad(name,(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(d/k,h/k))
        self.quad(name,(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1),(d/k,h/k))
        self.quad(name,(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0),(w/k,d/k))
        self.quad(name,(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1),(w/k,d/k))

    def cylinder(self,name,center,radius,height,segments=12,axis='z'):
        x,y,z=center;normal=[]
        a=[];b=[]
        for j in range(segments):
            angle=2*math.pi*j/segments
            p=(radius*math.cos(angle),radius*math.sin(angle))
            if axis=='z':
                a.append((x+p[0],y+p[1],z-height/2));b.append((x+p[0],y+p[1],z+height/2))
            elif axis=='x':
                a.append((x-height/2,y+p[0],z+p[1]));b.append((x+height/2,y+p[0],z+p[1]))
            else:
                a.append((x+p[0],y-height/2,z+p[1]));b.append((x+p[0],y+height/2,z+p[1]))
        for j in range(segments):
            k=(j+1)%segments
            self.quad(name,a[j],a[k],b[k],b[j],(.4,1))
        for j in range(1,segments-1):
            # cap triangles (degenerate quads not used)
            self.triangle(name,a[0],a[j+1],a[j]);self.triangle(name,b[0],b[j],b[j+1])

    def triangle(self,name,a,b,c):
        vs=self.v[name];i=len(vs)
        vs.extend([tuple(a),tuple(b),tuple(c)])
        self.f[name].append((i,i+1,i+2));self.uv[name].extend([(0,0),(1,0),(1,1)])
        self.count[name]+=1

    def roof(self,name,cx,cy,z,w,d,rise=3,axis='y'):
        x0,x1=cx-w/2,cx+w/2;y0,y1=cy-d/2,cy+d/2
        if axis=='x':
            self.quad(name,(x0,y0,z),(x0,y1,z),(cx,y1,z+rise),(cx,y0,z+rise),(d/3,rise/2))
            self.quad(name,(cx,y0,z+rise),(cx,y1,z+rise),(x1,y1,z),(x1,y0,z),(d/3,rise/2))
            self.triangle('trim',(x0,y0,z),(cx,y0,z+rise),(x1,y0,z))
            self.triangle('trim',(x1,y1,z),(cx,y1,z+rise),(x0,y1,z))
        else:
            self.quad(name,(x0,y0,z),(x1,y0,z),(x1,cy,z+rise),(x0,cy,z+rise),(w/3,rise/2))
            self.quad(name,(x0,cy,z+rise),(x1,cy,z+rise),(x1,y1,z),(x0,y1,z),(w/3,rise/2))
            self.triangle('trim',(x0,y0,z),(x0,cy,z+rise),(x0,y1,z))
            self.triangle('trim',(x1,y1,z),(x1,cy,z+rise),(x1,y0,z))

    def finish(self):
        scene=trimesh.Scene()
        for name in self.mats:
            if not self.f[name]:continue
            mesh=trimesh.Trimesh(vertices=np.asarray(self.v[name],dtype=np.float32),
              faces=np.asarray(self.f[name],dtype=np.int32),process=False,
              visual=TextureVisuals(uv=np.asarray(self.uv[name],dtype=np.float32),material=self.mats[name]))
            scene.add_geometry(mesh,node_name='RACCONIA_'+name,geom_name='RACCONIA_'+name)
        return scene


def piece_wall(g,wall,c,half,z0,z1,holes,mat):
    """Create ACTUAL facade wall apertures: no wall triangles inside door/windows.
    Coordinates u=horizontal along wall, vertical=z. c is wall-plane xy center.
    """
    xx,yy=c
    spans=[-half,half]
    bands=[z0,z1]
    for u0,u1,v0,v1 in holes:
        spans.extend((max(-half,u0),min(half,u1)))
        bands.extend((max(z0,v0),min(z1,v1)))
    spans=sorted(set(round(x,4) for x in spans));bands=sorted(set(round(x,4) for x in bands))
    for u0,u1 in zip(spans,spans[1:]):
        for v0,v1 in zip(bands,bands[1:]):
            if min(u1-u0,v1-v0)<.004:continue
            u=(u0+u1)/2;v=(v0+v1)/2
            if any(a<u<b and lo<v<hi for a,b,lo,hi in holes):continue
            if wall in ('front','back'):
                g.quad(mat,(xx+u0,yy,v0),(xx+u1,yy,v0),
                       (xx+u1,yy,v1),(xx+u0,yy,v1),((u1-u0)/2,(v1-v0)/2))
            else:
                g.quad(mat,(xx,yy+u0,v0),(xx,yy+u1,v0),
                       (xx,yy+u1,v1),(xx,yy+u0,v1),((u1-u0)/2,(v1-v0)/2))


def window(g,wall,c,u,z,width=1.5,height=1.85,profile='civil'):
    wx,wy=c
    thick=.10;depth=.12
    pos=wx+u if wall in ('front','back') else wy+u
    if wall in ('front','back'):
        g.box('glassblue' if profile in ('science','office') else 'glass',
            (pos,wy,z), (width-.10,.045,height-.10),1)
        for cx in (pos-width/2,pos+width/2):g.box('trim',(cx,wy,z),(thick,.22,height+.25),1)
        for cz in (z-height/2,z+height/2):g.box('trim',(pos,wy,cz),(width+.22,.24,thick),1)
        g.box('darkwood' if profile in ('gothic','manor') else 'steel',(pos,wy,z),(.045,.23,height),1)
        g.box('limestone',(pos,wy,z-height/2-.12),(width+.4,.36,.17),1)
        if profile in ('gothic','manor'):
            g.box('trim',(pos,wy,z+height/2+.19),(width+.5,.45,.23),1)
    else:
        g.box('glassblue' if profile in ('science','office') else 'glass',
            (wx,pos,z), (.045,width-.10,height-.10),1)
        for cy in (pos-width/2,pos+width/2):g.box('trim',(wx,cy,z),(.24,thick,height+.25),1)
        for cz in (z-height/2,z+height/2):g.box('trim',(wx,pos,cz),(.24,width+.22,thick),1)
        g.box('steel' if profile in ('science','office') else 'darkwood',(wx,pos,z),(.24,.045,height),1)
        g.box('limestone',(wx,pos,z-height/2-.12),(.36,width+.4,.17),1)


def door(g,wall,c,u,z,width=2.15,height=2.9,industrial=False):
    cx,cy=c
    mat='steel' if industrial else 'darkwood'
    if wall in ('front','back'):
        g.box(mat,(cx+u,cy+.12,z+height/2),(width-.1,.09,height-.08),2)
        for dx in (-width/2,width/2):g.box('trim',(cx+u+dx,cy+.04,z+height/2),(.18,.42,height+.25),1)
        g.box('limestone',(cx+u,cy+.04,z+height+.16),(width+.5,.45,.28),1)
        g.box('gold' if not industrial else 'steel',(cx+u+.55,cy+.22,z+1.1),(.07,.11,.14),1)
    else:
        g.box(mat,(cx+.12,cy+u,z+height/2),(.09,width-.1,height-.08),2)
        for dy in (-width/2,width/2):g.box('trim',(cx+.04,cy+u+dy,z+height/2),(.42,.18,height+.25),1)
        g.box('limestone',(cx+.04,cy+u,z+height+.16),(.45,width+.5,.28),1)


def stairs(g,cx,cy,base=0.,front=-1):
    for i in range(5):
        depth=(5-i)*.56
        g.box('limestone',(cx,cy+front*(depth/2),base+i*.16-.2),(5.4,depth,.34),1.5)


def land_light(g,x,y,z):
    g.cylinder('steel',(x,y,z+2.2),.09,4.4,8)
    g.box('glass',(x,y,z+4.6),(.7,.7,.95),1)
    g.box('darkstone',(x,y,z+5.12),(.85,.85,.22),1)


def house(g,cx,cy,w,d,floors=3,style='manor',color=None,roof=True,front='south',seed=0):
    rng=random.Random(seed)
    h=3.45 if style in ('manor','gothic','castle') else 3.65 if style=='science' else 3.25
    base=0.
    facade=color or ('limestone' if style in ('manor','gothic','castle') else
                      'concrete' if style in ('science','industrial','office') else 'brick')
    profile='gothic' if style in ('gothic','castle') else style
    g.box('darkstone',(cx,cy,-.43),(w+1.0,d+1.0,.86),3)
    for floor in range(floors):
        zl=base+floor*h;zu=zl+h
        g.box('floor',(cx,cy,zl+.14),(w-.65,d-.65,.27),2)
        cols_x=max(1,int((w-3)/4));cols_y=max(1,int((d-3)/4))
        for wall in ('front','back','left','right'):
            along=w if wall in ('front','back') else d
            cols=cols_x if wall in ('front','back') else cols_y
            plane=(cx,cy-d/2 if wall=='front' else cy+d/2) if wall in ('front','back') else (cx-w/2 if wall=='left' else cx+w/2,cy)
            openings=[]
            for j in range(cols):
                u=-along/2+(j+.5)*along/cols
                if floor==0 and j==cols//2 and wall==front:
                    ww=min(2.7,along/cols*.8);hh=2.8
                    openings.append((u-ww/2,u+ww/2,zl,zl+hh))
                else:
                    ww=min(1.6,along/cols*.46);hh=1.85
                    openings.append((u-ww/2,u+ww/2,zl+1.0,zl+1.0+hh))
            piece_wall(g,wall,plane,along/2,zl,zu,openings,facade)
            for j,(u0,u1,a,b) in enumerate(openings):
                mid=(u0+u1)/2
                if floor==0 and j==cols//2 and wall==front:
                    door(g,wall,plane,mid,zl,u1-u0,b-zl,style in ('science','industrial','office'))
                else:
                    window(g,wall,plane,mid,(a+b)/2,u1-u0,b-a,profile)
            if wall in ('front','back'):
                g.box('trim',(cx,plane[1],zu-.17),(w+.18,.35,.18),2)
            else:g.box('trim',(plane[0],cy,zu-.17),(.35,d+.18,.18),2)
        if floor==0:
            # Internal cross-corridor with side openings. Real floor planes/partitions,
            # not 491 finished gameplay rooms.
            if d>14:
                g.box('plaster',(cx,cy+3.0,zl+1.65),(w*.7,.14,3.0),2)
                g.box('plaster',(cx,cy-3.0,zl+1.65),(w*.7,.14,3.0),2)
        # Exterior pilasters and weathering reveals
        if floor==0 and style in ('manor','gothic','castle'):
            for xx in (cx-w/2+.55,cx+w/2-.55):
                for yy in (cy-d/2+.55,cy+d/2-.55):
                    g.box('trim',(xx,yy,zl+h/2),(.72,.72,h),1)
    top=base+floors*h
    g.box('trim',(cx,cy,top+.09),(w+.5,d+.5,.28),2)
    if roof and style in ('manor','gothic','castle','residential'):
        g.roof('roof',cx,cy,top+.15,w+1.2,d+1.2,min(3.0,max(1.2,w/10)),axis='x')
        for px in (cx-w/3,cx+w/3):
            g.box('darkstone',(px,cy,top+2.3),(1.3,1.3,4.0),1)
    else:
        g.box('roof',(cx,cy,top+.3),(w,d,.40),1.5)
        for j in range(max(1,int(w/12))):
            px=cx-w/3+j*5
            g.box('steel',(px,cy,top+1.0),(2.3,2.1,1.2),1)
            for slit in range(4):
                g.box('darkstone',(px-.8+slit*.52,cy-1.11,top+1),(.1,.11,.75),1)
    if front=='front':front='south'
    stairs(g,cx,cy-d/2-1.5,0.,-1)
    # gutter/downpipe exterior as cylinders, not painted boxes
    for side in (-1,1):
        g.cylinder('copper',(cx+side*(w/2+.15),cy-d/2,top/2),.1,top+1,10)


def turret(g,x,y,floors=5,r=2.8,z0=0,gothic=True):
    h=floors*3.4
    g.cylinder('darkstone',(x,y,z0+h/2),r,h,16)
    for level in range(floors):
        g.box('gold' if level==floors-1 else 'trim',(x,y-r-.13,z0+level*3.4+1.8),(1.25,.28,1.5),1)
    if gothic:
        # eight sided steep copper/stone pointed roof
        apex=(x,y,z0+h+4.2)
        for i in range(12):
            a=math.tau*i/12;b=math.tau*(i+1)/12
            g.triangle('copper',(x+r*math.cos(a),y+r*math.sin(a),z0+h),
                (x+r*math.cos(b),y+r*math.sin(b),z0+h),apex)
    else:
        for j in range(12):
            a=math.tau*j/12
            g.box('limestone',(x+math.cos(a)*(r-.25),y+math.sin(a)*(r-.25),z0+h+.55),(.84,.84,1.1),1)


def cathedral(g,w,d,seed):
    house(g,0,0,w,d,3,'gothic','limestone',roof=True,seed=seed)
    for x in (-w*.32,w*.32):turret(g,x,-d*.42,floors=5,r=2.8)
    # outward buttresses and gothic ribs
    for j in range(6):
        y=-d*.38+j*d*.15
        for sign in (-1,1):
            g.box('limestone',(sign*(w/2+1),y,3.0),(2.2,1.3,6.0),2)
            g.roof('limestone',sign*(w/2+1),y,6.0,2.3,1.4,.9,axis='x')
    # Rose glass with stone radial tracery at high western end
    g.cylinder('glassblue',(0,-d/2-.17,8),2.0,.1,32,axis='y')
    for a in range(12):
        ang=a*math.tau/12
        g.cylinder('trim',(math.cos(ang)*1.65,-d/2-.3,8+math.sin(ang)*1.65),.08,.34,8,axis='y')
    for j in range(3):land_light(g,(-w*.3)+j*w*.3,-d/2-4.,0)


def industrial(g,w,d,style,seed):
    house(g,0,0,w,d,2 if style=='industrial' else 3,style,'concrete',roof=False,seed=seed)
    for side in (-1,1):
        x=side*(w/2+3)
        g.cylinder('rust',(x,d*.1,8),2.0,15,16)
        for band in range(4):g.cylinder('steel',(x,d*.1,3+band*3),2.1,.24,16)
        g.cylinder('steel',(x,d*.1,16),2.5,.7,12)
    for j in range(3):
        x=-w/4+j*w/4
        g.cylinder('steel',(x,d*.35,12),.25,8,10)
        g.box('paint',(x,d*.35,16.2),(2,2,.65),1)
    for i in range(4):g.box('rust',(-w/2+i*3,-d/2-2,1.3),(2.2,2.2,2.6),1)


def castle(g,w,d,seed):
    w=max(21,w);d=max(20,d)
    # courtyard with separate wings, battlement curtain walls and corner towers
    house(g,0,d*.17,w*.68,d*.48,3,'castle','darkstone',roof=True,seed=seed)
    for x in (-w*.48,w*.48):
        for y in (-d*.47,d*.47):turret(g,x,y,6,2.5,gothic=True)
    for sign in (-1,1):
        y=sign*d*.48
        g.box('darkstone',(0,y,4.2),(w*.95,1.2,8.4),2)
        for i in range(15):g.box('darkstone',(-w*.44+i*w*.88/14,y,8.75),(1.05,1.35,1.7),2)
        x=sign*w*.48
        g.box('darkstone',(x,0,4.2),(1.2,d*.94,8.4),2)
        for i in range(15):g.box('darkstone',(x,-d*.44+i*d*.88/14,8.75),(1.35,1.05,1.7),2)
    # old stone keep arched gate marker, stair detail and iron gate
    g.box('steel',(0,-d*.49-.9,2.25),(3.4,.12,4.5),1)
    for i in range(9):g.box('gold',(-1.5+i*.36,-d*.5-1.0,2.25),(.07,.2,4.6),1)


def ship(g,kind,seed):
    w=18 if kind=='NEREIDE' else 21;d=55 if kind=='NEREIDE' else 62
    # taper from keel to decks, boat's long axis Y, not a box rectangle
    for zz,ww,dd in ((0,w*.48,d*.78),(1.5,w*.7,d*.9),(3.1,w,d)):
        g.box('darkstone',(0,0,zz),(ww,dd,.52),2)
    for side in (-1,1):
        for a,b in zip(range(-5,5),range(-4,6)):
            yy=a*d/10;yyy=b*d/10
            v1=(side*w*.32,yy,0);v2=(side*w*.50,yy,3.5)
            v3=(side*w*.50,yyy,3.5);v4=(side*w*.32,yyy,0)
            g.quad('rust' if kind!='NEREIDE' else 'paint',v1,v2,v3,v4,(1,2))
    g.box('floor',(0,0,3.5),(w,d,.38),2)
    # Deckhouse cabins/windows with actual apertures
    house(g,0,3,w*.62,d*.36,2,'office','paint',roof=False,seed=seed)
    house(g,0,-d*.20,w*.48,d*.19,1,'industrial','paint',roof=False,seed=seed+1)
    for x in (-w*.48,w*.48):
        for i in range(20):
            y=-d*.48+i*d*.05
            g.cylinder('steel',(x,y,4.4),.05,1.6,6)
    for i in range(2):
        y=-d*.14+i*8
        g.cylinder('rust',(0,y,13),1.4,7,16)
    for xx in (-w*.41,w*.41):
        for y in (-d*.22,d*.27):g.box('paint',(xx,y,5.3),(2.8,5.1,1.4),1)


def rail(g,seed):
    # Original Express Nocturne is a TRAIN, not a skyscraper
    for x in (-1.2,1.2):g.box('steel',(x,0,-.5),(.16,70,.27),1)
    for y in range(-34,36,2):g.box('wood',(0,y,-.58),(3.6,.28,.35),1)
    for j in range(4):
        y=-25+j*16.5
        house(g,0,y,4.0,15.5,1,'office','paint',roof=False,seed=seed+j)
        g.box('steel',(0,y,-.03),(4.3,15.8,.5),1)
        for dy in (-6.5,6.5):
            for dx in (-1.5,1.5):g.cylinder('steel',(dx,y+dy,-.54),.8,.44,14,axis='x')
        for yy in (y-7,y+7):g.box('gold',(0,yy,1.0),(3.4,.1,.35),1)


def prison(g,w,d,seed):
    house(g,0,0,w*.5,d*.55,3,'industrial','brick',roof=False,seed=seed)
    for side in (-1,1):
        g.box('darkstone',(0,side*d*.46,3.25),(w,.55,6.5),2)
        g.box('darkstone',(side*w*.46,0,3.25),(.55,d,6.5),2)
        for coord in range(12):
            x=-w*.45+coord*(w*.9/11)
            g.box('steel',(x,side*d*.46,7.1),(.05,.12,1.6),1)
    for side in (-1,1):turret(g,side*w*.43,-d*.43,floors=3,r=2.0,gothic=False)
    g.box('steel',(0,-d*.46-.09,2.1),(3.3,.2,4.2),1)


def manor(g,w,d,seed):
    house(g,0,d*.02,w*.69,d*.72,3,'manor','limestone',roof=True,seed=seed)
    for s in (-1,1):
        house(g,s*w*.36,0,w*.24,d*.43,2,'manor','brick',roof=True,seed=seed+s)
        turret(g,s*w*.46,-d*.27,3,2.2)
    for i in range(8):
        x=-w*.21+i*w*.06
        g.cylinder('limestone',(x,-d*.39,5.1),.29,7.7,12)
        g.box('limestone',(x,-d*.39,9.1),(.9,.9,.55),1)
    for x in (-w*.46,w*.46):land_light(g,x,-d*.47,0)


def city(g,w,d,seed):
    structures=[(-w*.22,-d*.16,w*.38,d*.40,4),
      (w*.23,-d*.18,w*.30,d*.36,5),(-w*.22,d*.23,w*.26,d*.31,3),
      (w*.20,d*.22,w*.34,d*.31,4)]
    for i,(x,y,bw,bd,floors) in enumerate(structures):
        house(g,x,y,bw,bd,floors,'office' if i%2 else 'industrial',
            'brick' if i%2 else 'concrete',roof=False,seed=seed+i)
    for x in (-w*.42,w*.42):
        for y in (-d*.38,d*.38):land_light(g,x,y,0)


PROFILE={
 'VARKOV':'manor','SPD':'police','RAVENFALL':'hotel','SAINT_VEYR':'orphanage',
 'VEYRHOLM':'hospital','HELIX':'science','SECTEUR_ZERO':'industrial',
 'NEREIDE':'ship','VALTERIA':'harbor','LEVIATHAN':'shipwreck',
 'KARSEN':'prison','NOCTIS':'tower','VALDRIS':'castle','NEXUS':'science',
 'BLACKWOOD':'manor','DRAKOV':'castle','BIG_CITY_CONTAMINE':'city',
 'EXPRESS_NOCTURNE':'train','ACADEMIE_VARKOV':'academy','MOROZOV':'industrial',
 'RAVENSKA':'village','SANCTUAIRE_VALDRIS':'gothic','KROVAK':'military',
 'KARZHAN':'city','ZARNOV':'swamp','OMEGA':'science',
 'SAINT_MORVAN':'cathedral','VOLSKAYA':'city','LIANSKAR':'city',
}


def build_one(site,source_zip,mats,seed=20261111):
    kind=site['id'];style=PROFILE[kind]
    with zipfile.ZipFile(source_zip) as z:
        source_file='Models/'+site['geometry'] if 'Models/'+site['geometry'] in z.namelist() else 'Models_original_blockouts/'+site['geometry']
        source_scene=trimesh.load(io.BytesIO(z.read(source_file)),file_type='glb',force='scene')
    extent=source_scene.extents
    local_mats=dict(mats)
    sign=Image.new('RGB',(640,160),(24,33,38))
    ink=ImageDraw.Draw(sign)
    try:ft=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf',40)
    except OSError:ft=ImageFont.load_default()
    title=site['name'].upper()
    while ink.textbbox((0,0),title,font=ft)[2]>600 and len(title)>9:
        title=title[:-2]+'.'
    box=ink.textbbox((0,0),title,font=ft)
    ink.rectangle((12,12,628,148),outline=(136,123,91),width=4)
    ink.text(((640-(box[2]-box[0]))/2,(160-(box[3]-box[1]))/2-box[1]),
             title,font=ft,fill=(224,207,157))
    local_mats['sign']=PBRMaterial(name='RACCONIA_UNIQUE_SIGN_'+kind,
        baseColorTexture=sign,metallicFactor=.15,roughnessFactor=.48,doubleSided=True)
    g=Geometry(local_mats)
    rng=random.Random(seed+sum(map(ord,kind)))
    w=max(12.,min(55.,extent[0]*.75));d=max(13.,min(47.,extent[1]*.67))
    if style=='manor':manor(g,w,d,seed)
    elif style=='police':
        house(g,0,0,w,d,4,'manor','limestone',roof=False,seed=seed)
        for x in np.linspace(-w*.30,w*.30,8):g.cylinder('limestone',(float(x),-d/2-1,5.2),.42,8.,12)
        for x in (-w*.35,w*.35):land_light(g,x,-d/2-5,0)
    elif style=='hotel':
        house(g,0,0,w,d,5,'residential','brick',roof=True,seed=seed)
        for floor in range(1,5):
            for x in np.linspace(-w*.36,w*.36,5):
                g.box('steel',(float(x),-d/2-1,3.25*floor+.2),(2.9,1.8,.15),1)
                for dx in (-1.35,1.35):g.cylinder('steel',(float(x+dx),-d/2-1.85,3.25*floor+.65),.06,.9,8)
    elif style in ('orphanage','academy'):
        house(g,0,0,w,d,3,'manor','brick',roof=True,seed=seed)
        for x in (-w*.4,w*.4):turret(g,x,d*.31,3,1.8)
    elif style=='cathedral':cathedral(g,w,d,seed)
    elif style=='gothic':
        house(g,0,0,w,d,3,'gothic','darkstone',roof=True,seed=seed)
        for x in (-w*.4,w*.4):turret(g,x,-d*.37,5,2.0)
    elif style=='castle':
        castle(g,w,d,seed)
        if kind=='DRAKOV':
            turret(g,0,d*.34,8,4.1,gothic=True)
            for x in (-w*.38,w*.38):g.box('darkstone',(x,-d*.2,4.5),(1.8,5.0,9.0),2)
        else:
            for j in range(5):
                g.box('darkstone',(-w*.34+j*w*.17,d*.21,11),(2.0,2.0,2.6),2)
    elif style in ('industrial','science'):
        industrial(g,w,d,style,seed)
        if kind=='MOROZOV':
            for xx in (-w*.35,w*.35):
                for yy in (-d*.33,d*.36):
                    g.cylinder('darkstone',(xx,yy,.9),3.3,1.6,24)
                    g.cylinder('glassblue',(xx,yy,1.8),3.0,.12,24)
        elif kind=='OMEGA':
            for xx in (-w*.31,w*.31):
                g.cylinder('glassblue',(xx,d*.33,5),3.5,8,24)
                apex=(xx,d*.33,11.)
                for i in range(16):
                    a=math.tau*i/16;b=math.tau*(i+1)/16
                    g.triangle('steel',(xx+3.5*math.cos(a),d*.33+3.5*math.sin(a),9),
                        (xx+3.5*math.cos(b),d*.33+3.5*math.sin(b),9),apex)
        elif kind=='NEXUS':
            for side in (-1,1):
                g.box('steel',(side*w*.42,-d*.32,4),(1.2,8,7),1)
                for i in range(8):
                    g.box('rust',(side*w*.46,-d*.3+i*.9,4),(.25,.2,7),1)
        elif kind=='HELIX':
            # distinct roof helicopter pad and biomedical ventilation stacks
            g.cylinder('concrete',(0,0,12),5.0,.35,32)
            g.box('paint',(0,0,12.3),(4,.6,.12),1)
            for yy in (-1.8,1.8):g.box('paint',(0,yy,12.3),(.6,4,.12),1)
    elif style=='ship':ship(g,'NEREIDE',seed)
    elif style=='shipwreck':ship(g,'LEVIATHAN',seed)
    elif style=='train':rail(g,seed)
    elif style=='prison':prison(g,w,d,seed)
    elif style=='village':
        for i,(x,y,floor) in enumerate(((-w*.28,-d*.21,2),(w*.24,-d*.25,2),
                                       (-w*.20,d*.27,1),(w*.27,d*.24,2))):
            house(g,x,y,w*.29,d*.27,floor,'residential','wood',roof=True,seed=seed+i)
            g.box('darkwood',(x,y-d*.14,1.3),(2.0,.18,2.6),1)
        for x in (-w*.4,w*.4):land_light(g,x,-d*.42,0)
    elif style=='city':
        city(g,w,d,seed)
        if kind=='LIANSKAR':
            house(g,w*.04,-d*.06,w*.24,d*.22,8,'office','concrete',roof=False,seed=seed+80)
            for i in range(3):g.cylinder('steel',(-w*.14+i*3,d*.32,13),.25,24,10)
        elif kind=='VOLSKAYA':
            for x in np.linspace(-w*.35,w*.35,7):g.cylinder('limestone',(float(x),-d*.36,3.9),.28,7.8,12)
            for i in range(5):g.box('limestone',(-w*.32+i*4,-d*.47,.5),(3.6,2.2,.28),1)
        elif kind=='KARZHAN':
            for xx in (-w*.43,w*.42):
                g.cylinder('rust',(xx,d*.37,4.8),2.1,8.5,18)
                g.cylinder('steel',(xx,d*.37,9.0),2.4,.38,18)
            for i in range(4):g.box('steel',(-w*.35+i*5,d*.4,1.7),(1.1,3.4,2.8),1)
        elif kind=='BIG_CITY_CONTAMINE':
            for i in range(6):
                x=-w*.38+i*w*.15
                g.box('rust',(x,-d*.42,1.2),(2.5,.75,2.25),1)
                g.box('wood',(x,-d*.42-.18,2.55),(2.7,.35,.21),1)
            for i in range(3):
                g.box('darkstone',(w*.3,-d*.18+i*3,1.2),(1.2,2.9,2.4),1)
    elif style=='swamp':
        house(g,0,0,15,13,2,'residential','darkstone',roof=True,seed=seed)
        for j in range(12):
            y=-21+j*3.8
            g.box('wood',(6,y,.85),(3.0,2.8,.18),1)
            for x in (4.8,7.2):g.cylinder('wood',(x,y,.10),.18,1.8,10)
        for x in (-13,13):land_light(g,x,-9,0)
    elif style in ('military','harbor'):
        industrial(g,w,d,'industrial',seed)
        for x in (-w*.5,w*.5):turret(g,x,d*.35,3,2.1,False)
        if kind=='VALTERIA':
            for xx in (-w*.39,w*.39):
                g.box('gold',(xx,d*.18,12),(.6,.6,23),1)
                g.box('gold',(xx+5,d*.18,23.5),(11,.6,.65),1)
                g.cylinder('steel',(xx+10,d*.18,17),.06,12,8)
        elif kind=='KROVAK':
            g.cylinder('steel',(0,d*.25,11),.24,18,10)
            for yy in (-d*.33,d*.33):
                g.box('concrete',(0,yy,1.5),(10,3.8,3),1)
    elif style=='tower':
        house(g,0,0,w*.8,d*.8,7,'office','concrete',roof=False,seed=seed)
        for x in (-w*.38,w*.38):g.box('steel',(x,0,12.5),(.65,d*.8,25),1)
        g.cylinder('steel',(0,0,34),.32,18,12)
        for i in range(3):g.box('gold',(0,0,27+i*3),(7,.24,.20),1)
    elif style=='hospital':
        house(g,0,0,w,d,4,'science','plaster',roof=False,seed=seed)
        for dx in (-w*.39,w*.39):g.box('paint',(dx,-d*.5-.5,8),(.22,.3,6),1)
        g.box('paint',(0,-d*.5-.5,8),(6,.3,.22),1)
    else:raise ValueError('Not authored: '+kind)
    # A locally-authored sign using the user's ORIGINAL venue name gives each
    # landmark a distinct visual identity; no Resident Evil logos/assets.
    if style not in ('train','ship','shipwreck'):
        front_y=-d*.5-.45
        g.box('darkstone',(0,front_y-.03,4.55),(min(w*.60,15),.38,1.85),1)
        sw=min(w*.58,14.6)
        g.quad('sign',(-sw/2,front_y-.245,4.03),(sw/2,front_y-.245,4.03),
              (sw/2,front_y-.245,5.05),(-sw/2,front_y-.245,5.05),(1,1))
    scene=g.finish()
    faces=sum(len(v.faces) for v in scene.geometry.values())
    textured=sum(isinstance(v.visual,TextureVisuals) and getattr(v.visual.material,'baseColorTexture',None) is not None
                 for v in scene.geometry.values())
    if faces<900 or textured<5:raise ValueError(f'Unacceptably simple/unstyled 3D scene {kind}: {faces} faces {textured} textured materials')
    if np.max(scene.extents)>170 or np.any(scene.extents<=0):raise ValueError('Model bounds invalid '+kind)
    return scene,{'id':kind,'name':site['name'],'style':style,'originalReferenceGLB':site['geometry'],
        'sourceOriginalTriangles':sum(len(v.faces) for v in source_scene.geometry.values()),
        'sourceOriginalTexturedGeometryCount':sum(getattr(v.visual,'kind',None)=='texture' for v in source_scene.geometry.values()),
        'newTriangles':faces,'newTexturedMaterialGroups':textured,
        'newGeometryBoundsMeters':[round(float(v),3) for v in scene.extents],
        'documentedRooms':site.get('room_count',len(site.get('rooms',[]))), 'interiorsComplete':False,
        'photorealismVisuallyCertified':False,'nativeUE5Imported':False,
        'collisionsAndDoorsPlaytested':False,'geometryStatus':'PBR_ARCHITECTURAL_EXTERIOR_V1_NOT_FINAL'}


def generate(original:Path,dest:Path,limit=None,catalog_path:Path|None=None):
    if dest.exists():raise FileExistsError('Refuse to overwrite existing 29-site upgrade pack')
    with zipfile.ZipFile(original) as src:
        if 'Data/Horror_Catalog_29.json' in src.namelist():
            catalog_bytes=src.read('Data/Horror_Catalog_29.json')
        elif catalog_path is not None:
            catalog_bytes=catalog_path.read_bytes()
        else:raise ValueError('Missing original 29 horror catalog or --catalog argument')
        catalog=json.loads(catalog_bytes)
        if len(catalog['sites'])!=29:raise ValueError('Expected 29 original horror sites')
        source_hash=hashlib.sha256(catalog_bytes).hexdigest()
        master_sites=set(s['id'] for s in catalog['sites'])
        if master_sites != set(PROFILE):raise ValueError('Changed original horror site identities')
    dest.mkdir(parents=True)
    (dest/'GLB_PBR_EXTERIORS_V1').mkdir()
    mats=textures()
    entries=[]
    for idx,site in enumerate(catalog['sites'][:limit]):
        scene,rec=build_one(site,original,mats,seed=20261111+idx*27)
        artifact='RACCONIA_'+site['id']+'_ARCHITECTURAL_PBR_V1.glb'
        data=scene.export(file_type='glb')
        (dest/'GLB_PBR_EXTERIORS_V1'/artifact).write_bytes(data)
        rec['file']=artifact;rec['bytes']=len(data)
        rec['sha256']=hashlib.sha256(data).hexdigest()
        entries.append(rec)
        print(idx+1,site['id'],rec['newTriangles'],rec['newTexturedMaterialGroups'],round(len(data)/1024), 'KB',flush=True)
    manifest={'schemaVersion':1,'project':'ANOMALIA’Z PRIGIMALIA','world':'RACCONIA-VARKOVIA',
      'approvedOriginalSiteCount':29,'catalogSha256':source_hash,'modelsGenerated':len(entries),
      'sourceFilesUntouched':True,'allOriginalSiteNamesPreserved':True,
      'notMincraftReferenceOnly':True,'style':'Original authored horror PBR exterior architecture',
      'noResidentEvilProprietaryAssets':True,
      'geometryIsNotPhotogrammetry':True,'photorealisticInGameNotVerified':True,
      '491RoomsCompleted':False,'187PuzzlesCompleted':False,
      'nativeUE5Imported':False,'nativeMapPlayable':False,
      'originalBlockoutsRemainForReferenceNotFinalPlacement':True,'models':entries}
    (dest/'RACCONIA_29_PBR_ARCHITECTURE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (dest/'README_FR.txt').write_text('''RACCONIA-VARKOVIA 29 lieux d’horreur — nouvelle architecture 3D PBR V1.

29 lieux et noms conservés du vrai catalogue Horror_Catalog_29.json.
Génération de vrais maillages 3D d’architecture: murs avec ouvertures géométriques,
fenêtres avec cadres, portes, toitures, tours, corniches, escaliers, matériaux
PBR (textures RGB et rugosité/métal), silhouettes personnalisées (château,
manoir, laboratoire, prison, cathédrale, hôtel, bateau, train, quartiers).

ATTENTION: c'est une livraison architecturale V1, pas du photoréalisme
validé dans Unreal ni un bâtiment de jeu terminé. Les 491 salles, portes
interactives, escaliers fonctionnels, collision fine, navmesh, loot, puzzles,
optimisation Nanite/LOD et gameplay nécessitent du travail et des tests UE.
Ne pas remplacer les modèles originaux; les GLB préliminaires restent des
références pour l’agencement des pièces. La topographie et les emplacements
originaux n’ont pas été modifiés. L’ensemble n’utilise pas d’assets Resident Evil.
''',encoding='utf-8')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=None)
    parser.add_argument('--catalog',type=Path,default=None)
    args=parser.parse_args()
    generate(args.source,args.output,args.limit,args.catalog)
