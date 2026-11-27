"""Safely embed a native CitySample Big City World reference as LevelInstance in the
real populated graded SKARVIK 48 km World Partition map, WITHOUT loading 86k
City Sample external actors. Saving the reference ≠ city visuals/playability.
"""
from pathlib import Path
import hashlib,json,os,traceback,shutil
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
CITY="/Game/Map/Big_City_LVL"
MAP_FILE=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
SOURCE_FILE=ROOT/"Content/Map/Big_City_LVL.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/BigCityNativeReferencePilot20261031/before-city-reference.umap"
OUT=Path(os.environ["SKARVIK_BIGCITY_REFERENCE_REPORT"])
LABEL="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
report={"state":"FAILED","targetMap":PKG,"sourceCity":CITY,
        "cityLevelReferenceSaved":False,"sourceCityActorsStreamedAndVisible":False,
        "bigCityFullIntegrationVerified":False,"SM5VisualGameplayTested":False,
        "roadsStillPreserved":False,"originalDModified":False,"sourceCityModified":False}
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
        raise RuntimeError("Wrong isolated stage")
    if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Wrong stage marker")
    for f in (MAP_FILE,SOURCE_FILE,D,V1):
        if not f.is_file(): raise RuntimeError("Required world missing "+str(f))
    if BACKUP.exists():raise RuntimeError("Reference pilot was already attempted, refuse duplicate")
    if any((ROOT/"Content"/x).exists() for x in ("Crowd","Vehicle")):
        raise RuntimeError("CitySample crowd and vehicle sources not authorised for copy")
    hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (D,V1,SOURCE_FILE)}
    cls=getattr(unreal,"LevelInstance",None)
    if cls is None or not hasattr(cls,"set_world_asset") or not hasattr(cls,"get_world_asset"):
        raise RuntimeError("Native LevelInstance does not support World asset reference")
    city=unreal.load_asset(CITY)
    if not city or not isinstance(city,unreal.World):
        raise RuntimeError("Unreal cannot load source CitySample UWorld")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(PKG):
        raise RuntimeError("Cannot open verified graded SKARVIK")
    w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not w or w.get_path_name().split(".")[0]!=PKG:
        raise RuntimeError("Wrong current native World Partition map")
    desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    names=[str(a.label) for a in desc]
    houses=sum(s.startswith("SKARVIK_GRADED_SITE_") for s in names)
    oldroads=sum(s.startswith("SKARVIK_GRADED_ROAD_") for s in names)
    newroads=sum(s.startswith("SKARVIK_EXPANSION_ROAD_") for s in names)
    if houses!=1039 or oldroads!=126 or newroads!=1668:
        raise RuntimeError("Existing 1039 buildings / 1794 road actors unexpectedly missing")
    if any(LABEL==name for name in names):
        raise RuntimeError("Already staged Big City LevelInstance, no duplicate")
    BACKUP.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(MAP_FILE,BACKUP)
    if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(MAP_FILE.read_bytes()).hexdigest():
        raise RuntimeError("Cannot confirm safe graded pre-CitySample backup")
    terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    h=float(terrain.skarvik_graded_height(2000.,-8000.))
    # Preserve source city native scale (no forced shrink) and preserve original CitySample.
    inst=actors.spawn_actor_from_class(cls,unreal.Vector(200000.,800000.,h*100.))
    if not inst:raise RuntimeError("Native LevelInstance actor could not spawn")
    inst.set_actor_label(LABEL)
    inst.tags=[unreal.Name("SKARVIK_CENTRE"),unreal.Name("CITY_SAMPLE_SOURCE_REFERENCE_NOT_STREAMED")]
    result=inst.set_world_asset(city)
    if result is False:raise RuntimeError("Native World asset setter refused Big City source")
    pointed=inst.get_world_asset()
    if not pointed or pointed.get_path_name().split(".")[0]!=CITY:
        raise RuntimeError("LevelInstance does not retain Big City source reference")
    # CRITICAL: do not call load_level_instance()/get_loaded_level() here; a
    # prior full City Sample load failed after 32 minutes in this environment.
    report["referenceResolvesInCurrentSession"]=True
    report["sourceActorPackageCountAuditedEarlier"]=86608
    report["actorBeforeCommit"]={"houses":houses,"nativeRoadMeshes":oldroads+newroads}
    if not levels.save_all_dirty_levels():
        raise RuntimeError("Failed to persist native graded map reference")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Failed to persist only dirty WP actor packages")
    for f in (D,V1,SOURCE_FILE):
        if hashlib.sha256(f.read_bytes()).hexdigest()!=hashes[str(f)]:
            raise RuntimeError("Protected original modified (cannot claim success)")
    report.update(state="BIG_CITY_NATIVE_WORLD_REFERENCE_SAVED_IN_GRADED_SKARVIK_NOT_STREAMED",
        cityLevelReferenceSaved=True,roadsStillPreserved=True,
        existingBuildingActors=houses,existingRoadMeshActors=oldroads+newroads,
        cityAnchorKm=[2,-8],cityElevationM=round(h,2))
    unreal.log("SKARVIK_BIG_CITY_NATIVE_WORLD_REFERENCE_SAVED=true")
except Exception as e:
    report["error"]=str(e);report["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_BIG_CITY_NATIVE_REFERENCE_FAILED="+str(e))
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
