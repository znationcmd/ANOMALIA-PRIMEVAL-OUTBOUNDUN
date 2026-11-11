"""Original 50m concrete viaduct span: deck, footways, girders and tubular guardrails.
Reuses the project's existing CC0 Poly Haven albedo images; not final production art.
"""
import base64,hashlib,json,re,struct
from pathlib import Path
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'unreal/SourceAssets/Infrastructure/Bridge'
parts=[[],[],[]] # asphalt, concrete, steel

def box(size,at,material):
 m=trimesh.creation.box(extents=size);m.apply_translation(at);parts[material].append(m)
def rail(a,b,r=.045):
 parts[2].append(trimesh.creation.cylinder(radius=r,segment=np.array([a,b]),sections=12))
# X length, Y up, Z width. Engine's glTF importer converts metres/Y-up into cm/Z-up.
box([50,.5,11],[0,-.27,0],1)
box([50,.035,8],[0,-.0175,0],0)
for z in [-4.65,4.65]:box([50,.18,1.3],[0,.09,z],1)
for z in [-3,-1,1,3]:
 box([50,.2,.65],[0,-.6,z],1);box([50,1.15,.16],[0,-1.275,z],1);box([50,.2,.6],[0,-1.95,z],1)
for x in [-24.7,0,24.7]:box([.6,.6,9],[x,-1.75,0],1)
for z in [-5.35,5.35]:
 for y in [.65,1.28]:rail([-25,y,z],[25,y,z])
 for x in np.linspace(-25,25,14):rail([x,.18,z],[x,1.3,z],.055)
# White lane markings are actual surface geometry, not collision-blocking cubes.
for x in np.arange(-23,25,8):box([4,.005,.12],[x,.004,0],2)

blob=bytearray();views=[];access=[]
def put(data,target=None):
 while len(blob)%4:blob.append(0)
 offset=len(blob);blob.extend(data);v=dict(buffer=0,byteOffset=offset,byteLength=len(data))
 if target:v['target']=target
 views.append(v);return len(views)-1

def accessor(array,kind,component):
 a=np.ascontiguousarray(array);v=put(a.tobytes(),34963 if kind=='SCALAR' else 34962)
 spec=dict(bufferView=v,componentType=component,count=len(a),type=kind)
 if kind=='VEC3':spec.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
 access.append(spec);return len(access)-1
primitives=[]
for mat,geometries in enumerate(parts):
 m=trimesh.util.concatenate(geometries);m.unmerge_vertices()
 vertices=np.array(m.vertices,dtype='<f4');normals=np.array(m.vertex_normals,dtype='<f4')
 # World-sized texture repeats, with planar UVs selected per face normal.
 uv=np.empty((len(vertices),2),dtype='<f4');n=np.argmax(abs(normals),axis=1)
 for axis,coords in [(0,[2,1]),(1,[0,2]),(2,[0,1])]:uv[n==axis]=vertices[n==axis][:,coords]/4
 p=dict(attributes=dict(POSITION=accessor(vertices,'VEC3',5126),NORMAL=accessor(normals,'VEC3',5126),TEXCOORD_0=accessor(uv,'VEC2',5126)),indices=accessor(np.asarray(m.faces.reshape(-1),dtype='<u4'),'SCALAR',5125),material=mat,mode=4)
 primitives.append(p)
images=[]
for name in ['asphalt_02','concrete_wall_001']:
 text=(ROOT/'src/textures'/f'{name}.js').read_text();data=base64.b64decode(re.search(r'base64,([^";]+)',text).group(1));images.append(dict(bufferView=put(data),mimeType='image/jpeg',name=name))
materials=[]
for index,name in enumerate(['Asphalt','Concrete','Steel']):
 pbr=dict(metallicFactor=.8 if index==2 else 0,roughnessFactor=.4 if index==2 else .9)
 if index<2:pbr['baseColorTexture']=dict(index=index)
 else:pbr['baseColorFactor']=[.65,.67,.68,1]
 materials.append(dict(name=name,pbrMetallicRoughness=pbr))
doc=dict(asset=dict(version='2.0',generator='CMD original ANOMALIA viaduct span v1'),scenes=[dict(nodes=[0])],scene=0,nodes=[dict(mesh=0)],meshes=[dict(name='ANOMALIA_Viaduct50m',primitives=primitives)],materials=materials,images=images,textures=[dict(source=0,sampler=0),dict(source=1,sampler=0)],samplers=[dict(wrapS=10497,wrapT=10497)],buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=access)
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob+=b'\0'*((-len(blob))%4)
result=struct.pack('<III',0x46546c67,2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
OUT.mkdir(parents=True,exist_ok=True);p=OUT/'bridge50m.glb'
if p.exists() and p.read_bytes()!=result:raise RuntimeError('Existing source differs; choose a new version')
p.write_bytes(result)
meta=dict(schemaVersion=1,sha256=hashlib.sha256(result).hexdigest(),bytes=len(result),spanMeters=50,widthMeters=11,originalGeometry='CMD / ANOMALIA',textures=[dict(name=n,license='CC0-1.0',source='https://polyhaven.com/a/'+n) for n in ['asphalt_02','concrete_wall_001']],notes='Original structural model; no final art, vehicle drive test or rendered quality claim.')
(OUT/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
