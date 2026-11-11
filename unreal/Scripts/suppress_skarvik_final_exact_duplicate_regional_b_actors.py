"""Reversibly suppress ONLY 160 independently proven duplicate regional road actors.

A and B both saved genuine SK-RX-003 road meshes ~0.498m apart. Keep original
663 A actors active, preserve 992 B descriptors, and disable only 160 exact B
duplicates from independent native read-only report. No deletion of assets.
Restore by setting visibility True, collision BlockAll, hiddenInGame False on
labels saved in the restoration manifest.
"""
import hashlib,json,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
TARGET="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
MAP=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
AUDIT=Path(os.environ["SKARVIK_EXACT_DUPLICATE_REGIONAL_AUDIT"])
OUT=Path(os.environ["SKARVIK_DUPLICATE_REGIONAL_SUPPRESSION_RESULT"])
DIR=ROOT/"Saved/SkarvikCity/FinalRegionalNearDuplicateSuppression_20261101"
BACKUP=DIR/"final-before-duplicate-suppression.umap"
RESTORE=DIR/"restore-hidden-SK-RX-003-B-actors.json"
B_PREFIX="SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
A_PREFIX="SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
TAG="SKARVIK_REGIONAL_DUPLICATE_SAFE_SUPPRESSED"
doc={"state":"FAILED","sourceMapsModified":False,
     "originalSourceRoadActorsDeleted":False,
     "secondRegionalRoadActorsDeleted":False,
     "firstRegionalRoadsStillVisible":False,
     "BActorsSafelyHidden":0,"BActorsWithCollisionDisabled":0,
     "allRegionalRoutesDriveable":False,"SM5PlaytestValidated":False,
     "full382RoadsFinished":False}
try:
 marker=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
     or not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Not the trusted isolated C stage")
 if not MAP.is_file() or any(not p.is_file() for p in SOURCES):
  raise RuntimeError("Protected staged or source World Partition map missing")
 if BACKUP.exists() or RESTORE.exists():
  raise RuntimeError("Regional duplicate suppression previously attempted, refuse repeated modification")
 audited=json.loads(AUDIT.read_text(encoding="utf-8-sig"))
 if audited.get("state")!="EXACT_SAME_ROUTE_REGIONAL_DUPLICATE_SECOND_BATCH_SURVEY_ONLY":
  raise RuntimeError("Missing native independently audited exact overlap report")
 expected=audited.get("duplicateBActorLabels",[])
 if (audited.get("exactSameRouteXYNearDuplicateCount")!=160
     or len(expected)!=160 or len(set(expected))!=160
     or audited.get("routeCounts")!={"SK-RX-003":160}
     or any(not name.startswith(B_PREFIX+"SK-RX-003_") for name in expected)):
  raise RuntimeError("Untrusted exact native duplicate route label set")
 checks={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 wp=unreal.WorldPartitionBlueprintLibrary
 if not lv.load_level(TARGET):raise RuntimeError("Cannot load native final seven-island World Partition")
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(prefix):return sum(s.startswith(prefix) for s in labels)
 for prefix,value in (
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
  ("SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_E5_",121),
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298),
  (A_PREFIX,663),(B_PREFIX,992)):
  if count(prefix)!=value:raise RuntimeError("Previously saved original actor group missing "+prefix)
 chosen=[d for d in desc if str(d.label) in set(expected)]
 if len(chosen)!=160:raise RuntimeError("All exact duplicate regional WP descriptors not present")
 # All duplicate actor packages remain valid, only their rendering and collision
 # state changes. Store a full restoration record BEFORE first mutation.
 originals=[]
 for i in range(0,len(chosen),40):
  wp.load_actors([d.guid for d in chosen[i:i+40]])
 loaded={a.get_actor_label():a for a in actors.get_all_level_actors()}
 for d in chosen:
  lab=str(d.label)
  actor=loaded.get(lab)
  if not isinstance(actor,unreal.StaticMeshActor):
   raise RuntimeError("Cannot load original regional StaticMeshActor "+lab)
  c=actor.get_component_by_class(unreal.StaticMeshComponent)
  mesh=c.get_editor_property("static_mesh") if c else None
  if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Actual original regional mesh missing "+lab)
  if TAG in [str(x) for x in actor.tags]:
   raise RuntimeError("Duplicate regional actor already suppressed "+lab)
  original=actor.get_actor_transform()
  originals.append({
    "label":lab, "sourceMesh":mesh.get_path_name(),
    "previousVisibility":True,"previousCollisionProfile":"BlockAll",
    "previousHiddenInGame":False,
    "originalLocation":[float(original.translation.x),float(original.translation.y),float(original.translation.z)],
    "originalTags":[str(t) for t in actor.tags]})
 DIR.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(MAP.read_bytes()).hexdigest():
  raise RuntimeError("Could not validate original final map backup")
 RESTORE.write_text(json.dumps({
   "world":TARGET,"reversible":True,"operation":"hide duplicated exact B road actors, NO deletion",
   "sourceAuditState":audited["state"],"previousActors":originals,
   "restoreWith":"set StaticMesh visibility True, collision BlockAll, actor hiddenInGame False",
   "noOriginalDModification":True},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 for row in originals:
  actor=loaded[row["label"]]
  c=actor.get_component_by_class(unreal.StaticMeshComponent)
  c.set_visibility(False,True)
  c.set_collision_profile_name("NoCollision")
  actor.set_actor_hidden_in_game(True)
  actor.tags=list(actor.tags)+[unreal.Name(TAG)]
  doc["BActorsSafelyHidden"]+=1
  doc["BActorsWithCollisionDisabled"]+=1
 if doc["BActorsSafelyHidden"]!=160:
  raise RuntimeError("Not all audited exact overlapping B actors were suppressed")
 if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Native actor visibility/collision state changes could not persist")
 for p in SOURCES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=checks[str(p)]:
   raise RuntimeError("Original protected source map unexpectedly modified")
 doc.update(state="FINAL_SKARVIK_160_EXACT_SK_RX_003_DUPLICATE_ASPHALT_ACTORS_REVERSIBLY_HIDDEN",
    sourceMapsModified=False,originalSourceRoadActorsDeleted=False,
    secondRegionalRoadActorsDeleted=False,firstRegionalRoadsStillVisible=True,
    firstRegionalActorCountRetained=663,secondRegionalActorCountRetained=992,
    secondRegionalActorsRemainingActive=832,restorationManifest=str(RESTORE),
    exactSourceAuditMatched=True)
 unreal.log("SKARVIK_FINAL_EXACT_DUPLICATE_REGIONAL_MESHES_HIDDEN="+str(doc["BActorsSafelyHidden"]))
except Exception as e:
 doc["error"]=str(e);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_REVERSIBLE_REGIONAL_DUPLICATE_HIDING_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
