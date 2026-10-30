"""Safely author a NEW, isolated F.A.L.C (26.5km) Unreal Engine 5.8 map.

Offline source files MUST be installed first as 4 verified RAW16 tiles in
<Project>/TerrainSource/FALC. Does not edit DRAZOVIA, SKARVIK or any save.
This is a real native World Partition .umap authoring script, not evidence
it was executed. Requires a working compiled UE Editor on an isolated host.
"""
import hashlib
import json
import os
from pathlib import Path
import traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE="/Game/Maps/PRIGIMALIA_FALC"
MAPFILE=ROOT/"Content/Maps/PRIGIMALIA_FALC.umap"
SOURCE=ROOT/"TerrainSource/FALC"
REPORT=Path(os.environ.get("PRIGIMALIA_FALC_REPORT",
                           str(ROOT/"Saved/FALC/falc-first-native-test.json")))
RESULT={
 "status":"FAILED","mapPackage":PACKAGE,"nativeUmapVerified":False,
 "realLandscapeComponents":0,"collisionVerified":False,"gameplayTested":False,
 "mapAreaKm2":702.25,"landTargetKm2":500,"otherWorldsModified":False,
 "fullNativeWorldBuilt":False,
}

def author():
    # Prevent editing protected original local game project.
    normalized=str(ROOT).replace("/","\\").lower()
    if normalized=="d:\\anomalia" or normalized.startswith("d:\\anomalia\\"):
        raise RuntimeError("Protected D:\\ANOMALIA cannot be edited by authoring script")
    if MAPFILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("Existing FALC world must never be recreated/overwritten")
    if (ROOT/"Content/__ExternalActors__/Maps/PRIGIMALIA_FALC").exists():
        raise RuntimeError("Possible partial World Partition actors; manual audit required")
    if (ROOT/"Content/__ExternalObjects__/Maps/PRIGIMALIA_FALC").exists():
        raise RuntimeError("Possible partial external objects; manual audit required")
    if not SOURCE.is_dir():
        raise RuntimeError("FALC source RAW16 tiles are not installed on this host")
    paths=[SOURCE/f"FALC_x{x:02d}_y{y:02d}.r16"
           for y in range(2) for x in range(2)]
    for tile in paths:
        if not tile.is_file() or tile.stat().st_size!=1009*1009*2:
            raise RuntimeError("Missing or invalid 1009x1009 RAW16: "+str(tile))
    # Validate both directions' shared edges on source bytes before touching UE.
    def row_segment(path,idx):
        with path.open("rb") as file:
            file.seek(idx*1009*2)
            return file.read(1009*2)
    for row in range(2):
        left,right=paths[row*2:row*2+2]
        with left.open("rb") as handle:a=handle.read()
        with right.open("rb") as handle:b=handle.read()
        for j in range(1009):
            if a[2*(j*1009+1008):2*(j*1009+1009)]!=b[2*j*1009:2*j*1009+2]:
                raise RuntimeError("East-West RAW16 seam mismatch")
    for col in range(2):
        north,south=paths[col],paths[2+col]
        with north.open("rb") as handle:a=handle.read()
        with south.open("rb") as handle:b=handle.read()
        if a[-1009*2:]!=b[:1009*2]:
            raise RuntimeError("North-South RAW16 seam mismatch")
    native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native,"create_falc_landscape_tile"):
        raise RuntimeError("FALC native C++ importer must compile before authoring")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels or not actors:raise RuntimeError("Unreal Editor subsystem missing")
    if not levels.new_level(PACKAGE,is_partitioned_world=True):
        raise RuntimeError("Cannot create isolated FALC World Partition level")
    context=unreal.EditorLevelLibrary.get_editor_world()
    if not context or str(context.get_outermost().get_name())!=PACKAGE:
        raise RuntimeError("Loaded Unreal world does not match independent FALC")
    num_components=0
    for row in range(2):
        for col in range(2):
            tile=native.create_falc_landscape_tile(col,row)
            if not tile:raise RuntimeError(f"FALC quadrant {col},{row} failed native import")
            n=len(tile.get_components_by_class(unreal.LandscapeComponent))
            if n!=64:raise RuntimeError("Bad number of real Landscape components")
            num_components+=n
    if num_components!=256:raise RuntimeError("World has missing Landscape components")
    # Grounded spawn test: search only actual land, never assume the water is safe.
    raw=paths[0].read_bytes()
    import struct
    spawn=None
    for row in range(150,950,75):
        for col in range(150,950,75):
            value=struct.unpack_from("<H",raw,2*(row*1009+col))[0]
            h=(value-32768)/16.
            if 25<=h<=100:
                west=-13250+col*(13250/1008.)
                south=-13250+row*(13250/1008.)
                spawn=(west,south,h)
                break
        if spawn is not None:break
    if spawn is None:raise RuntimeError("No suitable dry spawn in first tile")
    p=actors.spawn_actor_from_class(unreal.PlayerStart,
       unreal.Vector(spawn[0]*100,spawn[1]*100,spawn[2]*100+185))
    if not p:raise RuntimeError("Could not create PlayerStart")
    p.set_actor_label("FALC_InitialTestSpawn")
    # Lighting is a preview, not certified biome texture, wildlife or ocean.
    sun=actors.spawn_actor_from_class(unreal.DirectionalLight,
       unreal.Vector(0,0,500000),unreal.Rotator(-50,-20,0))
    if not sun:raise RuntimeError("Could not create preview lighting")
    sun.set_actor_label("FALC_DaylightPreview")
    actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,10000))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
    if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Native .umap or external actors failed to save")
    if not MAPFILE.is_file() or MAPFILE.stat().st_size<1024:
        raise RuntimeError("Real Unreal .umap file not verified on disk")
    RESULT.update(status="FALC_NATIVE_LEVEL_SAVED_NOT_PLAYTESTED",
        nativeUmapVerified=True,fullNativeWorldBuilt=True,
        realLandscapeComponents=num_components,
        mapFileBytes=MAPFILE.stat().st_size,
        sourceHashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        spawnMeters=list(spawn))
try:
    author()
except Exception as e:
    RESULT["error"]=str(e)
    RESULT["traceback"]=traceback.format_exc()
    raise
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(RESULT,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    unreal.log("FALC_NATIVE_AUTHOR_REPORT="+str(REPORT))
