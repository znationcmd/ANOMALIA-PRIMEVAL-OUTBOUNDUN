"""Create a separate NASDARAS 18 x 26 km / 468 km2 dry World Partition map.

Built in the actual original D:\ANOMALIA\unreal UE project. Never overwrites
existing worlds. Uses existing native C++ landscape heightfield API.
Creates only a physical landscape, player start and NON-PLAYABLE editor guide
markers; NO fake 3D wells, no tunnels, no visible water or gameplay claims.
"""
import json,math,os,traceback
from pathlib import Path
import unreal

IDENT="NASDARAS"
PACKAGE="/Game/Maps/PRIGIMALIA_NASDARAS"
PROJECT=Path(unreal.Paths.project_dir()).resolve()
EXPECTED=Path("D:/ANOMALIA/unreal").resolve()
MAP=PROJECT/"Content/Maps/PRIGIMALIA_NASDARAS.umap"
REPORT=Path(os.environ.get("NASDARAS_WORLD_REPORT",str(PROJECT/"Saved/Nasdaras/report.json")))
LAYOUT=Path(os.environ.get("NASDARAS_LAYOUT_PATH",""))
result={"state":"FAILED","name":"NASDARAS","sizeKm":[18,26],"areaKm2":468,
        "worldPartitionSaved":False,"nativeTerrainCreated":False,
        "originalMapFilesModified":False,"surfaceWaterActorsPlaced":0,
        "actualRepairableWellActorsPlaced":0,"tunnelSegmentsBuilt":0,
        "undergroundPhysicalTraversalTested":False,"gameplayPlaytested":False}
try:
    if PROJECT!=EXPECTED:raise RuntimeError("Refuse wrong Unreal project: must use D:/ANOMALIA/unreal")
    if not (PROJECT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
        raise RuntimeError("Original world missing")
    if not LAYOUT.is_file():raise RuntimeError("NASDARAS map layout JSON missing")
    plan=json.loads(LAYOUT.read_text(encoding="utf-8"))
    if plan.get("mapId")!="nasdaras-v1" or plan.get("sizeMetres")!={"eastWest":18000,"northSouth":26000}:
        raise RuntimeError("Wrong map plan")
    if plan["waterPolicy"]["surfaceWaterAllowed"] is not False or plan["underground"]["wellCount"]!=10:
        raise RuntimeError("NASDARAS no-surface-water/well rules differ")
    external=PROJECT/"Content/__ExternalActors__/Maps/PRIGIMALIA_NASDARAS"
    objects=PROJECT/"Content/__ExternalObjects__/Maps/PRIGIMALIA_NASDARAS"
    if any(p.exists() for p in (MAP,external,objects)) or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("NASDARAS or partial World Partition data already exists, refuse overwrite")
    native=(getattr(unreal,"AnomaliaPrimevalRequestedWorldLibrary",None)
        or getattr(unreal,"AnomaliaZPrigimaliaRequestedWorldLibrary",None))
    if native is None or not hasattr(native,"create_named_world_landscape") or not hasattr(native,"named_world_height"):
        raise RuntimeError("Native requested-world module not compiled")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels or not actors:raise RuntimeError("Editor level/actor subsystems unavailable")
    if not levels.new_level(PACKAGE,is_partitioned_world=True):
        raise RuntimeError("Could not create new, separate World Partition map")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name().split(".")[0]!=PACKAGE:
        raise RuntimeError("Unexpected active Unreal map; refuse writing")
    landscape=native.create_named_world_landscape(IDENT)
    if not landscape:raise RuntimeError("Native 18x26km landscape generation returned no actor")
    proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    comps=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
    collision=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
    if comps!=256 or collision!=256:
        raise RuntimeError("Landscape component/collision mismatch: %s/%s"%(comps,collision))
    get_height=lambda east,north:float(native.named_world_height(IDENT,east,north))
    spawn_candidates=[(0,0),(-2200,4800),(800,3500),(3500,-3500),(-4300,-4500),
                      (500,9000),(0,-8000),(-4000,9000)]
    spawn=None
    for east,north in spawn_candidates:
        h=get_height(east,north)
        around=[get_height(east+dx,north+dy) for dx in (-8,8) for dy in (-8,8)]
        if 20<h<1500 and max(around)-min(around)<3:
            spawn=(east,north,h);break
    if not spawn:raise RuntimeError("No walkable, level, dry candidate for player start")
    def marker(cls,label,east,north,offset=150):
        z=100*get_height(east,north)+offset
        actor=actors.spawn_actor_from_class(cls,unreal.Vector(east*100,-north*100,z))
        if not actor:raise RuntimeError("Unable to spawn "+label)
        actor.set_actor_label(label)
        return actor
    marker(unreal.PlayerStart,"NASDARAS_OriginalDryPlayerSpawn",*spawn[:2],offset=180)
    sun=marker(unreal.DirectionalLight,"NASDARAS_DrySun",0,0,offset=45000)
    sun.set_actor_rotation(unreal.Rotator(-42.,-35.,0.),False)
    marker(unreal.SkyLight,"NASDARAS_SkyLight",0,0,offset=10000)
    marker(unreal.SkyAtmosphere,"NASDARAS_SkyAtmosphere",0,0,offset=0)
    # Planning references only, deliberately invisible in gameplay.
    # Do NOT substitute TargetPoints for playable well/tunnel meshes.
    for well in plan["underground"]["wells"]:
        loc=well["coordinatesMeters"]
        marker(unreal.TargetPoint,"NASDARAS_PLANNED_ONLY_"+well["id"],
               float(loc["east"]),float(loc["north"]),offset=200)
    for site in plan["settlements"]:
        marker(unreal.TargetPoint,"NASDARAS_PLANNED_ONLY_"+site["id"],
               float(site["east"]),float(site["north"]),offset=200)
    # Never spawn WaterBody, Lake, River, WaterMesh, or Ocean actors.
    if not levels.save_all_dirty_levels():raise RuntimeError("Unable to save map .umap")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Unable to save World Partition actor data")
    if not MAP.is_file() or MAP.stat().st_size<1024:
        raise RuntimeError("Real native .umap not produced")
    result.update(state="NATIVE_DRY_LANDSCAPE_SAVED_UNDERGROUND_CONTENT_NOT_BUILT",
        worldPartitionSaved=True,nativeTerrainCreated=True,
        unrealMapFile=str(MAP),unrealMapBytes=MAP.stat().st_size,
        landscapeComponents=comps,collisionComponents=collision,
        playerStartMetres=spawn,plannedWellMarkers=10,
        plannedSettlementMarkers=len(plan["settlements"]))
    unreal.log("NASDARAS_NATIVE_DRY_WORLD_SAVED="+str(MAP))
except Exception as exc:
    result["error"]=str(exc)
    result["traceback"]=traceback.format_exc()
    unreal.log_error("NASDARAS_WORLD_ERROR="+str(exc))
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    unreal.log("NASDARAS_WORLD_REPORT="+str(REPORT))
