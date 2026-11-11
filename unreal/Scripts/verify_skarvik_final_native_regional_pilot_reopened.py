"""Read-only native re-open after safe regional-road pilot, including no-build gate."""
import os,json,hashlib,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_FINAL_REGIONAL_REOPEN_REPORT"])
PREV=Path(os.environ["SKARVIK_FINAL_REGIONAL_NATIVE_BUILD_REPORT"])
PREFIX="SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
FILES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
       ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
       ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
       ROOT/"Content/Map/Big_City_LVL.umap",
       Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
data={"state":"FAILED","readOnly":True,"fullRoadNetworkFinished":False,
      "SM5DrivingTestPassed":False}
try:
 m=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
     or not m.is_file() or m.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Untrusted coastal stage")
 if not PREV.is_file() or any(not p.is_file() for p in FILES):
  raise RuntimeError("Native plan receipt or protected world file missing")
 source=json.loads(PREV.read_text(encoding="utf-8-sig"))
 expected=int(source.get("actualNativeRoadMeshActorsAdded",0))
 if source.get("state") not in (
  "FINAL_SEVEN_ISLAND_BOUNDED_DRY_REGIONAL_REAL_ASPHALT_SAVED_NOT_DRIVEN",
  "NO_NEW_REGIONAL_CORRIDOR_PASSED_ALL_NATIVE_BUILDING_AND_EXISTING_ROAD_GATES"):
  raise RuntimeError("Regional previous build did not complete checks")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("Could not independently reopen true seven-island coastal world")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(prefix):return sum(x.startswith(prefix) for x in labels)
 for prefix,number in (
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298)):
  if count(prefix)!=number:raise RuntimeError("Previously proven original actors missing: "+prefix)
 built=[d for d in desc if str(d.label).startswith(PREFIX)]
 if len(built)!=expected:raise RuntimeError("Real native regional asphalt actor count changed")
 samples=[]
 if built:
  chosen=[built[i] for i in sorted({int(k*(len(built)-1)/11) for k in range(12)})]
  wp.load_actors([d.guid for d in chosen])
  actors={a.get_actor_label():a for a in
   unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
  for d in chosen:
   actor=actors.get(str(d.label))
   if not isinstance(actor,unreal.StaticMeshActor):raise RuntimeError("Actual road actor missing")
   comp=actor.get_component_by_class(unreal.StaticMeshComponent)
   mesh=comp.get_editor_property("static_mesh") if comp else None
   if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Selected regional native asphalt missing mesh")
   samples.append({"actor":str(d.label),"mesh":mesh.get_path_name()})
  wp.unload_actors([d.guid for d in chosen])
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
   raise RuntimeError("Read-only regional-road verification altered protected original")
 data.update(
  state="FINAL_SKARVIK_REAL_REGIONAL_ROADS_PERSIST_OR_SAFE_NOOP_NOT_PLAYTESTED",
  realNativeRegionalActorsAfterReopen=len(built),
  realNewRegionalRouteCount=int(source["verifiedRegionalRoutesAdded"]),
  originalFilesUnchanged=True,verifiedSampleAssets=samples)
 unreal.log("SKARVIK_FINAL_REAL_NATIVE_REGIONAL_REOPEN_ACTORS="+str(len(built)))
except Exception as exc:
 data["error"]=str(exc);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_REGIONAL_NATIVE_REOPEN_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
