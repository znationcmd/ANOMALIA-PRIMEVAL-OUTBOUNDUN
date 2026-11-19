"""Create a NEW, independent 15km Apocalyptic Outbreak landscape in the real D: UE project.

This creates a real World Partition .umap, original native landscape with
heightfield collision, a player start, sky, and editorial POI markers. It does
not claim to have constructed complete interiors, broken buildings, roads,
infected gameplay, playable build, or a packaged release.
All existing map packages are preserved. Fail closed on ambiguous conditions.
"""
import json
import math
import os
import traceback
from pathlib import Path

import unreal

NAME="APOCALYPTIC_OUTBREAK"
ROOT=Path(unreal.Paths.project_dir()).resolve()
EXPECTED=Path("D:/ANOMALIA/unreal").resolve()
PKG="/Game/Maps/PRIGIMALIA_"+NAME
UMAP=ROOT/"Content"/"Maps"/("PRIGIMALIA_"+NAME+".umap")
CONFIG_PATH=Path(os.environ.get("APOCALYPTIC_LAYOUT_PATH",""))
REPORT=Path(os.environ.get("APOCALYPTIC_MAP_REPORT",str(ROOT/"Saved"/"ApocalypticOutbreak"/"result.json")))
res={"name":"APOCALYPTIC OUTBREAK","identifier":NAME,"state":"FAILED",
     "sideKm":15,"areaKm2":225,
     "worldPartitionSaved":False,"nativeLandscapeCreated":False,
     "originalMapsModified":False,"buildingsPlaced":0,"completeBuildingInteriorsValidated":False,
     "apocalypticSceneryPlaced":0,"roadsBuilt":0,"waterBuilt":False,
     "zombiesIntegrated":False,"lootIntegrated":False,"playtested":False}
try:
    if ROOT!=EXPECTED:
        raise RuntimeError("Refused: expected actual original D:/ANOMALIA/unreal project")
    if not (ROOT/"Content"/"Maps"/"ANOMALIA_Archipelago_v2.umap").is_file():
        raise RuntimeError("Original SKARVIK map missing; refuse world creation")
    if not CONFIG_PATH.is_file():
        raise RuntimeError("Layout JSON not available")
    cfg=json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if cfg.get("mapId")!="apocalyptic-outbreak-v1" or cfg.get("sizeMetres")!={"eastWest":15000,"northSouth":15000}:
        raise RuntimeError("Wrong map layout, cannot author new level")
    external=ROOT/"Content"/"__ExternalActors__"/"Maps"/("PRIGIMALIA_"+NAME)
    externalobjects=ROOT/"Content"/"__ExternalObjects__"/"Maps"/("PRIGIMALIA_"+NAME)
    if any(x.exists() for x in (UMAP,external,externalobjects)) or unreal.EditorAssetLibrary.does_asset_exist(PKG):
        raise RuntimeError("Destination or partial World Partition data already exists: refuse overwrite")
    native=(getattr(unreal,"AnomaliaPrimevalRequestedWorldLibrary",None)
            or getattr(unreal,"AnomaliaZPrigimaliaRequestedWorldLibrary",None))
    if not native or not hasattr(native,"create_named_world_landscape") or not hasattr(native,"named_world_height"):
        raise RuntimeError("New native requested-world module missing or not compiled")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels or not actors:
        raise RuntimeError("UE editor level/actor subsystems unavailable")
    if not levels.new_level(PKG,is_partitioned_world=True):
        raise RuntimeError("Failed creating unique World Partition level")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name().split(".")[0]!=PKG:
        raise RuntimeError("UE active map isn't new Apocalyptic Outbreak level")
    landscape=native.create_named_world_landscape(NAME)
    if not landscape:
        raise RuntimeError("Native 15x15km landscape generation failed")
    proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
    collisions=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
    if components!=64 or collisions!=64:
        raise RuntimeError("Expected 64 native landscape components/collision components; got %d/%d"%(components,collisions))
    def height(east,north):
        return float(native.named_world_height(NAME,east,north))
    def put(klass,label,east,north,offset=0,rot=None):
        z=height(east,north)*100+offset
        if not math.isfinite(z) or z< -40000 or z>180000:
            raise RuntimeError("Unsafe native terrain height for "+label)
        obj=actors.spawn_actor_from_class(klass,unreal.Vector(east*100,-north*100,z))
        if not obj:
            raise RuntimeError("Could not spawn actor "+label)
        obj.set_actor_label(label)
        obj.tags=[unreal.Name("APOCALYPTIC_OUTBREAK_NEW_WORLD")]
        if rot is not None:
            obj.set_actor_rotation(rot,False)
        return obj

    # Select a locally flat dry spawn near the metropolis, not a crater floor.
    spawn=None
    for east,north in [(0,0),(-400,1100),(-800,1100),(-600,1200),(300,250),
                       (-1800,1200),(-2600,2500),(0,3500)]:
        footprint=[height(east+dx,north+dy) for dx in (-8,8) for dy in (-8,8)]
        h=height(east,north)
        if 20<h<550 and max(footprint)-min(footprint)<3.5:
            spawn=(east,north,h)
            break
    if spawn is None:
        raise RuntimeError("No level, safe native PlayerStart candidate")
    put(unreal.PlayerStart,"APOCALYPTIC_OUTBREAK_PlayerStart",spawn[0],spawn[1],180)
    sun=put(unreal.DirectionalLight,"APOCALYPTIC_OUTBREAK_DuskSun",0,0,55000)
    sun.set_actor_rotation(unreal.Rotator(-30,-85,0),False)
    put(unreal.SkyLight,"APOCALYPTIC_OUTBREAK_SkyLight",0,0,12000)
    put(unreal.SkyAtmosphere,"APOCALYPTIC_OUTBREAK_SkyAtmosphere",0,0,0)
    if hasattr(unreal,"ExponentialHeightFog"):
        put(unreal.ExponentialHeightFog,"APOCALYPTIC_OUTBREAK_Haze",0,0,2500)

    # Honest editor-only anchors; not fake buildings or placeholder meshes.
    labels=[]
    for group in ("settlements","landmarks"):
        for item in cfg[group]:
            e,n=float(item["east"]),float(item["north"])
            if abs(e)>7100 or abs(n)>7100:
                raise RuntimeError("POI outside 15km world: "+item["id"])
            mark=put(unreal.TargetPoint,"AO_PLANNED_"+item["id"],e,n,200)
            labels.append(mark.get_actor_label())

    if not levels.save_all_dirty_levels():
        raise RuntimeError("UE failed to save independent World Partition world")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("UE failed saving partition actor packages")
    if not UMAP.is_file() or UMAP.stat().st_size<=1024:
        raise RuntimeError("Native .umap not present or zero-sized after saving")
    res.update(state="NATIVE_TERRAIN_SAVED_CONTENT_NOT_POPULATED",
        unrealMapPackage=PKG,unrealMapFile=str(UMAP),unrealMapBytes=UMAP.stat().st_size,
        worldPartitionSaved=True,nativeLandscapeCreated=True,
        landscapeComponents=components,collisionComponents=collisions,
        safePlayerSpawnMetres=spawn,plannedSiteMarkersPlaced=len(labels),
        plannedMarkers=labels)
    unreal.log("APOCALYPTIC_OUTBREAK_WORLD_SAVED="+str(UMAP))
except Exception as exc:
    res["error"]=str(exc)
    res["traceback"]=traceback.format_exc()
    unreal.log_error("APOCALYPTIC_OUTBREAK_WORLD_ERROR="+str(exc))
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    unreal.log("APOCALYPTIC_OUTBREAK_REPORT="+str(REPORT))
