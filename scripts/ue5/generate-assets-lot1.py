"""Original CMD geometry, metres/Y-up. Explicit versioned files; never overwrite art."""
import hashlib,json,math,struct
from pathlib import Path
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'unreal/SourceAssets/OriginalLot1'
MATERIALS=[('Paint',[.12,.27,.17,1],.35,.25),('Rubber',[.025,.027,.03,1],0,.92),('Steel',[.3,.32,.35,1],.85,.32),('Seat',[.08,.065,.045,1],0,.85),('Plaster',[.77,.74,.63,1],0,.95),('Roof',[.28,.11,.065,1],0,.9),('Timber',[.25,.12,.055,1],0,.85),('Concrete',[.4,.42,.4,1],0,.95),('Hull',[.82,.84,.83,1],.1,.3)]
parts=[]
def add(m,mat):parts.append((m,mat));return m
def box(size,at,mat,angle=0):
 m=trimesh.creation.box(extents=size)
 if angle:m.apply_transform(trimesh.transformations.rotation_matrix(angle,[0,0,1]))
 m.apply_translation(at);return add(m,mat)
def tube(a,b,r,mat=2):return add(trimesh.creation.cylinder(radius=r,segment=np.array([a,b]),sections=20),mat)
def oval(at,scale,mat):
 m=trimesh.creation.icosphere(subdivisions=3);m.apply_scale(scale);m.apply_translation(at);return add(m,mat)
def loft(stations,mat):
 # (x, centre y, half-width, half-height), joined elliptical rings.
 n=40;v=[];f=[]
 for x,y,w,h in stations:
  for k in range(n):
   a=2*math.pi*k/n;v.append([x,y+h*math.sin(a),w*math.cos(a)])
 for i in range(len(stations)-1):
  for k in range(n):
   a=i*n+k;b=i*n+(k+1)%n;c=b+n;d=a+n;f.extend([[a,b,d],[b,c,d]])
 for ring,reverse in [(0,True),(len(stations)-1,False)]:
  centre=len(v);v.append([stations[ring][0],stations[ring][1],0])
  for k in range(n):
   a=ring*n+k;b=ring*n+(k+1)%n;f.append([centre,b,a] if reverse else [centre,a,b])
 return add(trimesh.Trimesh(v,f,process=False),mat)
def wheel(x,z,r=.32):
 m=trimesh.creation.torus(major_radius=r*.72,minor_radius=r*.28,major_sections=32,minor_sections=12);m.apply_translation([x,r,z]);add(m,1)
 tube([x,r,z-.1],[x,r,z+.1],r*.48)
 for k in range(24):
  a=2*math.pi*k/24
  box([r*.12,r*.09,.23],[x+r*.96*math.cos(a),r+r*.96*math.sin(a),z],1,a)
 for k in range(6):
  a=2*math.pi*k/6;tube([x,r,z],[x+r*.4*math.cos(a),r+r*.4*math.sin(a),z],.015)
def quad():
 loft([(-1,.52,.28,.12),(-.7,.58,.4,.17),(.15,.61,.36,.19),(.75,.65,.38,.18),(1,.59,.22,.12)],0)
 box([.9,.1,.42],[-.22,.87,0],3);oval([.39,.83,0],[.36,.2,.27],0)
 for x in [-.7,.68]:
  tube([x,.36,-.63],[x,.36,.63],.045)
  for z in [-.57,.57]:
   wheel(x,z)
   oval([x,.67,z],[.46,.065,.23],0)
   tube([x-.16,.42,z*.7],[x+.08,.66,z],.035)
 for z in [-.4,.4]:tube([.32,.87,z],[.62,1.13,z],.025)
 tube([.62,1.13,-.43],[.62,1.13,.43],.025)
 for x in [-.92,.85]:
  for z in np.linspace(-.35,.35,5):tube([x-.12,.8,z],[x+.12,.8,z],.014)
 for z in [-.26,.26]:oval([1,.65,z],[.025,.065,.075],8)
def jetski():
 loft([(-1.55,.23,.08,.08),(-1.25,.27,.37,.21),(-.65,.29,.5,.26),(.45,.33,.53,.3),(1.2,.42,.33,.24),(1.55,.46,.015,.04)],8)
 loft([(-1.2,.47,.31,.06),(-.5,.64,.43,.2),(.48,.67,.4,.26),(1.12,.55,.2,.12)],0)
 oval([-.4,.87,0],[.78,.11,.23],3)
 tube([.42,.76,0],[.7,1.07,0],.06);tube([.7,1.07,-.32],[.7,1.07,.32],.025)
 for z in [-.43,.43]:box([1.2,.04,.14],[-.55,.54,z],1)
 tube([-1.62,.25,0],[-1.43,.25,0],.095)
def snowmobile():
 loft([(-1.25,.6,.24,.12),(-.5,.73,.32,.2),(.45,.68,.4,.25),(.95,.48,.3,.15),(1.17,.43,.05,.06)],0)
 oval([-.55,.94,0],[.65,.12,.23],3)
 # Continuous track belt, with actual exposed tread bars.
 for x in np.linspace(-1.2,.2,16):box([.055,.055,.48],[x,.07,0],1);box([.055,.055,.48],[x,.48,0],1)
 for x in [-1.1,0]:wheel(x,0,.23)
 for z in [-.55,.55]:
  loft_ski=[(.35,.1,.07,.025),(1.1,.1,.08,.025),(1.6,.23,.045,.02)]
  before=len(parts);loft(loft_ski,1)
  parts[before][0].apply_translation([0,0,z])
  tube([.7,.18,z],[.6,.6,z*.5],.035)
 tube([.25,.8,0],[.15,1.18,0],.045);tube([.15,1.18,-.37],[.15,1.18,.37],.024)
def zodiac():
 # Inflatable side tubes with tapered bow; open interior, outboard and benches.
 for z in [-.85,.85]:
  tube([-1.6,.44,z],[.9,.44,z],.29,0)
  oval([-1.6,.44,z],[.29,.29,.29],0)
 for side in [-1,1]:
  tube([.9,.44,side*.85],[1.93,.44,0],.29,0)
  oval([.9,.44,side*.85],[.29,.29,.29],0)
 oval([1.93,.44,0],[.29,.29,.29],0)
 box([3.15,.1,1.2],[-.25,.16,0],8);box([.1,.55,1.2],[-1.85,.4,0],6)
 for x in [-1,.0,.85]:box([.3,.08,1.2],[x,.56,0],6)
 oval([-2.12,.63,0],[.27,.34,.2],1);tube([-2.14,.45,0],[-2.14,-.15,0],.075)
 tube([-2.14,-.15,-.16],[-2.14,-.15,.16],.05)
 for z in [-.85,.85]:
  tube([-1.5,.77,z],[.8,.77,z],.018,1)
  for x in [-1.4,-.4,.6]:tube([x,.65,z],[x,.78,z],.02)
def building(garage=False):
 # Local X width, Z depth. Floor at y=0, front at z=-depth/2.
 w,d,h=(8,9,3.4) if garage else (10,8,3)
 box([w,.2,d],[0,-.1,0],7)
 opening=4.4 if garage else 1.2
 for side in [-1,1]:box([(w-opening)/2,h,.24],[side*(w+opening)/4,h/2,-d/2],4)
 box([opening,h-2.5,.24],[0,(h+2.5)/2,-d/2],4)
 box([w,h,.24],[0,h/2,d/2],4)
 # Side walls have actual window holes, with frames and sills; no blocking glass.
 for side in [-1,1]:
  x=side*w/2
  box([.24,1,d],[x,.5,0],4);box([.24,h-2.2,d],[x,(h+2.2)/2,0],4)
  for z0,z1 in [(-d/2,-1.0),(1.,d/2)]:box([.24,1.2,z1-z0],[x,1.6,(z0+z1)/2],4)
  for y in [1.,2.2]:box([.28,.08,2.2],[x,y,0],6)
  for z in [-1,1]:box([.28,1.2,.08],[x,1.6,z],6)
 # Double-sided pitched roof planes and individual roof courses.
 rise=1.7;slope=math.atan2(rise,w/2+.35);length=math.hypot(w/2+.35,rise)
 for side in [-1,1]:
  box([length,.15,d+.7],[side*(w/2+.35)/2,h+rise/2,0],5,-side*slope)
  for z in np.arange(-d/2-.25,d/2+.35,.32):
   tube([0,h+rise+.09,z],[side*(w/2+.35),h+.09,z],.035,5)
 # Actual gable triangles, not a solid bounding box across rooms.
 for z in [-d/2,d/2]:
  m=trimesh.Trimesh(vertices=[[-w/2,h,z],[w/2,h,z],[0,h+rise,z]],faces=[[0,1,2],[2,1,0]],process=False);add(m,4)
 for side in [-1,1]:box([.12,2.5,.32],[side*opening/2,1.25,-d/2],6)
 box([opening+.2,.12,.32],[0,2.5,-d/2],6)
 if not garage:
  # Porch, stairs, chimney and interior partition with its own opening.
  box([3,.15,1.5],[0,-.02,-d/2-.75],7)
  box([.7,1.8,.7],[w*.3,h+1,1.5],7)
  for z in [-d/2,-2.,2.,d/2]:
   if abs(z)>1:box([.12,2.6,1.8],[1.8,1.3,z/2],4)
 else:
  for y in np.arange(2.65,3.35,.12):box([opening,.045,.12],[0,y,-d/2-.15],2)

def apartment_block():
 w,d,h=18,12,3
 for floor in range(8):
  base=floor*h
  # Slabs around an open central stairwell, preserving circulation on every level.
  for side in [-1,1]:box([7.5,.2,d],[side*5.25,base-.1,0],7)
  for z in [-3,4.5]:box([3,.2,6 if z<0 else 3],[0,base-.1,z],7)
  for z in [-d/2,d/2]:
   for x in [-7.5,-4.5,-1.5,1.5,4.5,7.5]:
    if floor==0 and z<0 and abs(x)==1.5:
     box([1.0,h,.25],[x*1.6,base+h/2,z],4)
     box([2.0,.6,.25],[x,base+2.7,z],4)
    else:
     box([3,.95,.25],[x,base+.475,z],4)
     box([3,.85,.25],[x,base+2.575,z],4)
     for dx in [-1.25,1.25]:box([.5,1.2,.25],[x+dx,base+1.55,z],4)
     for y in [base+.95,base+2.15]:box([2.1,.07,.28],[x,y,z],6)
     for dx in [-1.,1.]:box([.07,1.2,.28],[x+dx,base+1.55,z],6)
  for side in [-1,1]:box([.25,h,d],[side*w/2,base+h/2,0],4)
  # Apartment partitions stop at internal doors instead of sealing each floor.
  for side in [-1,1]:
   for z in [-4.5,4.5]:box([.12,2.7,3],[side*1.5,base+1.35,z],4)
   for x in [side*4.5]:box([.12,2.7,4],[x,base+1.35,3.8],4)
  if floor<7:
   # Two 1.5m flights, 15cm rises and 28cm treads, joined by a landing.
   for step in range(10):
    box([1.05,.15,.28],[-.7,base+(step+1)*.15-.075,.14+step*.28],7)
    box([1.05,.15,.28],[.7,base+1.5+(step+1)*.15-.075,2.66-step*.28],7)
   box([2.7,.18,.6],[0,base+1.41,3.1],7)
   for x in [-1.27,1.27]:tube([x,base+.95,0],[x,base+2.45,2.8],.035)
  if floor>0:
   for x in [-6,6]:
    box([4.4,.18,1.5],[x,base-.09,-6.75],7)
    for xx in [x-2.15,x+2.15]:tube([xx,base,-7.45],[xx,base+1.05,-7.45],.035)
    tube([x-2.15,base+1.05,-7.45],[x+2.15,base+1.05,-7.45],.035)
    for xx in np.arange(x-2.05,x+2.1,.2):tube([xx,base,-7.45],[xx,base+1.05,-7.45],.012)
 box([18.6,.25,12.6],[0,24,0],7)
 for z in [-6.2,6.2]:box([18.6,.5,.15],[0,24.25,z],7)

def beach_villa():
 building(False)
 # Pool shell outside the house: basin, coping, water surface and ladder.
 cx,cz=0,-10
 box([8.4,.2,4.4],[cx,-1.8,cz],7)
 for x in [-4.1,4.1]:box([.2,1.8,4.4],[x,-.9,cz],7)
 for z in [cz-2.1,cz+2.1]:box([8.4,1.8,.2],[0,-.9,z],7)
 for x in [-4.3,4.3]:box([.6,.12,5.2],[x,.06,cz],4)
 for z in [cz-2.3,cz+2.3]:box([8.6,.12,.6],[0,.06,z],4)
 # Colour material only for now; swimming/buoyancy are separate gameplay work.
 box([8,.015,4],[0,-.2,cz],8)
 for x in [2.5,3.]:
  tube([x,-1.6,cz+1.8],[x,.6,cz+1.8],.035)
  tube([x,.6,cz+1.8],[x,.6,cz+2.6],.035)
 for y in [-1.3,-.95,-.6,-.25]:tube([2.5,y,cz+1.8],[3.,y,cz+1.8],.025)
 for x in [-4,4]:tube([x,0,-5],[x,2.7,-5],.09,6)
 for z in np.arange(-7.,-4.,.25):box([9,.1,.1],[0,2.75,z],6)

def write(name,kind,fn):
 parts.clear();fn();blob=bytearray();views=[];access=[];primitives=[]
 def array(a,typ,comp,target):
  a=np.ascontiguousarray(a)
  while len(blob)%4:blob.append(0)
  views.append(dict(buffer=0,byteOffset=len(blob),byteLength=a.nbytes,target=target));blob.extend(a.tobytes())
  spec=dict(bufferView=len(views)-1,componentType=comp,count=len(a),type=typ)
  if typ=='VEC3':spec.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
  access.append(spec);return len(access)-1
 for mat in range(len(MATERIALS)):
  meshes=[m for m,i in parts if i==mat]
  if not meshes:continue
  m=trimesh.util.concatenate(meshes)
  primitives.append(dict(attributes=dict(POSITION=array(np.array(m.vertices,dtype='<f4'),'VEC3',5126,34962),NORMAL=array(np.array(m.vertex_normals,dtype='<f4'),'VEC3',5126,34962)),indices=array(np.asarray(m.faces.reshape(-1),dtype='<u4'),'SCALAR',5125,34963),material=mat,mode=4))
 doc=dict(asset=dict(version='2.0',generator='CMD Original Lot1 v1'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0)],meshes=[dict(name='SM_'+name,primitives=primitives)],materials=[dict(name=n,pbrMetallicRoughness=dict(baseColorFactor=([.05,.38,.58,1] if name=='beach_villa_pool_v1' and n=='Hull' else c),metallicFactor=metal,roughnessFactor=rough),doubleSided=True) for n,c,metal,rough in MATERIALS],buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=access)
 j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob+=b'\0'*((-len(blob))%4)
 data=struct.pack('<III',0x46546c67,2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
 suffix='_repaired' if name=='hlm_8floors_v1' else ('_v2' if name in ['zodiac','beach_villa_pool_v1'] else '')
 path=OUT/(name+suffix+'.glb');OUT.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=data:raise RuntimeError('Existing original preserved: '+name)
 if not path.exists():path.write_bytes(data)
 v=np.vstack([m.vertices for m,_ in parts]);dims=(v.max(axis=0)-v.min(axis=0)).tolist()
 return dict(id=name,kind=kind,file=path.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),dimensionsMetresYUp=dims,triangles=sum(len(m.faces) for m,_ in parts),objectPath=('/Game/Anomalia/Vehicles/'+name+'/SM_'+name if kind=='vehicle' else '/Game/Anomalia/Buildings/Lot1/SM_'+name),state='SOURCE_ONLY',notes='Original geometry and PBR colour materials; no textures, animation or driving validation.')
def main():
 models=[write(n,k,f) for n,k,f in [('quad','vehicle',quad),('snowmobile','vehicle',snowmobile),('jetski','vehicle',jetski),('zodiac','vehicle',zodiac),('coastal_house_v1','building',building),('garage_v1','building',lambda:building(True)),('hlm_8floors_v1','building',apartment_block),('beach_villa_pool_v1','building',beach_villa)]]
 (OUT/'manifest.json').write_text(json.dumps(dict(schemaVersion=1,author='CMD / ANOMALIA',license='Original project assets; redistribution subject to ANOMALIA project terms',models=models),indent=2)+'\n')
 print(json.dumps(models,indent=2))
if __name__=='__main__':main()
