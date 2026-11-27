"""Reversibly disable ONLY proven overlaid B-road meshes on SKARVIK FINAL.

The audited native mesh paths/rotations/heights from run 41316507845 must match
again before any mutation. Never delete original actor packages, edit D:,
touch all other 832 B actors, or alter 663 A meshes. Write a restoration manifest
before hiding/disabling collision on the duplicate B actors. Reopen separately.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
WORLD="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
ORIGINAL=(
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap")
AUDIT=Path(os.environ["SKARVIK_FINAL_REGIONAL_ACTUAL_DUPLICATES_RECEIPT"])
OUT=Path(os.environ["SKARVIK_FINAL_REGIONAL_DEDUPLICATION_REPORT"])
BASE=ROOT/"Saved/SkarvikCity/FinalRegionalExactDuplicateNonDestructiveSuppression20261101"
BACKUP=BASE/"final-before-disabling-exact-duplicate-B-road-meshes.umap"
RESTORE=BASE/"exact-original-B-road-flags-for-restoration.json"
TAG="SKARVIK_FINAL_OVERLAID_B_ROAD_DISABLED_REVERSIBLE"
A="SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
B="SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
report={"state":"FAILED","deletedRoadActors":0,"revertedOrMovedRoadMeshes":0,
        "disabledDuplicateBActors":0,"allOriginalMapsUnchanged":False,
        "allRoadsDrivable":False,"fullCitySampleLoaded":False,
        "SM5RenderedProof":False,"worldPackage":WORLD}
try:
 marker=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
     or not marker.is_file()
     or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Untrusted original-coast staged project")
 if not TARGET.is_file() or any(not x.is_file() for x in ORIGINAL):
  raise RuntimeError("Original/staged World Partition map missing")
 if BACKUP.exists() or RESTORE.exists():
  raise RuntimeError("Duplicate suppression already attempted; never repeat")
 audited=json.loads(AUDIT.read_text(encoding="utf-8-sig"))
 if audited.get("state")!="SKARVIK_FINAL_TWO_REGIONAL_PILOTS_REAL_DUPLICATE_MESHES_VERIFIED_READ_ONLY":
  raise RuntimeError("Missing prior native true mesh-identity audit")
 proven=audited.get("verifiedOverlaidActors",[])
 if len(proven)!=160 or len({r["newerB"] for r in proven})!=160 or (
    audited.get("exactSameMeshPathAndDirection")!=160):
  raise RuntimeError("No exact 160-overlapping-B-actor verification manifest")
 for row in proven:
  if not row["olderA"].startswith(A) or not row["newerB"].startswith(B) or (
      row.get("roadId")!="SK-RX-003"):
   raise RuntimeError("Unexpected source route, only SK-RX-003 is authorized")
 native_before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINAL}
 world_before=hashlib.sha256(TARGET.read_bytes()).hexdigest()
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level(WORLD):raise RuntimeError("Final real seven-island map does not reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 checks={A:663,B:992,
  "SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_":6130,
  "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_":1674,
  "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_":1298,
  "SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_":906,
  "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_":128,
  "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_":720}
 for prefix,expected in checks.items():
  if sum(s.startswith(prefix) for s in labels)!=expected:
   raise RuntimeError("Trusted native source actor missing "+prefix)
 byname={str(d.label):d for d in desc}
 selected={label:byname[label] for row in proven for label in (row["olderA"],row["newerB"])
           if label in byname}
 if len(selected)<160 or any(row["olderA"] not in selected or row["newerB"] not in selected for row in proven):
  raise RuntimeError("Proven native asphalt actor descriptor missing")
 wp.load_actors([d.guid for d in selected.values()])
 actor_system=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 loaded={actor.get_actor_label():actor for actor in actor_system.get_all_level_actors()}
 before_flags=[]
 for row in proven:
  older=loaded.get(row["olderA"]);newer=loaded.get(row["newerB"])
  if (not isinstance(older,unreal.StaticMeshActor)
      or not isinstance(newer,unreal.StaticMeshActor)):
   raise RuntimeError("Native source 3D actor cannot be reloaded for duplicate verification")
  c0=older.get_component_by_class(unreal.StaticMeshComponent)
  c1=newer.get_component_by_class(unreal.StaticMeshComponent)
  mesh0=c0.get_editor_property("static_mesh") if c0 else None
  mesh1=c1.get_editor_property("static_mesh") if c1 else None
  if not isinstance(mesh0,unreal.StaticMesh) or not isinstance(mesh1,unreal.StaticMesh):
   raise RuntimeError("Genuine source real StaticMesh missing")
  if mesh0.get_path_name()!=mesh1.get_path_name() or mesh1.get_path_name()!=row["originalStaticMeshAsset"]:
   raise RuntimeError("Native B road is no longer the exact original source road")
  p0=older.get_actor_location();p1=newer.get_actor_location()
  r0=older.get_actor_rotation();r1=newer.get_actor_rotation()
  xy=math.hypot(float(p0.x-p1.x),float(p0.y-p1.y))/100.
  dz=abs(float(p0.z-p1.z))/100.
  yaw=abs((float(r0.yaw)-float(r1.yaw)+180.)%360.-180.)
  pitch=abs((float(r0.pitch)-float(r1.pitch)+180.)%360.-180.)
  if xy>.85 or dz>.45 or yaw>2.5 or pitch>3.:
   raise RuntimeError("Previously verified real road superposition moved; refuse to hide")
  if TAG in [str(tag) for tag in newer.tags]:
   raise RuntimeError("Native road B duplicate has already been disabled")
  if not newer.get_actor_enable_collision() or c1.get_editor_property("visible") is not True:
   raise RuntimeError("Road B source already hidden/collision disabled; require manual review")
  before_flags.append({
   "actor":str(newer.get_actor_label()),"matchedOriginalA":str(older.get_actor_label()),
   "priorActorCollisionEnabled":bool(newer.get_actor_enable_collision()),
   "priorComponentVisible":bool(c1.get_editor_property("visible")),
   "priorComponentHiddenInGame":bool(c1.get_editor_property("hidden_in_game")),
   "priorTags":[str(v) for v in newer.tags],
   "originalMesh":mesh1.get_path_name(),
   "restorationRequiresExplicitOperatorAction":True})
 if len(before_flags)!=160:raise RuntimeError("Fewer than 160 verified original actor flags")
 BASE.mkdir(parents=True,exist_ok=False)
 shutil.copy2(TARGET,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=world_before:
  raise RuntimeError("Cannot verify original staged WorldPartition map snapshot")
 RESTORE.write_text(json.dumps({"state":"BACKED_UP_PREVIOUS_NATIVE_B_ACTOR_FLAGS",
   "reversible":True,"originalStagedMapSHA256":world_before,
   "actorFlags":before_flags},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 # All 160 road meshes individually verified BEFORE any flag mutation.
 for entry in before_flags:
  actor=loaded[entry["actor"]]
  component=actor.get_component_by_class(unreal.StaticMeshComponent)
  actor.modify()
  component.modify()
  actor.set_actor_hidden_in_game(True)
  actor.set_actor_enable_collision(False)
  component.set_visibility(False,True)
  actor.tags=list(actor.tags)+[unreal.Name(TAG)]
  report["disabledDuplicateBActors"]+=1
 if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Reversible hide flag changes not persisted to external actor packages")
 for path in ORIGINAL:
  if hashlib.sha256(path.read_bytes()).hexdigest()!=native_before[str(path)]:
   raise RuntimeError("Protected original map unexpectedly changed")
 report.update(state="FINAL_NATIVE_160_CONFIRMED_OVERLAID_B_ROADS_HIDDEN_COLLISION_DISABLED_REVERSIBLE_NOT_DRIVEN",
  sourceOverlapRoad="SK-RX-003",allOriginalMapsUnchanged=True,
  noOriginalActorDeleted=True,
  oldABAndCityActorCountsKept=checks,
  externalActorOriginalFlagsBackup=str(RESTORE),
  originalFinalMapCopy=str(BACKUP),
  enabledOlderAActorsPreserved=663,
  stillSavedNewerBActors=992,
  stillActiveNewerBActorsAfterSuppression=832,
  verifiedNoDuplicateActorDestroyed=True)
 unreal.log("SKARVIK_FINAL_NATIVE_DUPLICATE_REGIONAL_B_MESHES_REVERSIBLY_DISABLED=160")
except Exception as ex:
 report["error"]=str(ex);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_NATIVE_DUPLICATE_ROAD_DISABLE_FAILED="+str(ex))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
