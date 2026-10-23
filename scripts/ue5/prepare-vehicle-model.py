"""Verify and bake an original single-node static GLB without replacing its source."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import numpy as np

ROOT=Path(__file__).resolve().parents[2]

def load_glb(path):
    blob=path.read_bytes()
    if len(blob)<28 or struct.unpack_from('<III',blob)!=(0x46546c67,2,len(blob)):
        raise ValueError('Invalid GLB container')
    chunks=[]; offset=12
    while offset<len(blob):
        length,kind=struct.unpack_from('<II',blob,offset);offset+=8
        if length%4 or offset+length>len(blob): raise ValueError('Invalid GLB chunk')
        chunks.append((kind,blob[offset:offset+length]));offset+=length
    if len(chunks)!=2 or chunks[0][0]!=0x4e4f534a or chunks[1][0]!=0x004e4942:
        raise ValueError('Expected one JSON and one embedded BIN chunk')
    return json.loads(chunks[0][1]),bytearray(chunks[1][1])

def transform(document):
    if len(document.get('meshes',[]))!=1 or len(document.get('nodes',[]))!=1 or document.get('animations') or document.get('skins'):
        raise ValueError('Requires a single-node static mesh; no silent hierarchy/animation loss')
    node=document['nodes'][0]
    if node.get('mesh')!=0 or node.get('children'): raise ValueError('Unexpected node layout')
    if document.get('extensionsRequired'): raise ValueError('Unsupported required extensions')
    if 'matrix' in node: matrix=np.array(node['matrix'],dtype=float).reshape(4,4).T
    else:
        x,y,z,w=node.get('rotation',[0,0,0,1]);r=np.array([
          [1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
          [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
          [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        matrix=np.eye(4);matrix[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));matrix[:3,3]=node.get('translation',[0,0,0])
    if not np.isfinite(matrix).all() or np.linalg.det(matrix[:3,:3])<=0:
        raise ValueError('Invalid or mirrored transform')
    return matrix

def prepare(source,destination,expected_hash):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=expected_hash: raise ValueError('Source checksum mismatch')
    d,b=load_glb(source);m=transform(d);normal=np.linalg.inv(m[:3,:3]).T
    if any(v.get('uri') for v in d.get('buffers',[])) or any(i.get('uri') for i in d.get('images',[])):
        raise ValueError('External resources are not permitted')
    done=set()
    for p in d['meshes'][0]['primitives']:
        if p.get('mode',4)!=4 or p.get('targets') or p.get('extensions'): raise ValueError('Unsupported geometry')
        for semantic in ('POSITION','NORMAL','TANGENT'):
            index=p['attributes'].get(semantic)
            if index is None or (semantic,index) in done: continue
            done.add((semantic,index));a=d['accessors'][index]
            if a.get('componentType')!=5126 or a.get('sparse') or a.get('type') not in ('VEC3','VEC4'):
                raise ValueError('Unsupported accessor')
            v=d['bufferViews'][a['bufferView']];components=4 if a['type']=='VEC4' else 3
            stride=v.get('byteStride',components*4);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
            end=offset+(a['count']-1)*stride+components*4
            if v.get('buffer',0)!=0 or end>v.get('byteOffset',0)+v['byteLength'] or end>len(b): raise ValueError('Accessor out of bounds')
            array=np.ndarray((a['count'],components),dtype='<f4',buffer=b,offset=offset,strides=(stride,4))
            values=array[:,:3].astype(float)
            values=values@m[:3,:3].T+m[:3,3] if semantic=='POSITION' else values@(normal.T if semantic=='NORMAL' else m[:3,:3].T)
            if semantic!='POSITION':
                length=np.linalg.norm(values,axis=1)
                if np.any(length<1e-12): raise ValueError('Zero length normal')
                values/=length[:,None]
            if not np.isfinite(values).all(): raise ValueError('Non-finite mesh')
            array[:,:3]=values
            if semantic=='POSITION': a['min']=values.min(axis=0).tolist();a['max']=values.max(axis=0).tolist()
    d['nodes']=[dict(mesh=0,name='ANOMALIA_airliner_baked')]
    d['scenes']=[dict(nodes=[0])];d['scene']=0
    d['asset']['generator']='ANOMALIA static vehicle preparation (original node transform baked)'
    j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
    b+=b'\0'*((-len(b))%4)
    result=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
    if destination.resolve()==source.resolve(): raise ValueError('Source must be preserved')
    if destination.exists() and destination.read_bytes()!=result: raise FileExistsError('Refusing to replace an existing different prepared model')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(result)
    return hashlib.sha256(result).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,default=ROOT/'unreal/SourceAssets/Vehicles/manifest.json');args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text())
    base=args.manifest.resolve().parent
    for item in manifest['models']:
        source=(base/item['sourceFile']).resolve();dest=(base/item['preparedFile']).resolve()
        if not source.is_relative_to(base) or not dest.is_relative_to(base): raise ValueError('Path escapes source asset directory')
        print(item['vehicleId'],prepare(source,dest,item['sha256']))
