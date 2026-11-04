"""Independently reopen 160 reversibly hidden exact duplicate SK-RX-003 actors."""
import os,json,hashlib,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_DUPLICATE_SUPPRESSION_REOPEN_REPORT"])
BUILD=Path(os.environ["SKARVIK_DUPLICATE_SUPPRESSION_BUILD_RESULT"])
RESTORE=ROOT/"Saved/SkarvikCity/FinalRegionalNearDuplicateSuppression_20261101/restore-hidden-SK-RX-003-B-actors.json"
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
A="SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
B="SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
TAG="SKARVIK_REGIONAL_DUPLICATE_SAFE_SUPPRESSED"
report={"state":"FAILED","readOnly":True,"realDrivingTestPassed":False}
try:
 mark=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
  or not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Untrusted native stage")
 if any(not p.is_file() for p in FILES) or not BUILD.is_file() or not RESTORE.is_file():
  raise RuntimeError("Protected native map, restore plan or proof missing")
 data=json.loads(BUILD.read_text(encoding="utf-8-sig"))
 restoration=json.loads(RESTORE.read_text(encoding="utf-8-sig"))
 if (data.get("state")!="FINAL_SKARVIK_160_EXACT_SK_RX_003_DUPLICATE_ASPHALT_ACTORS_REVERSIBLY_HIDDEN"
     or len(restoration.get("previousActors",[]))!=160):
  raise RuntimeError("Exact duplicate visibility repair receipt mismatch")
 hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("True seven island world did not reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(prefix):return sum(l.startswith(prefix) for l in labels)
 for prefix,n in (
  (A,663),(B,992),
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298),
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
  ("SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_E5_",121)):
  if count(prefix)!=n:raise RuntimeError("Protected native actor count lost: "+prefix)
 targets={x["label"] for x in restoration["previousActors"]}
 select=[d for d in desc if str(d.label) in targets]
 if len(select)!=160:raise RuntimeError("Reversible regional duplicate labels missing")
 # Load all 160 exact actor instances and check actual component flags.
 for off in range(0,len(select),40):
  wp.load_actors([d.guid for d in select[off:off+40]])
 objects={a.get_actor_label():a for a in
  unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 checks=[]
 for d in select:
  actor=objects.get(str(d.label))
  if not isinstance(actor,unreal.StaticMeshActor):
   raise RuntimeError("Previously suppressed actual actor no longer resolves")
  if TAG not in [str(x) for x in actor.tags]:
   raise RuntimeError("Native reversible suppression tag not saved")
  c=actor.get_component_by_class(unreal.StaticMeshComponent)
  mesh=c.get_editor_property("static_mesh") if c else None
  if not isinstance(mesh,unreal.StaticMesh):
   raise RuntimeError("Hidden actor lost its genuine original road mesh")
  try:
   is_visible=bool(c.get_editor_property("visible"))
  except Exception:
   is_visible=bool(c.is_visible())
  if is_visible:raise RuntimeError("Potential duplicate road mesh remains rendered")
  try:
   collision=str(c.get_collision_profile_name())
  except Exception as ex:
   raise RuntimeError("Unable to prove collision disabled on reloaded actor: "+str(ex))
  if collision!="NoCollision":raise RuntimeError("Duplicate road collision remains active: "+collision)
  if len(checks)<12:checks.append({"label":str(d.label),"meshKept":mesh.get_path_name(),
                                   "visible":is_visible,"collision":collision})
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[str(p)]:
   raise RuntimeError("Read-only check unexpectedly modified protected original")
 report.update(
  state="FINAL_SKARVIK_160_DUPLICATE_REGIONAL_B_ACTORS_HIDDEN_NO_COLLISION_AND_RESTORABLE_AFTER_REOPEN",
  actorsPreserved=992,stillActiveSecondRegionalActors=832,firstRegionalActorsPreserved=663,
  exactDuplicateBActorsHiddenAndCollisionOff=160,
  sourceUnchanged=True,restorationRecords=160,representativeRealNativeActorChecks=checks,
  allRoadsDriveable=False)
 unreal.log("SKARVIK_FINAL_160_DUPLICATE_ROAD_MESHES_COLLISION_DISABLED_VERIFIED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_ROAD_SUPPRESSION_REOPEN_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
