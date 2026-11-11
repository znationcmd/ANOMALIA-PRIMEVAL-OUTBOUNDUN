"""Read-only native bounding-box audit for original ANOMALIA houses staged in SKARVIK."""
import json,os,traceback
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
out=Path(os.environ.get("SKARVIK_OWNED_MESH_DIMENSIONS_REPORT",str(root/"Saved/SkarvikCity/owned-houses-dimensions.json")))
items={
"coastal_house":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
"garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
"apartment_8":"/Game/Anomalia/Buildings/Lot1/SM_hlm_8floors_v1",
"villa_pool":"/Game/Anomalia/Buildings/Lot1/SM_beach_villa_pool_v1",
"residence_4":"/Game/Anomalia/Buildings/Expansion1/SM_residence_4floors",
"townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
"hospital":"/Game/Anomalia/Buildings/Expansion1/SM_hospital",
"police":"/Game/Anomalia/Buildings/Expansion1/SM_police_station",
"barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn",
"fire_station":"/Game/Anomalia/Buildings/Expansion1/SM_fire_station",
"enterable_wood_house":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
}
result={"state":"FAILED","objects":{},"nativeConstructionAttempted":False,"originalDModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(root).upper():
  raise RuntimeError("Invalid project root")
 if (root/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Invalid stage marker")
 for name,path in items.items():
  mesh=unreal.EditorAssetLibrary.load_asset(path)
  if not isinstance(mesh,unreal.StaticMesh):
   result["objects"][name]={"path":path,"available":False}
   continue
  b=mesh.get_bounds()
  v=(b.box_extent.x,b.box_extent.y,b.box_extent.z)
  result["objects"][name]={"path":path,"available":True,
   "dimensionsMeters":[round(x*2/100,3) for x in v],
   "boundsOriginCm":[round(b.origin.x,2),round(b.origin.y,2),round(b.origin.z,2)]}
  unreal.log("SKARVIK_OWNED_MESH_AVAILABLE={} dimensionsMeters={}".format(name,result["objects"][name]["dimensionsMeters"]))
 result["availableCount"]=sum(1 for x in result["objects"].values() if x["available"])
 if result["availableCount"]<4:
  raise RuntimeError("Not enough real ANOMALIA house meshes to begin authentic village construction")
 if not result["objects"]["enterable_wood_house"]["available"]:
  raise RuntimeError("Enterable wooden house mesh missing")
 result["state"]="REAL_ANOMALIA_HOUSE_MESH_DIMENSIONS_VERIFIED_NO_WORLD_MODIFICATION"
 unreal.log("SKARVIK_REAL_HOUSE_SCALE_AUDIT_SUCCESS=true")
except Exception as e:
 result["error"]=str(e);result["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_REAL_HOUSE_SCALE_AUDIT_ERROR="+str(e))
finally:
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
