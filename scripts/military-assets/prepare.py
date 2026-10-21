"""Pinned public Savage X3D visual references to assembled static GLB; no source scripts run."""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import shlex
import struct
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import assimp_py
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]


def sha(data):return hashlib.sha256(data).hexdigest()
def preserve(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise RuntimeError('Existing artist output preserved: '+str(path))
    else:path.write_bytes(data)


def retrieve(url,digest,size,cache):
    if not url.startswith('https://savage.nps.edu/Savage/'):raise RuntimeError('Unapproved asset source')
    file=cache/digest
    raw=file.read_bytes() if file.exists() else urllib.request.urlopen(url,timeout=60).read()
    if sha(raw)!=digest or len(raw)!=size:raise RuntimeError('Source hash mismatch: '+url)
    preserve(file,raw);return raw


def prepare(entry,cache):
    raw=retrieve(entry['url'],entry['sha256'],entry['bytes'],cache);root=ET.fromstring(raw)
    if any(root.iter('Inline')) or any(root.iter('ProtoInstance')):raise RuntimeError('External geometry needs dedicated complete-scene import')
    defs={n.get('DEF'):n for n in root.iter() if n.get('DEF')}
    # Some archive files USE coordinates declared inside empty shapes; resolve before dropping empties.
    def expand(node,stack=()):
        if len(stack)>128:raise RuntimeError('Recursive scene definition')
        for index,child in enumerate(list(node)):
            name=child.get('USE')
            if name:
                if name in stack or name not in defs:raise RuntimeError('Invalid shared scene definition')
                replacement=copy.deepcopy(defs[name]);replacement.attrib.pop('DEF',None)
                node.remove(child);node.insert(index,replacement);expand(replacement,stack+(name,))
            else:expand(child,stack)
    expand(root)
    for parent in root.iter():
        for child in list(parent):
            if child.tag in ['Script','Sound','AudioClip','ROUTE','TimeSensor','PositionInterpolator','OrientationInterpolator'] or (child.tag=='IndexedFaceSet' and not child.get('coordIndex','').strip()):parent.remove(child)
    media={item['url']:item for item in entry['media']};images={};missing=[]
    for node in root.iter('ImageTexture'):
        urls=shlex.split(node.get('url',''))
        if not urls:continue
        url=urllib.parse.urljoin(entry['url'],urls[0]);item=media[url]
        if item.get('unavailable'):missing.append(url);node.set('url','');continue
        data=retrieve(url,item['sha256'],item['bytes'],cache)
        with Image.open(io.BytesIO(data)) as image:
            image=image.convert('RGBA');image.thumbnail((1024,1024));stream=io.BytesIO();image.save(stream,format='PNG');png=stream.getvalue()
        name=item['key']+'.png';images[name]=png;node.set('url',name)
    with tempfile.TemporaryDirectory() as folder:
        folder=Path(folder)
        for name,data in images.items():(folder/name).write_bytes(data)
        file=folder/'scene.x3d';ET.ElementTree(root).write(file)
        flags=assimp_py.Process_Triangulate|assimp_py.Process_PreTransformVertices|assimp_py.Process_GenNormals|assimp_py.Process_GenUVCoords|assimp_py.Process_SortByPType|assimp_py.Process_FlipUVs
        scene=assimp_py.import_file(str(file),flags)
    if not scene.meshes:raise RuntimeError('No visual mesh')
    # Archive models use both vertical conventions. Explicit per-source rotation, never relabel the model.
    rotation=np.array([[1,0,0],[0,0,1],[0,-1,0]],dtype=np.float32) if entry['sourceUp']=='z' else np.eye(3,dtype=np.float32)
    vertices=[np.asarray(m.vertices,dtype=np.float32).reshape(-1,3)@rotation.T for m in scene.meshes]
    all_vertices=np.concatenate(vertices);low=all_vertices.min(axis=0);high=all_vertices.max(axis=0);offset=np.array([(low[0]+high[0])/2,low[1],(low[2]+high[2])/2],dtype=np.float32)
    binary=bytearray();views=[];accessors=[];materials=[];textures=[];gimages=[];image_index={};primitives=[]
    def view(data,target=None):
        binary.extend(b'\0'*((-len(binary))%4));v=dict(buffer=0,byteOffset=len(binary),byteLength=len(data));binary.extend(data)
        if target:v['target']=target
        views.append(v);return len(views)-1
    def accessor(array,kind,component,target,bounds=False):
        idx=view(array.tobytes(),target);a=dict(bufferView=idx,componentType=component,count=len(array),type=kind)
        if bounds:a.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
        accessors.append(a);return len(accessors)-1
    def image(name):
        if name not in image_index:
            if name not in images:raise RuntimeError('Unresolved material image '+name)
            gimages.append(dict(bufferView=view(images[name]),mimeType='image/png'));textures.append(dict(source=len(gimages)-1));image_index[name]=len(textures)-1
        return image_index[name]
    for material in scene.materials:
        color=list(material.get('COLOR_DIFFUSE',[.6,.6,.6]))[:3];opacity=float(material.get('OPACITY',1))
        out=dict(pbrMetallicRoughness=dict(baseColorFactor=[*color,opacity],metallicFactor=0,roughnessFactor=.65),doubleSided=True)
        texture=material.get('TEXTURES',{}).get(assimp_py.TextureType_DIFFUSE,[])
        if texture and texture[0] in images:out['pbrMetallicRoughness']['baseColorTexture']=dict(index=image(texture[0]))
        if opacity<1:out['alphaMode']='BLEND'
        materials.append(out)
    triangles=0
    for index,mesh in enumerate(scene.meshes):
        indices=np.asarray(mesh.indices,dtype='<u4').reshape(-1)
        if len(indices)%3:raise RuntimeError('Unexpected non-triangle mesh')
        pos=np.asarray(vertices[index]-offset,dtype='<f4');normals=np.asarray(mesh.normals,dtype=np.float32).reshape(-1,3)@rotation.T
        lengths=np.linalg.norm(normals,axis=1);bad=lengths<1e-8
        if bad.any():
            faces=indices.reshape(-1,3);face_normals=np.cross(pos[faces[:,1]]-pos[faces[:,0]],pos[faces[:,2]]-pos[faces[:,0]])
            rebuilt=np.zeros_like(normals)
            for corner in range(3):np.add.at(rebuilt,faces[:,corner],face_normals)
            normals[bad]=rebuilt[bad];lengths=np.linalg.norm(normals,axis=1)
            normals[lengths<1e-8]=[0,1,0];lengths=np.linalg.norm(normals,axis=1)
        normals=normals/lengths[:,None]
        if not np.isfinite(normals).all():raise RuntimeError('Non-finite source normal')
        attrs=dict(POSITION=accessor(pos,'VEC3',5126,34962,True),NORMAL=accessor(np.asarray(normals,dtype='<f4'),'VEC3',5126,34962))
        if mesh.texcoords:
            uv=np.asarray(mesh.texcoords[0],dtype=np.float32).reshape(mesh.num_vertices,-1)[:,:2];attrs['TEXCOORD_0']=accessor(np.asarray(uv,dtype='<f4'),'VEC2',5126,34962)
        elif 'baseColorTexture' in materials[mesh.material_index]['pbrMetallicRoughness']:raise RuntimeError('Textured mesh missing UVs')
        primitives.append(dict(attributes=attrs,indices=accessor(indices,'SCALAR',5125,34963),material=mesh.material_index,mode=4));triangles+=len(indices)//3
    doc=dict(asset=dict(version='2.0',generator='ANOMALIA pinned Savage static reference conversion'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0,name=entry['id'])],meshes=[dict(name=entry['id'],primitives=primitives)],materials=materials,buffers=[dict(byteLength=len(binary))],bufferViews=views,accessors=accessors)
    if textures:doc.update(textures=textures,images=gimages)
    metadata=json.dumps(doc,separators=(',',':')).encode();metadata+=b' '*((-len(metadata))%4);binary.extend(b'\0'*((-len(binary))%4))
    data=struct.pack('<III',0x46546c67,2,12+8+len(metadata)+8+len(binary))+struct.pack('<II',len(metadata),0x4e4f534a)+metadata+struct.pack('<II',len(binary),0x004e4942)+binary
    return data,(high-low).tolist(),triangles,missing


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'unreal/SourceAssets/Military1');parser.add_argument('--cache',type=Path,default=ROOT/'unreal/Saved/MilitarySourceCache');args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    registry=json.loads((ROOT/'docs/vehicles/military-assets-sources.json').read_text());models=[];credits=['# Savage visual reference models','Historic source art; not finished manufacturer replicas or operational weapon simulations.','']
    for entry in registry['models']:
        data,dims,triangles,missing=prepare(entry,args.cache);preserve(args.output/(entry['id']+'.glb'),data)
        authors=[m['content'] for m in entry['metadata'] if m['name']=='creator'];models.append(dict(id=entry['id'],kind='reference_vehicle',file=entry['id']+'.glb',sha256=sha(data),bytes=len(data),triangles=triangles,dimensionsMetresYUp=dims,objectPath='/Game/Anomalia/Military1/'+entry['id']+'/SM_'+entry['id'],source=entry,missingTextures=missing,state='HISTORIC_STATIC_VISUAL_REFERENCE_NOT_DRIVABLE',scaleVerified=False,orientationValidated=False,drivingTested=False))
        credits.extend(['## '+entry['id'],'Creators: '+'; '.join(authors),'Original: '+entry['url'],'License: '+registry['licenseUrl'],'Changes: resolved shared geometry, baked static transforms, rotated source up axis, centred at bottom, triangulated, reconstructed invalid normals and generated analytic UV coordinates where needed, flipped UV vertical axis, and converted embedded PNG textures to 1024px maximum. Source animation/audio excluded; materials approximated as PBR.','Missing source textures: '+str(missing),'']);print(entry['id'],len(data),dims,flush=True)
    preserve(args.output/'manifest.json',(json.dumps(dict(schemaVersion=1,models=models,notes=registry['coverage']),indent=2)+'\n').encode())
    license_text=(ROOT/'scripts/military-assets/LICENSE-SAVAGE.txt').read_text();preserve(args.output/'CREDITS.md',('\n'.join(credits)+'\n\n'+license_text).encode())
if __name__=='__main__':main()
