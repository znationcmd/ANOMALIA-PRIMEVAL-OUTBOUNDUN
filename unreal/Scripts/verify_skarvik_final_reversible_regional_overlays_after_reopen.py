"""Independent read-only WP reload of reversible overlap suppression.

Do not confuse 160 disabled duplicates with 160 deleted assets: every B actor,
A actor, old asphalt, native house and City Sample mesh must remain in place.
"""
import os,json,hashlib,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
WORLD="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
SRC=Path(os.environ["SKARVIK_FINAL_REPAIR_ORIGINAL_REPORT"])
OUT=Path(os.environ["SKARVIK_FINAL_REPAIR_INDEPENDENT_REOPEN"])
BASE=ROOT/"Saved/SkarvikCity/FinalRegionalExactDuplicateNonDestructiveSuppression20261101"
FLAGS=BASE/"exact-original-B-road-flags-for-restoration.json"
FILES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
TAG="SKARVIK_FINAL_OVERLAID_B_ROAD_DISABLED_REVERSIBLE"
REPORT={"state":"FAILED","readOnly":True,"realDrivingSM5Validated":False,
 "all382RegionalRoadsFinished":False,"allRegionalIntersectionsFixed":False,
 "realCitySampleFullyLoaded":False,"actorsDeleted":0}
try:
 marker=ROOT/".skarvik-ci-stage-marker"
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
    not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Untrusted stage marker")
 if any(not f.is_file() for f in FILES) or not FLAGS.is_file():
  raise RuntimeError("Native protected original map or restoration flag manifest missing")
 before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
 saved=json.loads(SRC.read_text(encoding="utf-8-sig"))
 backup=json.loads(FLAGS.read_text(encoding="utf-8-sig"))
 if saved.get("state")!="FINAL_NATIVE_160_CONFIRMED_OVERLAID_B_ROADS_HIDDEN_COLLISION_DISABLED_REVERSIBLE_NOT_DRIVEN":
  raise RuntimeError("No proven original reversible native edit report")
 if backup.get("state")!="BACKED_UP_PREVIOUS_NATIVE_B_ACTOR_FLAGS" or len(backup.get("actorFlags",[]))!=160:
  raise RuntimeError("Original B road actor restore manifest absent")
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level(WORLD):raise RuntimeError("Cannot independently reopen final SKARVIK")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 names=[str(x.label) for x in desc]
 counts={
  "regionalA":sum(x.startswith("SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_") for x in names),
  "regionalB":sum(x.startswith("SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_") for x in names),
  "oldAsphalt":sum(x.startswith("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") for x in names),
  "townB1":sum(x.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_") for x in names),
  "townB2":sum(x.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_") for x in names),
  "mainlandBuildings":sum(x.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for x in names),
  "islandBuildings":sum(x.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for x in names),
  "CitySampleMeshes":sum(x.startswith("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_") for x in names)}
 REPORT["persistedNativeActors"]=counts
 if counts!={"regionalA":663,"regionalB":992,"oldAsphalt":6130,"townB1":1674,
            "townB2":1298,"mainlandBuildings":906,"islandBuildings":128,"CitySampleMeshes":720}:
  raise RuntimeError("Original native World Partition actor source unexpectedly changed")
 byname={str(d.label):d for d in desc}
 selected=[byname[v["actor"]] for v in backup["actorFlags"] if v["actor"] in byname]
 if len(selected)!=160:raise RuntimeError("Verified original 160 native B actor descriptors missing")
 wp.load_actors([d.guid for d in selected])
 loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 disabled=[]
 for item in backup["actorFlags"]:
  actor=loaded.get(item["actor"])
  if not actor or not isinstance(actor,unreal.StaticMeshActor):
   raise RuntimeError("Original B road actor cannot load after final world reopen")
  c=actor.get_component_by_class(unreal.StaticMeshComponent)
  path=c.get_editor_property("static_mesh") if c else None
  if not isinstance(path,unreal.StaticMesh) or path.get_path_name()!=item["originalMesh"]:
   raise RuntimeError("Original road mesh missing from disabled native actor")
  if TAG not in [str(tag) for tag in actor.tags]:
   raise RuntimeError("Reversible B asphalt suppression marker not persistent")
  if actor.get_actor_enable_collision() or c.get_editor_property("visible") is not False:
   raise RuntimeError("Original overlapping road is still visible or collision active")
  disabled.append(str(actor.get_actor_label()))
 REPORT["actualDisabledDuplicateBActorsReopened"]=len(disabled)
 REPORT["originalBActorsStillSaved"]=counts["regionalB"]
 REPORT["restorableOriginalActorFlagsCount"]=len(backup["actorFlags"])
 REPORT["olderRegionalAActorsPreserved"]=counts["regionalA"]
 wp.unload_actors([d.guid for d in selected])
 for f in FILES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=before[str(f)]:
   raise RuntimeError("Read-only independent verification modified native map file")
 REPORT["state"]="FINAL_NATIVE_160_OVERLAID_B_ROADS_REVERSIBLY_DISABLED_AND_PERSISTED_AFTER_REOPEN"
 REPORT["originalsUnchangedByAudit"]=True
 unreal.log("SKARVIK_FINAL_160_NATIVE_OVERLAID_ROADS_DISABLED_PERSISTED_READONLY=true")
except Exception as ex:
 REPORT["error"]=str(ex);REPORT["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_OVERLAID_ROAD_REOPEN_FAILED="+str(ex))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
