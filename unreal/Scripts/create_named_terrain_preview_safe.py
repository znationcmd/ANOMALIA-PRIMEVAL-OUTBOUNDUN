"""Create one isolated named original-procedural terrain PREVIEW in native UE5.8.

Never replace the user's selected photo-derived topographies; these six
previews are NOT the finished terrain or gameplay. No original map may be
opened, saved, renamed or overlaid. World Partition grid conversion deferred.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import traceback
import unreal

SPECS={
 "KARSKOV":(30000,3025,576),
 "VORGRAD":(30000,3025,576),
 "NEMORIS":(20000,2017,256),
 "DRAKHEIM":(20000,2017,256),
 "SOLYNACALYRA":(15000,1513,576),
 "NEXAVARKHOS":(10000,1009,256),
}
ROOT=Path(unreal.Paths.project_dir()).resolve()
ID=os.environ.get("PRIGIMALIA_PREVIEW_MAP","")
OUTPUT=Path(os.environ.get("PRIGIMALIA_PREVIEW_RECEIPT",str(ROOT/"Saved/NamedTerrainPreviews"/(ID+"-run.json"))))
PACKAGE="/Game/Maps/PRIGIMALIA_"+ID+"_TerrainPreview"
UMAP=ROOT/"Content/Maps"/("PRIGIMALIA_"+ID+"_TerrainPreview.umap")
PROTECTED=(
    ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap",
    ROOT/"Content/Maps/ANOMALIA_Inhabited_v2.umap",
    ROOT/"Content/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap",
)
REPORT={"state":"FAILED","id":ID,"package":PACKAGE,"realPhotoSourceImported":False,
        "terrainSource":"PROCEDURAL_PREVIEW_NOT_USER_PHOTO",
        "worldPartitionGridFinalized":False,"gameplayTested":False,
        "originalMapModified":False}

def run():
    if str(ROOT).replace("/","\\").lower().rstrip("\\")!=r"d:\anomaliaz-prigimalia\unreal":
        raise RuntimeError("Only isolated stage permitted; never original D:\\ANOMALIA")
    if ID not in SPECS:
        raise RuntimeError("Unexpected map identifier")
    if OUTPUT.exists():
        raise RuntimeError("Existing preview receipt; refuse to overwrite evidence")
    side,samples,count=SPECS[ID]
    assets=[UMAP,ROOT/"Content/__ExternalActors__/Maps"/("PRIGIMALIA_"+ID+"_TerrainPreview"),
            ROOT/"Content/__ExternalObjects__/Maps"/("PRIGIMALIA_"+ID+"_TerrainPreview")]
    if any(x.exists() for x in assets) or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("Existing preview/native assets: no automatic overwrite")
    sourceR16=ROOT/"TerrainSource"/ID/(ID+".r16")
    if sourceR16.exists():
        raise RuntimeError("User-photo RAW16 present; do not create procedural preview when exact source exists")
    for p in PROTECTED:
        if not p.is_file():
            raise RuntimeError("Missing protected native map: "+str(p))
    protectedBefore={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native,"create_named_world_landscape") or not hasattr(native,"inspect_named_world_preview_components"):
        raise RuntimeError("C++ preview importer/verifier not compiled")
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not editor or not actors:
        raise RuntimeError("Missing native editor subsystems")
    if not editor.new_level(PACKAGE,is_partitioned_world=True):
        raise RuntimeError("Cannot create independent World Partition preview level")
    world=unreal.EditorLevelLibrary.get_editor_world()
    if not world or world.get_outermost().get_name()!=PACKAGE:
        raise RuntimeError("Unexpected current map, refusing terrain creation")
    landscape=native.create_named_world_landscape(ID)
    if not landscape:
        raise RuntimeError("Unreal native Landscape import failed")
    verified=native.inspect_named_world_preview_components(landscape,ID)
    if verified!=count:
        raise RuntimeError("Native Landscape verification failed: "+str(verified))
    def spawn(cls,label,position,rotation=None):
        pos=unreal.Vector(*position)
        obj=actors.spawn_actor_from_class(cls,pos,rotation) if rotation else actors.spawn_actor_from_class(cls,pos)
        if not obj:
            raise RuntimeError("Native actor spawn failed: "+label)
        obj.set_actor_label("PRIGIMALIA_"+ID+"_Preview_"+label)
        return obj
    # Find a dry smooth spawn from the native procedural function.
    dry=None
    for radius in (0,500,1400,2600,4400):
        for angle in range(0,360,30):
            e=radius*math.cos(math.radians(angle))
            n=radius*math.sin(math.radians(angle))
            z=native.named_world_height(ID,e,n)
            edges=[native.named_world_height(ID,e+dx,n+dy) for dx,dy in ((-4,-4),(-4,4),(4,-4),(4,4))]
            if 5<z<1000 and max(abs(zz-z) for zz in edges)<8:
                dry=(e,n,z)
                break
        if dry:
            break
    if dry:
        spawn(unreal.PlayerStart,"PlayerStart",(dry[0]*100,-dry[1]*100,dry[2]*100+200))
    else:
        REPORT["spawnPlacement"]="NONE_SAFE_SPAWN_FOUND"
    spawn(unreal.DirectionalLight,"Sun",(0,0,100000),unreal.Rotator(-48,-22,0))
    spawn(unreal.SkyLight,"SkyLight",(0,0,10000))
    spawn(unreal.SkyAtmosphere,"Atmosphere",(0,0,0))
    if not editor.save_all_dirty_levels():
        raise RuntimeError("UE world level save failed")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("UE World Partition external actors save failed")
    if not UMAP.is_file() or UMAP.stat().st_size<1024:
        raise RuntimeError("No real .umap binary written")
    for p in PROTECTED:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=protectedBefore[str(p)]:
            raise RuntimeError("Protected map hash changed: "+str(p))
    REPORT.update(state="PROCEDURAL_TERRAIN_PREVIEW_SAVED_NOT_PLAYTESTED",
                  generatedInUnreal=True,landscapeComponents=verified,
                  resolution=samples,sideMetres=side,playerStartMetres=dry,
                  umapBytes=UMAP.stat().st_size,originalMapHashesUnchanged=True)

try:
    run()
except Exception as exc:
    REPORT["error"]=str(exc)
    REPORT["traceback"]=traceback.format_exc()
    raise
finally:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite existing preview report")
    OUTPUT.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("PRIGIMALIA_PREVIEW_REPORT="+str(OUTPUT))
