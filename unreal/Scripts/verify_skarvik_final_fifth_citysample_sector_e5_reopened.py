"""Independently verify the fifth original CitySample sector after final SKARVIK reload.

Read-only actor descriptors and selected real Unreal mesh assets. Does not
assert full 86k-actor Big City streaming or a rendered SM5 playtest.
"""
import hashlib,json,math,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PLAN=Path(os.environ["SKARVIK_FINAL_FIFTH_CITY_BUILD_REPORT"])
OUT=Path(os.environ["SKARVIK_FINAL_FIFTH_CITY_REOPEN_REPORT"])
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
PREFIX="SKARVIK_FINAL_CITYSAMPLE_E5_ORIGINAL_MESH_"
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
data={"state":"FAILED","readOnly":True,"fullCitySampleRenderedSM5":False,
      "vehicleDrivabilityTested":False,"allTownInteriorsExplorable":False,
      "multiplayerValidated":False}
try:
 mark=ROOT/".skarvik-ci-stage-marker"
 if("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
  or not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Wrong stage")
 if any(not f.is_file() for f in FILES):raise RuntimeError("Protected source final map absent")
 r=json.loads(PLAN.read_text(encoding="utf-8-sig"))
 if r.get("state")!="SKARVIK_FINAL_FIFTH_SOURCE_CITYSAMPLE_SECTOR_REAL_MESHES_SAVED_PARTIAL_CITY":
  raise RuntimeError("Fifth source city pilot was not natively saved")
 wanted=int(r["native3DCityMeshesAdded"])
 if not 15<=wanted<=121:raise RuntimeError("Unexpected count of genuine fifth sector meshes")
 before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level(PKG):raise RuntimeError("Final world not independently loadable")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 checks={
  "originalCitySampleMeshes":sum(z.startswith("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_") for z in labels),
  "newFifthSourceCityMeshes":sum(z.startswith(PREFIX) for z in labels),
  "mainlandBuildings":sum(z.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for z in labels),
  "islandBuildings":sum(z.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for z in labels),
  "oldDryRoadMeshes":sum(z.startswith("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") for z in labels),
  "localTownRoadB1":sum(z.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_") for z in labels),
  "localTownRoadB2":sum(z.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_") for z in labels),
  "nativeRegionalA":sum(z.startswith("SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_") for z in labels),
  "nativeRegionalB":sum(z.startswith("SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_") for z in labels)}
 data["native3DActorCounts"]=checks
 if(checks!={"originalCitySampleMeshes":720,"newFifthSourceCityMeshes":wanted,
 "mainlandBuildings":906,"islandBuildings":128,"oldDryRoadMeshes":6130,
 "localTownRoadB1":1674,"localTownRoadB2":1298,"nativeRegionalA":663,"nativeRegionalB":992}):
  raise RuntimeError("Fifth city sector or protected original actor count did not persist")
 actors=[d for d in desc if str(d.label).startswith(PREFIX)]
 if len({str(d.label) for d in actors})!=len(actors):
  raise RuntimeError("Duplicated fifth city native actor names")
 samples=sorted(actors,key=lambda d:str(d.label))
 indices=sorted({int(i*(len(samples)-1)/11) for i in range(12)})
 selected=[samples[i] for i in indices]
 wp.load_actors([d.guid for d in selected])
 loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 h=unreal.AnomaliaZPrigimaliaWorldImportLibrary.skarvik_final_coastal_height
 real=[]
 for d in selected:
  obj=loaded.get(str(d.label))
  if not isinstance(obj,unreal.StaticMeshActor):
   raise RuntimeError("Original fifth CitySample native asset actor did not reopen")
  c=obj.get_component_by_class(unreal.StaticMeshComponent)
  mesh=c.get_editor_property("static_mesh") if c else None
  if not isinstance(mesh,unreal.StaticMesh):
   raise RuntimeError("Original fifth source asset mesh missing")
  p=obj.get_actor_location()
  e,n=float(p.x)/100.,-float(p.y)/100.
  if abs(e-2000)>2000 or abs(n+8000)>2000 or float(h(e,n))<5.:
   raise RuntimeError("Fifth city source mesh not located on 4x4 km dry source city plateau")
  real.append({"label":str(d.label),"realMesh":mesh.get_path_name(),
    "nativeCityCenterMetres":[round(e),round(n)]})
 wp.unload_actors([d.guid for d in selected])
 for f in FILES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=before[str(f)]:
   raise RuntimeError("Read-only verification changed native map")
 data.update(state="SKARVIK_FINAL_FIFTH_ORIGINAL_CITYSAMPLE_NATIVE_MESHES_PERSISTED_NOT_PLAYTESTED",
  originalSourceWorldsUnchanged=True,
  sampledRealOriginalCityStaticMeshActors=real,
  allApprovedFifthSectorActorsReopened=True,
  cityTotal=720+wanted)
 unreal.log("SKARVIK_FINAL_REAL_FIFTH_SOURCE_CITY_MESHES_REOPENED="+str(wanted))
except Exception as ex:
 data["error"]=str(ex);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_FIFTH_CITY_REOPEN_FAILED="+str(ex))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
