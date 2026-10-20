"""Original terrain-following road surface; pure stdlib glTF writer (metres/Y-up)."""
import json,struct,math

def build_road(height,x0,x1,bridge_end,bridge_height,bridge_source):
    # Reuse the exact existing bridge asphalt/concrete images without downloading assets.
    count=struct.unpack_from('<I',bridge_source,12)[0]
    source=json.loads(bridge_source[20:20+count]);binary=bridge_source[28+count:]
    blob=bytearray();views=[];accessors=[]
    def put(data):
        blob.extend(b'\0'*((-len(blob))%4));offset=len(blob);blob.extend(data)
        views.append(dict(buffer=0,byteOffset=offset,byteLength=len(data)));return len(views)-1
    def array(values,kind,components):
        flat=[v for row in values for v in row] if components>1 else values
        view=put(struct.pack('<'+('I' if kind==5125 else 'f')*len(flat),*flat))
        spec=dict(bufferView=view,componentType=kind,count=len(values),type={1:'SCALAR',2:'VEC2',3:'VEC3'}[components])
        if components==3:spec.update(min=[min(v[i] for v in values) for i in range(3)],max=[max(v[i] for v in values) for i in range(3)])
        accessors.append(spec);return len(accessors)-1
    centre=(x0+x1)/2
    def road_height(x,z):
        # Blend into the unchanged bridge endpoint over 20 metres.
        blend=max(0.,1.-abs(x-bridge_end)/20.)
        terrain=height(x,-9000+z)+.30
        return terrain*(1-blend)+bridge_height*blend
    origin=road_height(centre,0)
    primitives=[]
    for left,right,material in [(-4,4,0),(-5.5,-4,1),(4,5.5,1)]:
        positions=[];uv=[];indices=[];normals=[]
        # 5m longitudinal subdivision follows the real Landscape elevation.
        steps=round((x1-x0)/5)
        for i in range(steps+1):
            x=x0+(x1-x0)*i/steps
            for z in (left,right):
                positions.append([x-centre,road_height(x,z)-origin,z]);uv.append([x/4,z/4])
                dx=(road_height(x+.1,z)-road_height(x-.1,z))/.2
                dz=(road_height(x,z+.1)-road_height(x,z-.1))/.2
                length=math.sqrt(dx*dx+1+dz*dz);normals.append([-dx/length,1/length,-dz/length])
        for i in range(steps):
            a=2*i;indices.extend([a,a+1,a+2,a+1,a+3,a+2])
        primitives.append(dict(attributes=dict(POSITION=array(positions,5126,3),NORMAL=array(normals,5126,3),TEXCOORD_0=array(uv,5126,2)),indices=array(indices,5125,1),material=material))
    images=[]
    for old in source['images'][:2]:
        v=source['bufferViews'][old['bufferView']];start=v.get('byteOffset',0)
        images.append(dict(bufferView=put(binary[start:start+v['byteLength']]),mimeType=old['mimeType']))
    doc=dict(asset=dict(version='2.0',generator='CMD original terrain road v1'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0)],meshes=[dict(primitives=primitives)],buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=accessors,images=images,textures=[dict(source=i,sampler=0) for i in range(2)],samplers=[dict(wrapS=10497,wrapT=10497)],materials=[dict(name=n,doubleSided=True,pbrMetallicRoughness=dict(baseColorTexture=dict(index=i),metallicFactor=0,roughnessFactor=.9)) for i,n in enumerate(['Asphalt','ConcreteShoulder'])])
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);blob.extend(b'\0'*((-len(blob))%4))
    glb=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(blob))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(blob),0x004e4942)+blob
    return glb,(centre,origin)
