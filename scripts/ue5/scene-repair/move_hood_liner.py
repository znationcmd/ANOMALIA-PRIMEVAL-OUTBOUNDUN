"""Preserve original E39 lining geometry and make it follow the actual opening bonnet.

Operates on GLB buffers without changing original UVs, normals, texture images or materials.
"""
import struct,json,copy,math,hashlib
from pathlib import Path
class GLB:
 def __init__(self,path):
  data=Path(path).read_bytes();magic,version,length=struct.unpack_from('<III',data)
  if (magic,version,length)!=(0x46546c67,2,len(data)):raise ValueError('GLB identity')
  jlen,jtype=struct.unpack_from('<II',data,12);self.j=json.loads(data[20:20+jlen]);off=20+jlen
  blen,btype=struct.unpack_from('<II',data,off);self.b=bytearray(data[off+8:off+8+blen])
 def values(self,index):
  a=self.j['accessors'][index];v=self.j['bufferViews'][a['bufferView']]
  count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']]
  size=struct.calcsize('<'+fmt*count);stride=v.get('byteStride',size);start=v.get('byteOffset',0)+a.get('byteOffset',0)
  return [struct.unpack_from('<'+fmt*count,self.b,start+i*stride) for i in range(a['count'])]
 def append(self,values,kind='VEC3',component=5126):
  while len(self.b)%4:self.b.append(0)
  start=len(self.b);fmt={5126:'f',5125:'I'}[component]
  for row in values:self.b.extend(struct.pack('<'+fmt*len(row),*row))
  vi=len(self.j['bufferViews']);self.j['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(self.b)-start})
  a={'bufferView':vi,'componentType':component,'count':len(values),'type':kind}
  if kind=='VEC3':a.update(min=[min(v[i] for v in values) for i in range(3)],max=[max(v[i] for v in values) for i in range(3)])
  ai=len(self.j['accessors']);self.j['accessors'].append(a);return ai
 def save(self,path):
  self.j['buffers'][0]['byteLength']=len(self.b);j=json.dumps(self.j,separators=(',',':')).encode()
  j+=b' '*((-len(j))%4);b=bytes(self.b);b+=b'\0'*((-len(b))%4)
  Path(path).write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
def repair(source,destination):
 source=Path(source);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
 body=GLB(source/'body.glb');hood=GLB(source/'hood.glb');pivot=[.927,.978,0];moved=0;area=0
 for p in body.j['meshes'][0]['primitives']:
  material=body.j['materials'][p['material']]
  if material['name']!='mottled':continue
  positions=body.values(p['attributes']['POSITION']);ids=[v[0] for v in body.values(p['indices'])] if 'indices' in p else list(range(len(positions)))
  selected=[];kept=[]
  for k in range(0,len(ids),3):
   tri=ids[k:k+3];pts=[positions[i] for i in tri]
   is_liner=all(.90<v[0]<2.36 and .50<v[1]<1.05 and abs(v[2])<.87 for v in pts)
   (selected if is_liner else kept).extend(tri)
   if is_liner:
    a,b,c=pts;u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];area+=math.sqrt(sum(x*x for x in cross))/2
  if not selected:continue
  if not kept:raise RuntimeError('Unexpected whole lining primitive; preserve source')
  p['indices']=body.append([(i,) for i in kept],'SCALAR',5125)
  materials=[i for i,m in enumerate(hood.j['materials']) if m.get('name')==material['name']]
  if len(materials)!=1:raise RuntimeError('Matching original hood material required')
  new={'attributes':{},'material':materials[0],'mode':4}
  for semantic,index in p['attributes'].items():
   a=body.j['accessors'][index];values=body.values(index)
   data=[tuple(v-pivot[k] for k,v in enumerate(values[i])) if semantic=='POSITION' else values[i] for i in selected]
   new['attributes'][semantic]=hood.append(data,a['type'],a['componentType'])
  hood.j['meshes'][0]['primitives'].append(new);moved+=len(selected)//3
 if not 0.5<area<5.0 or moved<2:raise RuntimeError('Unexpected hood liner selection '+str((area,moved)))
 # Retire only the broad, shallow stand-in cap spanning the engine aperture.
 # Original model remains intact in v7; the new detailed bay replaces this cap.
 cap_area=0
 def split(poly,plane):
  inside=[];outside=[]
  for i,a in enumerate(poly):
   b=poly[(i+1)%len(poly)];da=plane(a['POSITION']);db=plane(b['POSITION'])
   (inside if da>=0 else outside).append(a)
   if (da>=0)!=(db>=0):
    t=da/(da-db);v={k:tuple(x+(b[k][j]-x)*t for j,x in enumerate(val)) for k,val in a.items()};inside.append(v);outside.append(v)
  return inside,outside
 def triangulate(poly):return [[poly[0],poly[i],poly[i+1]] for i in range(1,len(poly)-1)]
 planes=[lambda p:p[0]-1.04,lambda p:2.22-p[0],lambda p:p[1]-.60,lambda p:1.0-p[1],lambda p:p[2]+.66,lambda p:.66-p[2]]
 for p in body.j['meshes'][0]['primitives']:
  if body.j['materials'][p['material']]['name']!='frame':continue
  attrs={key:body.values(index) for key,index in p['attributes'].items()};ids=[v[0] for v in body.values(p['indices'])] if 'indices' in p else list(range(len(attrs['POSITION'])))
  kept=[]
  for k in range(0,len(ids),3):
   tri=[{key:vals[i] for key,vals in attrs.items()} for i in ids[k:k+3]];a,b,c=[v['POSITION'] for v in tri]
   u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in cross))
   if length<1e-10 or abs(cross[1])/length<.85:kept.append(tri);continue
   inside=tri
   for plane in planes:
    if len(inside)<3:break
    inside,outside=split(inside,plane);kept.extend(triangulate(outside))
   for cut in triangulate(inside):
    a,b,c=[v['POSITION'] for v in cut];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];cap_area+=math.sqrt(sum(x*x for x in [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]))/2
  if not kept:raise RuntimeError('Engine aperture removed structural frame')
  old=p['attributes'].copy();p['attributes']={key:body.append([vertex[key] for tri in kept for vertex in tri],body.j['accessors'][index]['type'],body.j['accessors'][index]['componentType']) for key,index in old.items()};p.pop('indices',None)
 if not .5<cap_area<3.5:raise RuntimeError('Unexpected stand-in engine cap area '+str(cap_area))
 body.save(destination/'body.glb');hood.save(destination/'hood.glb')
 report={'state':'ORIGINAL_HOOD_LINER_MOVED_WITHOUT_REMOVING_AREA','retiredEngineCapAreaM2':cap_area,'trianglesMoved':moved,'surfaceAreaM2':area,'pivotMetresYUp':pivot,'sourceBodySha256':hashlib.sha256((source/'body.glb').read_bytes()).hexdigest(),'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.glob('*.glb')}}
 (destination/'liner-repair.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('destination');a=p.parse_args();print(json.dumps(repair(a.source,a.destination)))
