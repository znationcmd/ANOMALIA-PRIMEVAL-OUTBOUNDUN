"""Prepare all seven user-owned camping/bulb models; keep the original archive unchanged."""
import pathlib,sys,zipfile,io,json,hashlib,importlib.util
PACK_SHA="8f4662275751fe418489e362341a4a88ca2d2b86118175f0267c024b15d92b6c"
def main():
 source=pathlib.Path(sys.argv[1]);target=pathlib.Path(sys.argv[2]);target.mkdir(parents=True,exist_ok=True)
 assert hashlib.sha256(source.read_bytes()).hexdigest()==PACK_SHA,"Camping archive differs"
 spec=importlib.util.spec_from_file_location("prepare68",pathlib.Path(__file__).with_name("prepare-container-security-68.py"));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 report={"originalSHA256":PACK_SHA,"originalModified":False,"models":[]}
 with zipfile.ZipFile(source) as outer:
  names=[n for n in outer.namelist() if n.endswith("ANOMALIAZ_Camping_6_Objets_Ampoule_Universelle_3D.zip")]
  assert len(names)==1,"Unique nested original pack required"
  with zipfile.ZipFile(io.BytesIO(outer.read(names[0]))) as archive:
   manifest=json.loads(archive.read("Items_Manifest.json"));assert len(manifest["items"])==7
   for item in manifest["items"]:
    name=pathlib.Path(item["mesh"]).stem;prepared,checks=module.prepare(archive.read("Models/"+item["mesh"]),name,PACK_SHA)
    path=target/(name+".glb")
    if path.exists():assert path.read_bytes()==prepared,"Existing derived model preserved"
    else:path.write_bytes(prepared)
    report["models"].append({"color":"","kind":"Camping","itemId":item["id"],"prepared":str(path),"sha256":hashlib.sha256(prepared).hexdigest(),"assetPath":"/Game/ANOMALIAZ/Items/CampingAndVehicleBulbs/"+name,**checks})
 (target/"manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps({"models":len(report["models"]),"originalModified":False,"allGeometryPreserved":all(x["geometryBinaryUnchanged"] for x in report["models"])}),flush=True)
if __name__=="__main__":main()
