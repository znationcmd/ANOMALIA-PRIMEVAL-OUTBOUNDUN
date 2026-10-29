"""Append real garage sectors to the saved inhabited world; retain all original actors.
This is an authoring pass, not a finished-world or playtest assertion.
"""
import json, math, traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path("D:/ANOMALIA/StorageRecovery/apocalypse-regions.json")
MAP="/Game/Maps/ANOMALIA_Inhabited_v2"
SECTOR="/Game/Anomalia/Maps/ANOMALIA_Apocalypse_Garage_v1"
OWNER="ANOMALIA_ApocalypseRegions_v1"
report=dict(state="STARTED",map=MAP,placed=[],rejected=[],playtested=False,wholeMapFinished=False)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
        raise RuntimeError("Original inhabited world missing; no replacement terrain created")
    if not level.load_level(SECTOR): raise RuntimeError("Saved garage sector missing")
    sector_actors=actors.get_all_level_actors()
    boxes=[]
    for a in sector_actors:
        if isinstance(a,unreal.StaticMeshActor):
            p,e=a.get_actor_bounds(False)
            boxes.append(([p.x-e.x,p.y-e.y,p.z-e.z],[p.x+e.x,p.y+e.y,p.z+e.z]))
    if not boxes: raise RuntimeError("Sector has no actual geometry")
    lo=[min(b[0][k] for b in boxes) for k in range(3)]
    hi=[max(b[1][k] for b in boxes) for k in range(3)]
    cx,cy=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2
    rx,ry=(hi[0]-lo[0])/2,(hi[1]-lo[1])/2
    if max(rx,ry)>5000:raise RuntimeError("Sector too large for reserved corner; no scaling applied")
    # Remove only copied global lighting, keeping all source assets and indoor lights.
    global_types=(unreal.DirectionalLight,unreal.SkyLight,unreal.SkyAtmosphere,unreal.ExponentialHeightFog,unreal.PostProcessVolume)
    for a in sector_actors:
        if isinstance(a,global_types): actors.destroy_actor(a)
    if not level.save_current_level():raise RuntimeError("Cleaned sector could not save")
    if not level.load_level(MAP):raise RuntimeError("Original world failed to reopen")
    sector_asset=unreal.load_asset(SECTOR)
    if not sector_asset:raise RuntimeError("Sector world asset did not reload after changing maps")
    library=getattr(unreal,"AnomaliaWorldImportLibrary",None)
    if not library:raise RuntimeError("Compiled world library missing")
    desc=json.loads(library.get_archipelago_actor_descriptors())
    if desc.get("state")!="COPIED_DESCRIPTOR_VALUES":raise RuntimeError("World descriptor verification failed")
    blockers=[d for d in desc["actors"] if d.get("boundsValid") and d.get("nativeClass")=="/Script/Engine.StaticMeshActor" and
        (str(d.get("label","")).startswith("ANOMALIA_Inhabited1_") or
         str(d.get("label","")).startswith("ANOMALIA_Features_")) and
        "SceneryCluster" not in d.get("nativeClass","")]
    existing={d["label"] for d in desc["actors"]}
    sites=library.inhabited_settlement_sites()
    for index,site in enumerate(sites):
        label=OWNER+"_Garage_%02d"%index
        if label in existing:
            report["placed"].append(dict(id=label,existing=True));continue
        found=None
        for de,dn in ((365,365),(-365,365),(365,-365),(-365,-365)):
            east,north=site.x+de,site.y+dn
            x,y=east*100,-north*100
            footprint=[x-rx-200,y-ry-200,x+rx+200,y+ry+200]
            if any(footprint[0]<d["boundsMaxCm"][0] and footprint[2]>d["boundsMinCm"][0] and
                   footprint[1]<d["boundsMaxCm"][1] and footprint[3]>d["boundsMinCm"][1] for d in blockers):
                continue
            heights=[library.inhabited_archipelago_height(east+dx/100,north+dy/100)
                     for dx in (-rx,0,rx) for dy in (-ry,0,ry)]
            if min(heights)<5 or max(heights)-min(heights)>.25:continue
            z=max(heights)*100-lo[2]
            found=(x-cx,y-cy,z,footprint);break
        if not found:
            report["rejected"].append(dict(site=index,reason="NO_DRY_FLAT_CLEAR_CORNER"));continue
        x,y,z,footprint=found
        a=actors.spawn_actor_from_class(unreal.LevelInstance,unreal.Vector(x,y,z))
        if not a or not a.set_world_asset(sector_asset):raise RuntimeError("Level instance failed")
        a.set_actor_label(label);a.tags=[unreal.Name(OWNER),unreal.Name("POI:garage")]
        a.set_editor_property("is_spatially_loaded",True)
        report["placed"].append(dict(id=label,existing=False,positionCm=[x,y,z],sector=SECTOR))
        blockers.append(dict(boundsMinCm=[footprint[0],footprint[1],z],boundsMaxCm=[footprint[2],footprint[3],z+1000]))
    if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Region packages could not save")
    report.update(state="GARAGE_REGIONS_SAVED_NOT_PLAYTESTED",settlementSites=len(sites),sectorBoundsCm=[lo,hi],
                  existingWorldDescriptors=len(desc["actors"]),lootPlaced=False)
except Exception as error:
    report.update(state="FAILED",error=str(error),traceback=traceback.format_exc())
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    unreal.log("ANOMALIA_REGIONS_RESULT="+json.dumps(report))
