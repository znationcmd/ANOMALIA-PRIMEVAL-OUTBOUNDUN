"""Prepare the user-owned issue-68 GLBs for deterministic single-mesh Unreal import; preserve geometry."""
import pathlib,zipfile,json,struct,copy,hashlib,sys
PACK_SHA="d5ff88601c149ceddbda1495da7c139468de297611ccde256a0f5659e428350b"
COLORS=("Blue","Red","Green","Orange","Yellow","White")
def chunks(blob):
 magic,version,length=struct.unpack_from("<III",blob)
 if magic!=0x46546c67 or version!=2 or length!=len(blob):raise ValueError("Invalid glTF binary source")
 values=[];offset=12
 while offset<len(blob):
  size,kind=struct.unpack_from("<II",blob,offset);values.append((kind,blob[offset+8:offset+8+size]));offset+=8+size
 if offset!=len(blob):raise ValueError("Invalid GLB chunk lengths")
 return values
def color_value(g,binary,index):
 a=g["accessors"][index];v=g["bufferViews"][a["bufferView"]]
 component={5121:("B",255),5123:("H",65535),5126:("f",1)}.get(a["componentType"])
 if not component or a["type"] not in {"VEC3","VEC4"}:raise ValueError("Unsupported source vertex color type")
 count=3 if a["type"]=="VEC3" else 4;fmt="<"+component[0]*count;size=struct.calcsize(fmt)
 stride=v.get("byteStride",size);start=v.get("byteOffset",0)+a.get("byteOffset",0)
 colors=[struct.unpack_from(fmt,binary,start+i*stride) for i in range(a["count"])]
 if any(c!=colors[0] for c in colors):raise ValueError("Non-uniform vertex colors need an explicit shader conversion")
 value=[n/component[1] for n in colors[0]]
 if len(value)==3:value.append(1.)
 if any(n<0 or n>1 for n in value):raise ValueError("Out-of-range source vertex colors")
 return value
def prepare(blob,name,source_pack_sha=PACK_SHA):
 original=chunks(blob);g=json.loads(next(v for k,v in original if k==0x4e4f534a))
 binary=next(v for k,v in original if k==0x004e4942)
 if any(any(k in n for k in ("matrix","translation","rotation","scale","skin")) for n in g["nodes"]):raise ValueError("Transforms or skinning require reviewed geometry baking")
 if g.get("animations"):raise ValueError("Do not collapse animated source models")
 primitive_count=sum(len(m["primitives"]) for m in g["meshes"])
 primitives=[];materials=copy.deepcopy(g.get("materials",[]));colors={}
 for index,material in enumerate(materials):material["name"]=name+"_Material_"+str(index)
 for mesh in g["meshes"]:
  for source in mesh["primitives"]:
   p=copy.deepcopy(source)
   if p.get("mode",4)!=4:raise ValueError("Non-triangle geometry needs separate review")
   if "COLOR_0" in p.get("attributes",{}):
    rgba=color_value(g,binary,p["attributes"]["COLOR_0"]);key=tuple(rgba)
    if key not in colors:
     colors[key]=len(materials)
     paint=max(rgba[:3])-min(rgba[:3])>.15
     materials.append({"name":name+("_Paint_" if paint else "_Metal_")+str(len(materials)),"pbrMetallicRoughness":{"baseColorFactor":rgba,"roughnessFactor":.4,"metallicFactor":.12 if paint else .55}})
    p["material"]=colors[key];del p["attributes"]["COLOR_0"]
   primitives.append(p)
 g["materials"]=materials;g["meshes"]=[{"name":name,"primitives":primitives}]
 g["nodes"]=[{"name":name,"mesh":0}];g["scenes"]=[{"nodes":[0]}];g["scene"]=0
 g.setdefault("extras",{})["AnomaliaSourcePackSHA256"]=source_pack_sha
 payload=json.dumps(g,separators=(",",":"),ensure_ascii=False).encode("utf-8");payload+=b" "*((-len(payload))%4)
 parts=[(0x4e4f534a,payload)]+[(k,v) for k,v in original if k!=0x4e4f534a]
 output=b"".join(struct.pack("<II",len(v),k)+v for k,v in parts)
 result=struct.pack("<III",0x46546c67,2,12+len(output))+output
 return result,{"sourceMeshes":len(json.loads(next(v for k,v in original if k==0x4e4f534a))["meshes"]),"preparedMeshes":1,"primitives":primitive_count,"materials":len(materials),"geometryBinaryUnchanged":next(v for k,v in chunks(result) if k==0x004e4942)==binary}
def main():
 source=pathlib.Path(sys.argv[1]);target=pathlib.Path(sys.argv[2]);target.mkdir(parents=True,exist_ok=True)
 if hashlib.sha256(source.read_bytes()).hexdigest()!=PACK_SHA:raise ValueError("The verified issue-68 original ZIP differs")
 report={"originalSHA256":PACK_SHA,"originalModified":False,"models":[]}
 with zipfile.ZipFile(source) as z:
  for kind,stem in [("Keys","ContainerKey"),("Locks","ContainerLock")]:
   folder=target/kind;folder.mkdir(exist_ok=True)
   for color in COLORS:
    name=stem+"_"+color;path=folder/(name+".glb");data,checks=prepare(z.read("Models/"+kind+"/"+name+".glb"),name)
    if path.exists() and path.read_bytes()!=data:raise ValueError("Existing prepared model differs; preserve it")
    if not path.exists():path.write_bytes(data)
    report["models"].append({"color":color,"kind":kind,"source":"Models/"+kind+"/"+name+".glb","prepared":str(path),"sha256":hashlib.sha256(data).hexdigest(),"assetPath":"/Game/ANOMALIAZ/Items/ContainerLocks/"+kind+"/"+name,"itemId":"container_key_"+color.lower(),**checks})
 (target/"manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps({"models":len(report["models"]),"allGeometryPreserved":all(r["geometryBinaryUnchanged"] for r in report["models"]),"originalModified":False}),flush=True)
if __name__=="__main__":main()
