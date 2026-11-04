"""Read-only native UE5 audit of real installed City Sample road surfaces.
Never modifies any level. Keeps protected source D and staged maps untouched.
"""
from pathlib import Path
import json,os,traceback
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ.get("SKARVIK_NATIVE_ROAD_MESH_AUDIT",str(ROOT/"Saved/SkarvikCity/road-mesh-audit.json")))
assets={
 "road_10":"/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road",
 "road_20":"/Game/Road/Kit_City_Road/SM_ROAD_19_20_0_0_road",
 "road_5":"/Game/Road/Kit_City_Road/SM_ROAD_19_5_0_0_road"
}
state={"state":"FAILED","meshes":{},"roadActorsSpawned":0,"stageMapModified":False,"originalDModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Project is not the isolated verified C stage")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Invalid original stage marker")
 if not (ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap").is_file():
  raise RuntimeError("Original 48km terrain not present in C stage")
 if not Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
  raise RuntimeError("D original missing")
 for name,path in assets.items():
  mesh=unreal.EditorAssetLibrary.load_asset(path)
  if not isinstance(mesh,unreal.StaticMesh):
   state["meshes"][name]={"available":False,"path":path}
   continue
  b=mesh.get_bounds()
  dimensions=[round(float(v)*2/100,2) for v in (b.box_extent.x,b.box_extent.y,b.box_extent.z)]
  state["meshes"][name]={"available":True,"path":path,"dimensionsMeters":dimensions,"originCm":[round(v,2) for v in (b.origin.x,b.origin.y,b.origin.z)]}
  unreal.log("SKARVIK_NATIVE_ROAD_AUDIT_MESH={} dimensions={}".format(name,dimensions))
 if not any(x.get("available") for x in state["meshes"].values()):
  raise RuntimeError("No native City Sample 3D road mesh available")
 state["state"]="REAL_ROAD_STATIC_MESHES_AUDITED_NO_MAP_CHANGED"
 unreal.log("SKARVIK_NATIVE_ROAD_MESH_AUDIT_SUCCESS=true")
except Exception as e:
 state["error"]=str(e);state["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_NATIVE_ROAD_MESH_AUDIT_ERROR="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
