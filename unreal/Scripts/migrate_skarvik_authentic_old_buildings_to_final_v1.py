"""Safely migrate original authentic StaticMesh houses from old two native worlds
into single new 7-island 48km FINAL_v1 coast, without copying ocean-spanning roads.
Migrate graded source's 110 non-island site houses to 110 dry target mainland pads,
and island source's 128 original 15 dry island town cores.
Original source WP worlds/actors remain unchanged. CitySample meshes and roads are
intentionally separate follow-on phases. No gameplay-complete claim.
"""
from pathlib import Path
import os,json,math,hashlib,shutil,traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
STAGE_MARKER=ROOT/".skarvik-ci-stage-marker"
FINAL="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
SOURCE_GRADED="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
SOURCE_ISLAND="/Game/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1"
MAIN=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
PROTECTED=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
)
BACKUP=ROOT/"Saved/SkarvikCity/FinalV1AuthenticOriginalBuildingMigration_20261101/final-before-houses.umap"
PLAN=Path(os.environ["SKARVIK_FINAL_BUILDING_MIGRATION_PLAN"])
ISLAND_PLAN=Path(os.environ["SKARVIK_FINAL_ISLAND_MIGRATION_PLAN"])
OUT=Path(os.environ["SKARVIK_FINAL_BUILDING_MIGRATION_REPORT"])
NEW_GRADED="SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_"
NEW_ISLAND="SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_"
report={"state":"FAILED","target":FINAL,"readOnlySources":True,
        "sourceGradedNativeActorCount":0,"sourceIslandNativeActorCount":0,
        "originalActualGradedMeshActorsSaved":0,
        "originalActualIslandMeshActorsSaved":0,
        "sourceCitySampleActorsCopied":0,"regionalRoadActorsCopied":0,
        "sourceWorldsChanged":False,"sourceOriginalActorDeleted":False,
        "oldMainlandBuildingMeshesPreserved":False,"oldCitySampleFullyMigrated":False,
        "SM5GameplayValidationPassed":False,"rejectedSourceActors":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or STAGE_MARKER.read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Wrong C native world stage marker")
 if not MAIN.is_file() or not all(p.is_file() for p in PROTECTED):
  raise RuntimeError("New final world / protected source missing")
 if BACKUP.exists():raise RuntimeError("Final source-house copy already attempted")
 oldsha={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in PROTECTED}
 plan=json.loads(PLAN.read_text(encoding="utf-8"))
 islands=json.loads(ISLAND_PLAN.read_text(encoding="utf-8"))
 sites={s["id"]:s for s in plan["sites"]}
 if len(sites)!=125 or len(islands["islands"])!=7:
  raise RuntimeError("Untrusted landmask/site migration source")
 islandSiteIds={s["id"] for i in islands["islands"] for s in i["settlements"]}
 if len(islandSiteIds)!=15:raise RuntimeError("Missing island locality IDs")
 existingOffshore={s["id"] for s in sites.values() if s["hasExistingIslandNativeCore"]}
 if len(existingOffshore)!=14:
  raise RuntimeError("Untrusted source original island town IDs")
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 wp=unreal.WorldPartitionBlueprintLibrary
 saved={"graded":[],"island":[]}
 def extract(pkg,prefix,sourceKind):
  if not level.load_level(pkg):raise RuntimeError("Cannot reopen native source "+pkg)
  des=wp.get_actor_descs() or []
  desired=[d for d in des if str(d.label).startswith(prefix)]
  expected=1039 if sourceKind=="graded" else 128
  if len(desired)!=expected:
   raise RuntimeError("Source World Partition original mesh actor count changed "+sourceKind+" "+str(len(desired)))
  report["sourceGradedNativeActorCount" if sourceKind=="graded" else "sourceIslandNativeActorCount"]=len(desired)
  sortedIds=sorted(sites,key=len,reverse)
  actorData=[]
  for offset in range(0,len(desired),64):
   batch=desired[offset:offset+64]
   wp.load_actors([d.guid for d in batch])
   loaded={a.get_actor_label():a for a in subsystem.get_all_level_actors()}
   for d in batch:
    label=str(d.label)
    actor=loaded.get(label)
    if not actor or not isinstance(actor,unreal.StaticMeshActor):
     raise RuntimeError("Original source 3D StaticMesh actor missing "+label)
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh=comp.get_editor_property("static_mesh") if comp else None
    if not isinstance(mesh,unreal.StaticMesh):
     raise RuntimeError("Original source StaticMesh asset missing "+label)
    if sourceKind=="graded":
     rest=label[len(prefix):]
     siteId=next((sid for sid in sortedIds if rest.startswith(sid+"_")),None)
     if not siteId or siteId=="citysample":raise RuntimeError("Graded native settlement ID parsing failed "+label)
     if siteId in existingOffshore:continue # prefer exact true-coast island source cores
    else:
     tags=[str(t) for t in actor.get_editor_property("tags")]
     siteId=next((t[len("SKARVIK_SITE_"):] for t in tags if t.startswith("SKARVIK_SITE_")),None)
     if siteId not in islandSiteIds:
      raise RuntimeError("Native original island building lacks site GUID tag "+label)
    p=actor.get_actor_location()
    angle=actor.get_actor_rotation()
    scale=actor.get_actor_scale3d()
    actorData.append({"id":siteId,"sourceName":label,"mesh":mesh.get_path_name(),
     "locationCm":[float(p.x),float(p.y),float(p.z)],
     "rotation":[float(angle.pitch),float(angle.yaw),float(angle.roll)],
     "scale":[float(scale.x),float(scale.y),float(scale.z)]})
   # Important: release heavy loaded cells before opening another world.
   wp.unload_actors([d.guid for d in batch])
  saved[sourceKind]=actorData
  unreal.log("SKARVIK_FINAL_MIGRATION_REAL_SOURCE_ACTORS_EXTRACTED_{}={}".format(sourceKind.upper(),len(actorData)))
 extract(SOURCE_GRADED,"SKARVIK_GRADED_SITE_","graded")
 extract(SOURCE_ISLAND,"SKARVIK_ISLAND_V1_","island")
 if len(saved["graded"])<650 or len(saved["island"])!=128:
  raise RuntimeError("Source authentic building collection incomplete")
 if not level.load_level(FINAL):raise RuntimeError("Cannot reopen new final 48km islands world")
 desc=wp.get_actor_descs() or []
 if any(str(d.label).startswith((NEW_GRADED,NEW_ISLAND)) for d in desc):
  raise RuntimeError("Migration actors already exist in target, refuse duplicate")
 if sum(str(d.label).startswith("SKARVIK_FINAL_BIG_CITY_PLAYER_START") for d in desc)!=1:
  raise RuntimeError("Wrong final destination or missing original main city PlayerStart")
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(lib,"skarvik_final_coastal_height"):
  raise RuntimeError("Native final coast height API absent")
 h=lib.skarvik_final_coastal_height
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAIN,BACKUP)
 if hashlib.sha256(MAIN.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
  raise RuntimeError("Could not confirm final coast backup integrity")
 cached={}
 per_site={}
 for kind,prefix in (("island",NEW_ISLAND),("graded",NEW_GRADED)):
  for idx,datum in enumerate(saved[kind]):
   sid=datum["id"]
   if sid in sites:
    s=sites[sid]
    shiftX=(s["targetKm"][0]-s["sourceKm"][0])*100000.
    shiftY=-(s["targetKm"][1]-s["sourceKm"][1])*100000.
   else:
    # Provisional PORT DES BRUMES already had original safe island site; no move.
    shiftX=0.;shiftY=0.
   meshPath=datum["mesh"]
   if meshPath not in cached:
    mesh=unreal.EditorAssetLibrary.load_asset(meshPath)
    if not isinstance(mesh,unreal.StaticMesh):
     raise RuntimeError("Authentic source mesh not found by original object path "+meshPath)
    cached[meshPath]=mesh
   mesh=cached[meshPath]
   box=mesh.get_bounds()
   halfX=float(box.box_extent.x)/100.
   halfY=float(box.box_extent.y)/100.
   bottom=(float(box.origin.z)-float(box.box_extent.z))/100.
   e=(datum["locationCm"][0]+shiftX)/100.
   north=-(datum["locationCm"][1]+shiftY)/100.
   samples=[float(h(e+dx,north+dy)) for dx in (-halfX,0,halfX) for dy in (-halfY,0,halfY)]
   grade=max(samples)-min(samples)
   if min(samples)<3.5 or grade>1.5:
    report["rejectedSourceActors"].append({"id":sid,"label":datum["sourceName"],
       "reason":"underwater-or-uneven-final-coastal-terrain","grade":round(grade,2),
       "minimumNativeGroundM":round(min(samples),2)})
    continue
   pos=unreal.Vector((e)*100,-north*100,(max(samples)-bottom+.03)*100)
   actor=subsystem.spawn_actor_from_class(unreal.StaticMeshActor,pos)
   if not actor:raise RuntimeError("Cannot spawn authentic source building on final landscape")
   actor.set_actor_label("{}{}_{}".format(prefix,sid,idx))
   actor.tags=[unreal.Name("SKARVIK_FINAL_MIGRATED_SOURCE_ACTOR"),unreal.Name("SKARVIK_SITE_"+sid)]
   comp=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not comp or not comp.set_static_mesh(mesh):
    raise RuntimeError("Failed to set genuine original source static mesh")
   comp.set_collision_profile_name("BlockAll")
   p,y,r=datum["rotation"]
   actor.set_actor_rotation(unreal.Rotator(p,y,r),False)
   actor.set_actor_scale3d(unreal.Vector(*datum["scale"]))
   field="originalActualGradedMeshActorsSaved" if kind=="graded" else "originalActualIslandMeshActorsSaved"
   report[field]+=1;per_site[sid]=per_site.get(sid,0)+1
 report["nativeSiteCountWithActualOriginalMeshes"]=len(per_site)
 report["originalMainlandSitesWithBuildings"]=len([s for s in per_site if s not in islandSiteIds])
 report["authenticOriginalMeshSourceTypes"]=len(cached)
 report["rejectedActorCount"]=len(report["rejectedSourceActors"])
 if report["originalActualGradedMeshActorsSaved"]<550 or report["originalActualIslandMeshActorsSaved"]<100:
  raise RuntimeError("Too many original native buildings failed terrain-grade checks; do not save")
 if report["nativeSiteCountWithActualOriginalMeshes"]<103:
  raise RuntimeError("Too many of 125 native localities remain without any real original buildings")
 if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Cannot save real final migrated actor packages to World Partition")
 for source in PROTECTED:
  if hashlib.sha256(source.read_bytes()).hexdigest()!=oldsha[str(source)]:
   raise RuntimeError("Source World Partition map unexpectedly changed during guarded migration")
 report["state"]="AUTHENTIC_GRADED_AND_ISLAND_3D_BUILDINGS_COPIED_TO_FINAL_SEVEN_ISLAND_WORLD_NOT_COMPLETE_GAME"
 report["oldMainlandBuildingMeshesPreserved"]=True
 report["sourceWorldsChanged"]=False
 report["nativeActorPackagesSaved"]=True
 report["sourceGradedActorInstancesRetained"]=1039
 report["sourceIslandActorInstancesRetained"]=128
 report["sitesWithoutMigratedBuildings"]=[s["id"] for s in sites.values() if s["id"] not in per_site and s["id"]!="citysample"]
 unreal.log("SKARVIK_FINAL_ORIGINAL_REAL_BUILDINGS_MIGRATED={}".format(
   report["originalActualGradedMeshActorsSaved"]+report["originalActualIslandMeshActorsSaved"]))
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_BUILDING_MIGRATION_BLOCKED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
