"""Selectively migrate audited real dry native asphalt actors into final coastal
SKARVIK. Never place roads in the 7-island ocean, never fake continuity.
Safe original-actor labels must come from independent native run 41302837710.
The 8,586 rejected ocean/slope segments are NOT copied.
"""
import os,json,math,shutil,hashlib,traceback
from pathlib import Path
from collections import Counter
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
DEST="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
AUDIT=Path(os.environ["SKARVIK_FINAL_SAFE_ROAD_ACTOR_AUDIT"])
OUT=Path(os.environ["SKARVIK_FINAL_REAL_ROADS_MIGRATION_REPORT"])
MAP=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
         ROOT/"Content/Map/Big_City_LVL.umap",
         ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
         Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
BACKUP=ROOT/"Saved/SkarvikCity/FinalV1NativeDryAsphaltMigration20261101/final-before-safe-original-asphalt.umap"
LABEL="SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_"
report={"state":"FAILED","readOnlyOriginalWorld":True,"nativeDryAsphaltSaved":0,
 "nativeDryAsphaltMetresSaved":0.,"unmigratedUnsafeOriginalActorCount":8586,
 "realSeaCrossingRoadActorsPlaced":0,"fullRoadNetworkContinuous":False,
 "all382PlannedRoadsMigrated":False,"SM5VehicleDrivingTestPassed":False,
 "bridgesPortsAndWaterInfrastructureTested":False,"nativeOriginalMeshTypes":0,
 "perCategoryPavedMeshCount":{},"additionalUnsafeRejectedDuringNativeCopy":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Unsafe C stage marker")
 if not MAP.is_file() or not all(p.is_file() for p in SOURCES):
  raise RuntimeError("Cannot find final/native original maps")
 if BACKUP.exists():raise RuntimeError("Original road replay attempted before; no repeated duplication")
 originalHashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
 a=json.loads(AUDIT.read_text(encoding="utf-8"))
 if a.get("state")!="FINAL_SEVEN_ISLAND_ROAD_3D_SOURCE_COAST_AND_SLOPE_AUDITED_NOT_YET_MIGRATED":
  raise RuntimeError("Missing independently audited original road safe list")
 allowed=a["safeExistingRoadActorLabels"]
 if len(allowed)!=6212 or len(set(allowed))!=6212 or a["unsafeSourceRoadActorCount"]!=8586:
  raise RuntimeError("Untrusted independently audited original dry-road counts")
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 wp=unreal.WorldPartitionBlueprintLibrary
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not level.load_level(SOURCE):raise RuntimeError("Cannot reopen original source roads WP")
 desc=wp.get_actor_descs() or []
 byName={str(d.label):d for d in desc}
 selected=[]
 for name in allowed:
  if name not in byName:raise RuntimeError("Road actor from signed safe audit missing: "+name)
  selected.append(byName[name])
 original=[]
 for offset in range(0,len(selected),64):
  chunk=selected[offset:offset+64]
  wp.load_actors([d.guid for d in chunk])
  loaded={o.get_actor_label():o for o in actors.get_all_level_actors()}
  for d in chunk:
   label=str(d.label);actor=loaded.get(label)
   if not actor or not isinstance(actor,unreal.StaticMeshActor):
    raise RuntimeError("Actual source asphalt actor absent "+label)
   component=actor.get_component_by_class(unreal.StaticMeshComponent)
   mesh=component.get_editor_property("static_mesh") if component else None
   if not isinstance(mesh,unreal.StaticMesh):
    raise RuntimeError("Original asphalt StaticMesh reference missing "+label)
   p=actor.get_actor_location();rot=actor.get_actor_rotation();scale=actor.get_actor_scale3d()
   original.append({"sourceLabel":label,"mesh":mesh.get_path_name(),
    "locationCm":[float(p.x),float(p.y),float(p.z)],
    "rotation":[float(rot.pitch),float(rot.yaw),float(rot.roll)],
    "scale":[float(scale.x),float(scale.y),float(scale.z)]})
  wp.unload_actors([d.guid for d in chunk])
 if len(original)!=6212:raise RuntimeError("Native selected original asphalt actor list incomplete")
 if not level.load_level(DEST):raise RuntimeError("Cannot reopen populated final coastal world")
 labels=[str(d.label) for d in wp.get_actor_descs() or []]
 if any(x.startswith(LABEL) for x in labels):
  raise RuntimeError("Real original asphalt road migration already present, refuse duplicate")
 if sum(x.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for x in labels)!=906 or (
  sum(x.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for x in labels)!=128):
  raise RuntimeError("1034 real original buildings missing from final World Partition")
 if sum(x.startswith("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_") for x in labels)!=720:
  raise RuntimeError("720 authentic Big City static meshes not yet migrated")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP,BACKUP)
 if hashlib.sha256(MAP.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
  raise RuntimeError("Cannot confirm native final map backup")
 newheight=lib.skarvik_final_coastal_height
 oldheight=lib.skarvik_graded_height
 models={};categories=Counter()
 for index,rec in enumerate(original):
  path=rec["mesh"]
  if path not in models:
   asset=unreal.EditorAssetLibrary.load_asset(path)
   if not isinstance(asset,unreal.StaticMesh):
    raise RuntimeError("Genuine original road mesh asset missing "+path)
   models[path]=asset
  mesh=models[path]
  bb=mesh.get_bounds();length=max(1.,float(bb.box_extent.x)*.02*abs(rec["scale"][0]))
  loc=rec["locationCm"]
  e=loc[0]/100.;n=-loc[1]/100.
  yaw=rec["rotation"][1];rad=math.radians(yaw)
  dx=math.cos(rad)*length/2.;dn=-math.sin(rad)*length/2.
  check=[float(newheight(e,n)),float(newheight(e+dx,n+dn)),float(newheight(e-dx,n-dn)),
         float(newheight(e-2.5,n)),float(newheight(e+2.5,n))]
  if min(check)<4. or max(check)-min(check)>3.5:
   report["additionalUnsafeRejectedDuringNativeCopy"].append(rec["sourceLabel"])
   continue
  oldH=float(oldheight(e,n))
  delta=(check[0]-oldH)*100.
  p=unreal.Vector(loc[0],loc[1],loc[2]+delta)
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,p)
  if not actor:raise RuntimeError("Native asphalt road actor failed")
  actor.set_actor_label(LABEL+str(index).zfill(5))
  actor.tags=[unreal.Name("SKARVIK_FINAL_REUSED_REAL_ROAD"),
              unreal.Name("SKARVIK_OLD_ROAD_COAST_SAFE")]
  c=actor.get_component_by_class(unreal.StaticMeshComponent)
  if not c or not c.set_static_mesh(mesh):raise RuntimeError("Original real asphalt mesh assignment failed")
  c.set_collision_profile_name("BlockAll")
  angle=rec["rotation"]
  # Preserve original XY alignment; adapt road longitudinal pitch to final
  # terrace elevation rather than keep old graded-landscape pitch.
  signed=(check[1]-check[2])/length
  pitch=math.degrees(math.atan(signed))
  actor.set_actor_rotation(unreal.Rotator(pitch,angle[1],angle[2]),False)
  actor.set_actor_scale3d(unreal.Vector(*rec["scale"]))
  categories[rec["sourceLabel"].split("_ROAD_")[0] if "_ROAD_" in rec["sourceLabel"] else "short-road-or-gateway"]+=1
  report["nativeDryAsphaltSaved"]+=1
  report["nativeDryAsphaltMetresSaved"]+=length
 report["nativeOriginalMeshTypes"]=len(models)
 report["perCategoryPavedMeshCount"]=dict(categories)
 report["nativeDryAsphaltMetresSaved"]=round(report["nativeDryAsphaltMetresSaved"],1)
 report["additionalUnsafeRejectedCount"]=len(report["additionalUnsafeRejectedDuringNativeCopy"])
 if report["nativeDryAsphaltSaved"]<5000:
  raise RuntimeError("Too few actual slope-safe original asphalt meshes accepted; refuse save")
 if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Final 3D dry-road meshes not saved to WP")
 for file in SOURCES:
  if hashlib.sha256(file.read_bytes()).hexdigest()!=originalHashes[str(file)]:
   raise RuntimeError("Original map unexpectedly modified by read-only road extraction")
 report["state"]="FINAL_SEVEN_ISLAND_NATIVE_ASPHALT_SAFE_SUBSET_SAVED_NOT_YET_CONTINUOUS_OR_DRIVEN"
 report["sourceMapsUnchanged"]=True
 unreal.log("SKARVIK_FINAL_GENUINE_OLD_ASPHALT_ACTOR_REPLAY_SAVED="+str(report["nativeDryAsphaltSaved"]))
except Exception as exc:
 report["error"]=str(exc);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_NATIVE_DRY_ROAD_REPLAY_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
