"""Import the USER'S REAL F.A.L.C topo, 26.5 x 26.5 km, from verified original RAW16.
This is a NEW persistent World Partition .umap in the existing native 14-map
project. It does NOT modify any existing world or regenerate SKARVIK.
Heights are inferred from the supplied illustrated map, not a surveyed DEM.
"""
import hashlib
import json
import os
import struct
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
STAGE="ANOMALIAZ_SKARVIK_STAGE_41188816555"
PACKAGE="/Game/Maps/PRIGIMALIA_FALC"
BASE=ROOT/"TerrainSource/FALC"
SOURCE=BASE/"FALC_26_5KM_MASTER_2017.r16"
MANIFEST=BASE/"FALC_IMPORT_MANIFEST.json"
FILE=ROOT/"Content/Maps/PRIGIMALIA_FALC.umap"
EXT_ACT=ROOT/"Content/__ExternalActors__/Maps/PRIGIMALIA_FALC"
EXT_OBJ=ROOT/"Content/__ExternalObjects__/Maps/PRIGIMALIA_FALC"
REPORT=Path(os.environ.get("ANOMALIAZ_FALC_NATIVE_REPORT",str(ROOT/"Saved/FALC/native-falc-26-5km-import.json")))
EXPECTED_SHA="1d3ff52ed30338b59e6130a37aacc7e2a34367b7bc3b28faf4897b3bcfe6b5b7"
N=2017
SIDE=26500
result=dict(
 state="NOT_STARTED",
 exactNativeWorldSaved=False, worldPartitionExpected=True,
 nativeGamePackaged=False, publiclyPlayable=False,
 other14MapsModified=False, originalDProjectModified=False,
 syntheticEstimatedMountainAltitude=True, originalUserCoastReferenceUsed=True,
 actualSourceR16Sha256=None, collisionComponents=0, landscapeComponents=0
)
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def sample_height(data,col,row):
    col=max(0,min(N-1,col));row=max(0,min(N-1,row))
    encoded=struct.unpack_from("<H",data,2*(row*N+col))[0]
    return (encoded-32768)/16.0

try:
    if STAGE not in str(ROOT).upper():
        raise RuntimeError("FALC must author in original isolated 14-world SKARVIK stage")
    marker=ROOT/".skarvik-ci-stage-marker"
    if not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("The protected original 7-island stage marker does not match")
    # Final SKARVIK and 13 other existing .umap files must all be present.
    existing=["PRIGIMALIA_SKARVIK_FINAL_v1","ANOMALIA_Inhabited_v2",
              "PRIGIMALIA_KARSKOV","PRIGIMALIA_VORGRAD","PRIGIMALIA_NEMORIS",
              "PRIGIMALIA_DRAKHEIM","PRIGIMALIA_SOLYNACALYRA",
              "PRIGIMALIA_NEXAVARKHOS","PRIGIMALIA_CHERNASKALUXRIA",
              "PRIGIMALIA_KOLCHIEM_ORIGINS","PRIGIMALIA_ROSKATVIA_B1",
              "PRIGIMALIA_NOGOKV_51","PRIGIMALIA_PARADISIOMANIA",
              "PRIGIMALIA_DEADROOT"]
    missing=[name for name in existing
             if not (ROOT/"Content/Maps"/(name+".umap")).is_file()]
    if missing:raise RuntimeError("Refusing FALC until 14 actual maps are present: "+", ".join(missing))
    if FILE.exists() or EXT_ACT.exists() or EXT_OBJ.exists() or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("A FALC .umap or external actor folder already exists; refuse overwriting prior work")
    if not SOURCE.is_file() or SOURCE.stat().st_size!=N*N*2:
        raise RuntimeError("The USER'S FALC 26.5km original 2017 RAW16 source file is missing")
    actual=sha256(SOURCE)
    result["actualSourceR16Sha256"]=actual
    if actual!=EXPECTED_SHA:
        raise RuntimeError("The FALC RAW16 does not match user's original Oct 31 terrain")
    data=SOURCE.read_bytes()
    if MANIFEST.is_file():
        manifest=json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
        if manifest.get("masterSha256")!=EXPECTED_SHA or manifest.get("masterAxis")!=N:
            raise RuntimeError("The original FALC manifest does not match terrain source")
    # Locate natural flat dry ground from ORIGINAL RAW16, not arbitrary zero spawn.
    spawn=None
    for radius in [0,110,240,400,560,700,840]:
        cx=N//2;cy=N//2
        for direction in range(12):
            from math import cos,sin,pi
            x=int(round(cx+radius*cos(2*pi*direction/12)))
            y=int(round(cy+radius*sin(2*pi*direction/12)))
            h=sample_height(data,x,y)
            if not (8.0<h<650.0):continue
            hs=[sample_height(data,x+dx,y+dy) for dx in (-2,2) for dy in (-2,2)]
            if max(hs)-min(hs)>3.5:continue
            e=-SIDE/2+SIDE*x/(N-1)
            n=SIDE/2-SIDE*y/(N-1)
            spawn=(e,n,h)
            break
        if spawn:break
    if not spawn:
        raise RuntimeError("Original FALC RAW16 has no verified safe dry PlayerStart")
    subsystem=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not subsystem or not actors or not subsystem.new_level(PACKAGE,is_partitioned_world=True):
        raise RuntimeError("Cannot create a NEW partitioned FALC level; no substitute level")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name().split(".")[0]!=PACKAGE:
        raise RuntimeError("Unreal editor is not in the original new FALC package")
    native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native,"create_falc_raw16_landscape"):
        raise RuntimeError("The genuine FALC RAW16 C++ importer is not compiled and registered")
    landscape=native.create_falc_raw16_landscape(str(SOURCE))
    if not landscape:
        raise RuntimeError("The real native FALC RAW16 landscape importer refused the heightmap")
    proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
    collisions=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
    if components!=256 or collisions!=256:
        raise RuntimeError("FALC 26.5km native terrain or collision invalid: %s / %s"%(components,collisions))
    def place(actor_class,label,x,y,z):
        actor=actors.spawn_actor_from_class(actor_class,unreal.Vector(x,y,z))
        if not actor:raise RuntimeError("Cannot spawn native FALC actor "+label)
        actor.set_actor_label("PRIGIMALIA_FALC_"+label)
        return actor
    place(unreal.PlayerStart,"SafeDryPlayerStart",spawn[0]*100,-spawn[1]*100,spawn[2]*100+190)
    sun=place(unreal.DirectionalLight,"Sun",0,0,55000)
    sun.set_actor_rotation(unreal.Rotator(-43,-25,0),False)
    place(unreal.SkyLight,"SkyLight",0,0,15000)
    place(unreal.SkyAtmosphere,"SkyAtmosphere",0,0,0)
    if not subsystem.save_all_dirty_levels():
        raise RuntimeError("FALC level could not be saved to real .umap")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("FALC World Partition actor packages could not be saved")
    if not FILE.is_file() or FILE.stat().st_size<1024:
        raise RuntimeError("FALC new Unreal .umap not written")
    result.update(
        state="ORIGINAL_FALC_2017_RAW16_IMPORTED_NATIVE_WORLD_SAVED_REOPEN_NOT_YET_TESTED",
        exactNativeWorldSaved=True,
        world="/Game/Maps/PRIGIMALIA_FALC",
        widthMeters=SIDE,heightMeters=SIDE,
        sourceIsIllustratedTopographyWithEstimatedElevation=True,
        originalManifestSha256=EXPECTED_SHA,
        playerStartMeters=spawn,
        landscapeComponents=components,
        collisionComponents=collisions,
        bytes=FILE.stat().st_size
    )
    unreal.log("FALC_15TH_ORIGINAL_RAW16_UE_WORLD_SAVED=true")
except Exception as exc:
    result["state"]="FAILED_NO_EXISTING_MAP_REPLACED"
    result["error"]=str(exc)
    result["traceback"]=traceback.format_exc(limit=12)
    unreal.log_error("FALC_NATIVE_IMPORT_ERROR="+str(exc))
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("FALC_NATIVE_IMPORT_REPORT="+str(REPORT))
