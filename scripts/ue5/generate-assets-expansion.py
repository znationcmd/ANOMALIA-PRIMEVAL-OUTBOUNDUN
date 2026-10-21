"""Deterministic original ANOMALIA prototype geometry. Standard-library only.
Metres, glTF Y-up; no third-party art or claims of real manufacturer fidelity.
Each model is one mesh with named PBR materials. No driving/animation validation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = [
    ('Body', (.12,.24,.33,1), .45,.3),
    ('Rubber', (.018,.021,.025,1), 0,.95),
    ('Metal', (.42,.46,.5,1), .85,.28),
    ('Interior', (.075,.065,.055,1), 0,.85),
    ('Glass', (.12,.25,.31,.35), .1,.12),
    ('Lamp', (.98,.94,.72,1), .1,.22),
    ('Red', (.72,.025,.018,1), .2,.35),
    ('Blue', (.035,.11,.75,1), .25,.3),
    ('White', (.87,.88,.83,1), .15,.45),
    ('Concrete', (.5,.48,.43,1), 0,.95),
    ('Timber', (.24,.11,.04,1), 0,.85),
    ('Roof', (.29,.105,.055,1), 0,.9),
    ('Green', (.12,.25,.08,1), .2,.65),
]


class Mesh:
    def __init__(self):
        self.parts = {i: [] for i in range(len(MATERIALS))}

    def triangle(self, a, b, c, material):
        self.parts[material].append((a,b,c))

    def box(self, size, at, material=0):
        sx,sy,sz = [v/2 for v in size]
        x,y,z = at
        v = [(x+i*sx,y+j*sy,z+k*sz) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]:
            self.triangle(v[a],v[b],v[c],material);self.triangle(v[a],v[c],v[d],material)

    def cylinder(self, a, b, radius, material=2, steps=16):
        axis = unit(sub(b,a));guide=(0,1,0) if abs(axis[1])<.9 else (1,0,0)
        u=unit(cross(axis,guide));v=cross(axis,u)
        rings=[]
        for origin in [a,b]:
            rings.append([tuple(origin[j]+radius*(math.cos(t*2*math.pi/steps)*u[j]+math.sin(t*2*math.pi/steps)*v[j]) for j in range(3)) for t in range(steps)])
        for i in range(steps):
            n=(i+1)%steps
            self.triangle(rings[0][i],rings[0][n],rings[1][i],material)
            self.triangle(rings[0][n],rings[1][n],rings[1][i],material)
            self.triangle(a,rings[0][n],rings[0][i],material)
            self.triangle(b,rings[1][i],rings[1][n],material)

    def hull(self, rings, material=0):
        # Each station: x, lower y, upper y, lower half-width, upper half-width.
        vertices=[[(x,lo,-lw),(x,lo,lw),(x,hi,uw),(x,hi,-uw)] for x,lo,hi,lw,uw in rings]
        for i in range(len(vertices)-1):
            for k in range(4):
                a,b=vertices[i][k],vertices[i][(k+1)%4];c,d=vertices[i+1][(k+1)%4],vertices[i+1][k]
                self.triangle(a,b,c,material);self.triangle(a,c,d,material)
        for ring,reverse in [(vertices[0],False),(vertices[-1],True)]:
            for a,b,c in [(0,1,2),(0,2,3)]:self.triangle(ring[a],ring[c] if reverse else ring[b],ring[b] if reverse else ring[c],material)

    def wheel(self, x, y, z, radius=.36, width=.22):
        # Rounded tyre cross section with visible sidewalls and alloy wheel spokes.
        sections=24;profile=[(-.5,.76),(-.48,.9),(-.3,1),(.3,1),(.48,.9),(.5,.76)]
        rings=[[(x+radius*r*math.cos(2*math.pi*i/sections),y+radius*r*math.sin(2*math.pi*i/sections),z+p*width) for i in range(sections)] for p,r in profile]
        for j in range(len(rings)-1):
            for i in range(sections):
                k=(i+1)%sections
                self.triangle(rings[j][i],rings[j+1][i],rings[j+1][k],1)
                self.triangle(rings[j][i],rings[j+1][k],rings[j][k],1)
        self.cylinder((x,y,z-width*.53),(x,y,z+width*.53),radius*.58,2,24)
        for side in [-1,1]:
            zz=z+side*width*.55
            for i in range(6):
                angle=i*math.pi/3
                self.cylinder((x,y,zz),(x+radius*.5*math.cos(angle),y+radius*.5*math.sin(angle),zz),radius*.045,8,6)
        self.cylinder((x,y,z-width*.56),(x,y,z+width*.56),radius*.16,3,12)

    def seat(self, x, y, z, width=.46):
        self.box((.48,.12,width),(x,y,z),3)
        self.box((.12,.55,width),(x-.2,y+.28,z),3)
        self.box((.13,.18,width*.65),(x-.2,y+.63,z),3)

    def steering(self,x,y,z):
        self.cylinder((x-.18,y-.25,z),(x,y,z),.025)
        for i in range(16):
            a=i*math.pi/8;b=(i+1)*math.pi/8
            self.cylinder((x,y+.17*math.cos(a),z+.17*math.sin(a)),(x,y+.17*math.cos(b),z+.17*math.sin(b)),.015,1,6)

    def export(self, name):
        blob=bytearray();views=[];accessors=[];primitives=[];all_vertices=[];triangles=0
        def array(values, kind, component, target):
            while len(blob)%4:blob.append(0)
            flat=[c for v in values for c in v] if kind=='VEC3' else values
            raw=struct.pack('<'+('f' if component==5126 else 'I')*len(flat),*flat)
            view=len(views);views.append(dict(buffer=0,byteOffset=len(blob),byteLength=len(raw),target=target));blob.extend(raw)
            a=dict(bufferView=view,componentType=component,count=len(values),type=kind)
            if kind=='VEC3':a.update(min=[min(v[i] for v in values) for i in range(3)],max=[max(v[i] for v in values) for i in range(3)])
            accessors.append(a);return len(accessors)-1
        for material,faces in self.parts.items():
            if not faces:continue
            verts=[];normals=[]
            for a,b,c in faces:
                normal=unit(cross(sub(b,a),sub(c,a)))
                verts.extend([a,b,c]);normals.extend([normal]*3)
            all_vertices.extend(verts);triangles+=len(faces)
            primitives.append(dict(attributes=dict(POSITION=array(verts,'VEC3',5126,34962),NORMAL=array(normals,'VEC3',5126,34962)),indices=array(list(range(len(verts))),'SCALAR',5125,34963),material=material,mode=4))
        materials=[]
        for label,color,metal,rough in MATERIALS:
            item=dict(name=label,pbrMetallicRoughness=dict(baseColorFactor=color,metallicFactor=metal,roughnessFactor=rough),doubleSided=True)
            if label=='Glass':item.update(alphaMode='BLEND')
            materials.append(item)
        doc=dict(asset=dict(version='2.0',generator='CMD Original Expansion v1'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0)],meshes=[dict(name='SM_'+name,primitives=primitives)],materials=materials,buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=accessors)
        raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);blob+=b'\0'*((-len(blob))%4)
        data=struct.pack('<III',0x46546C67,2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4E4F534A)+raw+struct.pack('<II',len(blob),0x004E4942)+blob
        dims=[max(v[i] for v in all_vertices)-min(v[i] for v in all_vertices) for i in range(3)]
        return data,dims,triangles


def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
    n=math.sqrt(sum(x*x for x in v));return tuple(x/n for x in v) if n>1e-12 else (0,1,0)


def cabin(m, front, rear, height=1.85, width=1.8, floor=.75, paint=0):
    # Open usable volume: pillars, thin roof/floor, transparent window panes and dashboard.
    mid=(front+rear)/2;length=front-rear
    m.box((length,.12,width),(mid,floor,0),paint)
    m.box((length,.1,width*.94),(mid,height,0),paint)
    for x in [front,rear]:
        for z in [-width*.46,width*.46]:m.cylinder((x,floor,z),(x,height,z),.045,paint,8)
    for side in [-1,1]:
        z=side*width*.5
        m.box((length,.42,.045),(mid,floor+.24,z),paint)
        m.box((length-.12,height-floor-.65,.018),(mid,(height+floor+.55)/2,z),4)
        m.box((.2,.03,.04),(mid+.1,floor+.55,z+side*.035),2)
        m.box((.18,.1,.12),(front-.15,floor+.8,z+side*.16),paint)
    for x in [front,rear]:m.box((.018,height-floor-.3,width*.87),(x,(height+floor+.3)/2,0),4)
    m.box((.28,.16,width*.9),(front-.16,floor+.62,0),3)
    for z in [-width*.25,width*.25]:m.seat(rear+.42,floor+.25,z)
    m.steering(front-.32,floor+.85,-width*.25)


def road_vehicle(m,kind):
    truck=kind in ['transport_truck','semi_truck','fire_engine','train']
    suv=kind in ['suv','police','gendarmerie','monster_truck']
    van=kind in ['van','ambulance','armored_van']
    paint=6 if kind=='fire_engine' else (8 if kind in ['ambulance','police'] else (7 if kind=='gendarmerie' else 0))
    length=7.8 if truck else (5.7 if van else 4.65);width=2.35 if truck else (2.0 if van else 1.86)
    radius=.55 if truck else (.78 if kind=='monster_truck' else (.41 if suv else .35))
    floor=radius+.4;front=length*.5
    m.box((length,.24,width*.72),(0,floor-.25,0),2)
    for x in ([2.5,-1.6,-2.8] if truck else [length*.31,-length*.31]):
        m.cylinder((x,radius,-width*.52),(x,radius,width*.52),.075)
        for side in [-1,1]:
            m.wheel(x,radius,side*width*.48,radius,.3 if truck else .24)
            m.cylinder((x-.18,floor-.2,side*width*.36),(x+.12,radius,side*width*.48),.035)
    if truck:
        cabin(m,front-.15,front-2.0,height=floor+2,width=width,floor=floor,paint=paint)
        m.box((1.7,.55,width),(front-.95,floor+.25,0),paint)
        if kind=='semi_truck':
            # Tractor chassis and visible fifth wheel; trailer is a separate static model.
            m.cylinder((-1.4,floor,0),(-1.4,floor+.12,0),.42,2,24)
            for z in [-.75,.75]:m.cylinder((1.15,floor,z),(1.15,floor+2.4,z),.08)
        elif kind=='fire_engine':
            m.box((4.9,1.8,width),(-1.2,floor+.85,0),paint)
            for side in [-1,1]:
                for x in [-2.7,-1.4,-.1]:
                    m.box((1.1,1.1,.035),(x,floor+.8,side*(width/2+.02)),2)
                    for y in [.4,.65,.9,1.15]:m.box((1.05,.015,.045),(x,floor+y,side*(width/2+.05)),3)
            for z in [-.35,.35]:m.cylinder((-3.4,floor+1.95,z),(1.1,floor+1.95,z),.04)
            for x in range(-3,2):m.cylinder((x,floor+1.95,-.35),(x,floor+1.95,.35),.025)
        else:
            m.box((4.9,.18,width),(-1.2,floor+.05,0),paint)
            for side in [-1,1]:
                m.box((4.9,.7,.08),(-1.2,floor+.5,side*width/2),paint)
                for x in [-3.5,-2,-.5,1]:m.box((.07,.85,.1),(x,floor+.5,side*width/2),2)
    elif van:
        cabin(m,front-.2,front-1.9,height=floor+1.9,width=width,floor=floor,paint=paint)
        m.box((3.5,1.9,width),(-.9,floor+.95,0),paint)
        for side in [-1,1]:m.box((3.2,.12,.025),(-.9,floor+.65,side*(width/2+.02)),6 if kind=='ambulance' else 2)
        for z in [-width*.24,width*.24]:
            m.box((.035,1.6,width*.46),(-length*.5-.02,floor+.9,z),paint)
            m.box((.05,.4,.4),(-length*.5-.05,floor+1.4,z),4)
        if kind=='ambulance':
            for side in [-1,1]:
                m.box((.7,.15,.03),(-.8,floor+1.45,side*(width/2+.03)),6)
                m.box((.15,.7,.03),(-.8,floor+1.45,side*(width/2+.04)),6)
    else:
        m.hull([(-length/2,floor-.15,floor+.25,width*.42,width*.49),(-1,floor-.15,floor+.45,width*.48,width*.5),(1,floor-.15,floor+.4,width*.48,width*.49),(length/2,floor-.1,floor+.25,width*.4,width*.44)],paint)
        cabin(m,.7,-1.55,height=floor+(1.35 if suv else 1.05),width=width*.94,floor=floor+.15,paint=paint)
        m.box((1.5,.08,width*.86),(1.48,floor+.45,0),paint)
        for side in [-1,1]:
            for x in [-1,.15]:m.box((.03,.72,.04),(x,floor+.75,side*width*.48),paint)
    for side in [-1,1]:
        m.box((.05,.18,.32),(front+.02,floor+.2,side*width*.33),5)
        m.box((.05,.2,.25),(-length/2-.03,floor+.18,side*width*.36),6)
    m.box((.12,.14,width*.85),(front+.08,floor-.05,0),2)
    for y in [floor+.05,floor+.15,floor+.25]:m.box((.06,.025,width*.4),(front+.05,y,0),1)
    if kind in ['police','gendarmerie','ambulance','fire_engine']:
        top=floor+(2.1 if truck or van else 1.48)
        m.box((.3,.06,1.15),(.15 if not truck else front-.9,top,0),2)
        for side in [-1,1]:m.box((.25,.15,.45),(.15 if not truck else front-.9,top+.1,side*.34),7 if side<0 else 6)


def tractor(m):
    m.box((3.5,.35,1.1),(0,.8,0),12)
    for x,r,z in [(-1.1,.8,.85),(1.3,.48,.69)]:
        for side in [-1,1]:m.wheel(x,r,side*z,r,.4)
        m.cylinder((x,r,-z),(x,r,z),.08)
    m.box((1.6,.7,.85),(.9,1.2,0),12)
    cabin(m,.2,-1.25,height=2.8,width=1.35,floor=1.25,paint=12)
    m.cylinder((.65,1.3,.45),(.65,2.6,.45),.065,1)
    for side in [-1,1]:m.box((1.8,.12,.5),(-1.0,1.72,side*.9),12)
    for y in [.5,.75,1]:m.box((.4,.05,.28),(-.4,y,-.95),2)
    for z in [-.4,.4]:m.cylinder((-1.5,.7,z),(-2.1,.45,z),.04)


def racer(m,kind):
    buggy=kind=='buggy';formula=kind=='formula_one'
    length=4.8 if formula else (3.2 if buggy else 1.85);width=1.9 if formula else (1.65 if buggy else 1.25);r=.34 if formula else (.38 if buggy else .14)
    m.hull([(-length/2,r-.12,r+.25,.25,.4),(0,r-.12,r+.3,.42,.48),(length/2,r-.08,r+.12,.1,.13)],0)
    for x in [-length*.32,length*.32]:
        m.cylinder((x,r,-width*.5),(x,r,width*.5),.04)
        for side in [-1,1]:m.wheel(x,r,side*width*.48,r,.3 if formula else .2)
    for z in ([-.36,.36] if buggy else [0]):m.seat(-.25,r+.22,z,.42);m.steering(.3,r+.65,z)
    if buggy:
        for side in [-1,1]:
            for x in [-.8,.55]:m.cylinder((x,r+.2,side*.67),(x-.15,r+1.5,side*.6),.04)
            m.cylinder((-.95,r+1.5,side*.6),(.4,r+1.5,side*.6),.04)
            m.cylinder((-.95,r+1.5,side*.6),(-1.3,r+.25,side*.6),.04)
        for x in [-.95,.4]:m.cylinder((x,r+1.5,-.6),(x,r+1.5,.6),.04)
    if formula:
        for x,y,w in [(length*.45,r+.1,1.85),(-length*.45,r+.7,1.5)]:
            m.box((.38,.07,w),(x,y,0),0)
            for side in [-1,1]:m.box((.35,.25,.04),(x,y+.06,side*w/2),0)
        for side in [-1,1]:m.box((1.6,.45,.35),(-.45,r+.1,side*.65),0)
        m.cylinder((-.6,r+.55,-.3),(.2,r+.95,0),.03)
        m.cylinder((-.6,r+.55,.3),(.2,r+.95,0),.03)
    elif not buggy:
        m.box((.4,.32,.36),(-.55,r+.25,.35),2)
        m.box((.15,.2,width),(.75,r+.1,0),0)


def motorcycle(m,offroad=False):
    r=.34 if offroad else .31
    for x in [-.72,.78]:m.wheel(x,r,0,r,.12)
    for side in [-1,1]:
        z=side*.09
        for a,b in [((-.72,r,z),(-.2,.75,z)),((-.2,.75,z),(.55,.85,z)),((.55,.85,z),(.78,r,z)),((-.2,.75,z),(.08,r,z)),((.08,r,z),(-.72,r,z))]:m.cylinder(a,b,.028)
        m.cylinder((.5,1.05,z),(.78,r,z),.035)
    m.hull([(-.55,.76,.86,.12,.12),(.05,.72,.94,.19,.12),(.42,.7,.86,.12,.08)],0)
    m.box((.6,.09,.24),(-.36,.86,0),3)
    m.cylinder((.5,1.05,-.35),(.5,1.05,.35),.023,1)
    m.box((.36,.35,.3),(.0,.52,0),2)
    m.cylinder((-.7,.48,.23),(.25,.42,.23),.05)
    m.box((.08,.15,.18),(.62,.9,0),5)
    m.box((.08,.08,.16),(-.77,.83,0),6)


def trailer(m):
    m.box((10,.18,2.45),(0,1.2,0),2)
    for x in [-3,-2,-1]:
        for side in [-1,1]:m.wheel(x,.5,side*1.1,.5,.3)
    for side in [-1,1]:m.box((10,.65,.07),(0,1.6,side*1.2),0)
    for z in [-.8,.8]:m.box((.12,.9,.12),(2,.73,z),2)
    m.cylinder((4.0,1.2,0),(4.0,.95,0),.08)


def vessel(m,kind):
    submarine=kind=='submarine';carrier=kind=='carrier';war=kind=='warship'
    length=110 if carrier else (58 if war else (38 if submarine else 9));width=26 if carrier else (9 if war else (5 if submarine else 3));height=5 if carrier else (3.5 if war else (4 if submarine else 1.3))
    m.hull([(-length/2,0,height*.55,width*.2,width*.34),(-length*.35,-height*.4,height,width*.38,width*.5),(length*.32,-height*.4,height,width*.35,width*.5),(length/2,height*.1,height*.75,.03,.05)],8 if kind=='boat' else 0)
    if submarine:
        m.box((length*.7,.1,width*.4),(0,height+.05,0),2)
        m.hull([(-4,height,height+3,.8,.6),(3,height,height+3,.8,.6)],0)
        m.cylinder((0,height+2.8,0),(0,height+5,0),.12)
        m.box((3,.15,width*1.6),(-length*.38,height*.3,0),0)
        m.box((4,3,.15),(-length*.4,height*.3,0),0)
    elif carrier:
        m.box((length,.35,width),(0,height+.2,0),0)
        m.box((18,6,5),(-5,height+3.4,8),0)
        m.box((12,2,7),(-4,height+7.4,8),2)
        for x in range(-48,49,6):m.box((3,.015,.14),(x,height+.39,-4),8)
        for z in [-5,5]:m.box((length*.85,.015,.12),(0,height+.39,z),8)
        m.cylinder((-4,height+8,8),(-4,height+16,8),.2)
    else:
        cabin(m,length*.1,-length*.2,height=height+(4 if war else 1.9),width=width*.5,floor=height,paint=0 if war else 8)
        m.cylinder((0,height,0),(0,height+(10 if war else 3.5),0),.12)
        for side in [-1,1]:
            z=side*width*.42
            for x in [-length*.35,0,length*.3]:m.cylinder((x,height,z),(x,height+1,z),.025)
            m.cylinder((-length*.35,height+1,z),(length*.3,height+1,z),.025)
        if war:
            # Fictional unarmed deck fittings, no functional weapons simulation.
            for x in [-length*.3,length*.3]:m.cylinder((x,height,0),(x,height+1,0),1.4,2,20)


def aircraft(m,kind):
    heli='helicopter' in kind;attack=kind=='attack_helicopter';fighter=kind=='fighter_jet'
    length=12 if heli else (14 if fighter else 10);span=3 if heli else (9 if fighter else 12)
    m.hull([(-length/2,1.3,1.6,.06,.08),(-length*.15,.8,2.4,.55,.55),(length*.25,.85,2.2,.7,.55),(length/2,1.2,1.65,.05,.06)],0)
    cabin(m,length*.28,0,height=2.15,width=1.2,floor=1.0,paint=0)
    if heli:
        for z in [-.8,.8]:
            m.cylinder((-1,.65,z),(2,.65,z),.05)
            for x in [0,1.5]:m.cylinder((x,1.3,z*.5),(x,.65,z),.035)
        m.cylinder((-.1,2.2,0),(-.1,3.0,0),.1)
        for angle in [0,math.pi/2]:
            x,z=5.8*math.cos(angle),5.8*math.sin(angle)
            m.cylinder((-.1-x,3.0,-z),(-.1+x,3.0,z),.09,2,8)
        m.box((2,1.5,.08),(-length*.43,2,0),0)
        m.cylinder((-length*.43,2,-.25),(-length*.43,2,.25),.09)
        m.cylinder((-length*.43-1,2,-.3),(-length*.43+1,2,-.3),.05,2)
        if not attack:
            for x in [-2,-1,0]:
                for side in [-1,1]:m.box((.5,.5,.025),(x,1.65,side*.58),4)
    else:
        for side in [-1,1]:
            # Tapered wings modeled as closed lofts oriented along span.
            tip=( -2 if fighter else -.4,1.25,side*span/2)
            for a,b,c in [((1,1.3,0),(-3,1.3,0),tip),((1,1.24,0),tip,(-3,1.24,0))]:m.triangle(a,b,c,0)
            m.box((1.7,.07,2.8),(-length*.36,1.8,side*1.3),0)
        m.box((1.9,2,.09),(-length*.39,2.3,0),0)
        for x,z in [(length*.25,0),(-1,-1),(-1,1)]:
            m.cylinder((x,1.1,z),(x,.3,z),.035);m.wheel(x,.28,z,.28,.13)
        if fighter:
            for side in [-1,1]:m.cylinder((-length*.4,1.3,side*.25),(-length*.5,1.3,side*.25),.24,2,20)
        else:
            m.cylinder((length*.5,1.45,0),(length*.5+.2,1.45,0),.14)
            m.cylinder((length*.5+.25,.15,0),(length*.5+.25,2.75,0),.045,1)


def locomotive(m):
    m.box((13,.4,2.9),(0,1,0),2)
    m.box((9,2.6,2.65),(-1.5,2.4,0),0)
    cabin(m,6,2.8,height=4.0,width=2.8,floor=1.2,paint=0)
    for x in [-4.8,-3.7,3.7,4.8]:
        for side in [-1,1]:m.wheel(x,.5,side*.82,.5,.16)
    for side in [-1,1]:
        for x in range(-5,2):m.box((.5,1.4,.025),(x,2.4,side*1.34),1)
        m.cylinder((-6,1.5,side*1.4),(6,1.5,side*1.4),.025)
    for x in [-6.8,6.8]:m.box((.5,.3,.35),(x,.85,0),2)


def building(m,kind):
    levels=4 if kind=='residence_4floors' else (2 if kind in ['townhouse','hospital','police_station'] else 1)
    w,d= (16,12) if levels==4 else ((20,14) if kind in ['hospital','fire_station'] else (10,9))
    garage=kind in ['fire_station','farm_barn'];opening=4.5 if garage else 1.6
    for floor in range(levels):
        y=3*floor
        # Open central stairwell; slabs do not seal stair circulation.
        for side in [-1,1]:m.box(((w-3)/2,.2,d),(side*(w+3)/4,y-.1,0),9)
        for z in [-d/3,d/3]:m.box((3,.2,d/3),(0,y-.1,z),9)
        for z in [-d/2,d/2]:
            if floor==0 and z<0:
                for side in [-1,1]:m.box(((w-opening)/2,3,.22),(side*(w+opening)/4,y+1.5,z),8)
                m.box((opening,.5,.22),(0,y+2.75,z),8)
            else:
                m.box((w,.9,.22),(0,y+.45,z),8);m.box((w,.8,.22),(0,y+2.6,z),8)
                for x in range(-int(w/2),int(w/2)+1,3):m.box((.35,1.3,.22),(x,y+1.55,z),8)
        for side in [-1,1]:
            m.box((.22,3,d),(side*w/2,y+1.5,0),8)
            if floor>0:
                m.box((w*.38,.15,1.4),(side*w*.28,y-.08,-d/2-.7),9)
                for x in [side*w*.1,side*w*.45]:m.cylinder((x,y,-d/2-1.4),(x,y+1.05,-d/2-1.4),.025)
                m.cylinder((side*w*.1,y+1.05,-d/2-1.4),(side*w*.45,y+1.05,-d/2-1.4),.025)
        if floor<levels-1:
            for step in range(10):
                m.box((1.1,.15,.28),(-.7,y+(step+1)*.15-.075,-1.2+step*.28),9)
                m.box((1.1,.15,.28),(.7,y+1.5+(step+1)*.15-.075,1.32-step*.28),9)
            m.box((2.7,.18,.6),(0,y+1.41,1.8),9)
    roof=levels*3
    m.box((w+.5,.2,d+.5),(0,roof,0),11 if levels<3 else 9)
    if kind=='hospital':
        m.box((1.8,.3,.05),(0,roof-1,-d/2-.15),6);m.box((.3,1.8,.05),(0,roof-1,-d/2-.17),6)
    if kind=='police_station':m.box((4,.6,.05),(0,2.4,-d/2-.15),7)
    if kind=='farm_barn':
        for x in [-3,3]:m.box((2.2,1.1,3),(x,.55,1.5),10)

VEHICLES = ['transport_truck','semi_truck','farm_tractor','buggy','dirt_bike','motorcycle','kart','formula_one','car','suv','van','police','gendarmerie','fire_engine','ambulance','armored_van','monster_truck','boat','carrier','warship','submarine','train','airplane','fighter_jet','attack_helicopter','transport_helicopter']
BUILDINGS = ['residence_4floors','townhouse','hospital','police_station','fire_station','farm_barn']


def generate(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);models=[]
    for name in VEHICLES+['semi_trailer']+BUILDINGS:
        m=Mesh()
        if name in ['buggy','kart','formula_one']:racer(m,name)
        elif name in ['motorcycle','dirt_bike']:motorcycle(m,name=='dirt_bike')
        elif name=='farm_tractor':tractor(m)
        elif name=='semi_trailer':trailer(m)
        elif name in ['boat','carrier','warship','submarine']:vessel(m,name)
        elif name=='train':locomotive(m)
        elif name in ['airplane','fighter_jet','attack_helicopter','transport_helicopter']:aircraft(m,name)
        elif name in BUILDINGS:building(m,name)
        else:road_vehicle(m,name)
        data,dims,triangles=m.export(name);target=output/(name+'.glb')
        if target.exists() and target.read_bytes()!=data:raise RuntimeError('Existing art preserved: '+str(target))
        if not target.exists():target.write_bytes(data)
        kind='building' if name in BUILDINGS else ('prop' if name=='semi_trailer' else 'vehicle')
        folder='Buildings/Expansion1' if kind=='building' else ('Props/Expansion1' if kind=='prop' else 'Vehicles/'+name)
        models.append(dict(id=name,kind=kind,file=target.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),triangles=triangles,dimensionsMetresYUp=dims,objectPath='/Game/Anomalia/'+folder+'/SM_'+name,state='ORIGINAL_GEOMETRY_PROTOTYPE',drivingTested=False,manufacturerReplica=False))
    manifest=dict(schemaVersion=1,author='CMD / ANOMALIA',license='Original project geometry; ANOMALIA project terms',notes='Original proportions for fictional game vehicles, no manufacturer replica, no textures, rigging or final physics. Not a completed realism pass.',models=models)
    target=output/'manifest.json';raw=json.dumps(manifest,indent=2)+'\n'
    if target.exists() and target.read_text()!=raw:raise RuntimeError('Existing manifest preserved')
    target.write_text(raw)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'unreal/SourceAssets/Expansion1');args=parser.parse_args()
    result=generate(args.output);print(json.dumps(dict(models=len(result['models']),bytes=sum(m['bytes'] for m in result['models']),state='ORIGINAL_GEOMETRY_PROTOTYPES_NOT_PLAYTESTED')))
