r"""Create a NEW 48x48km SKARVIK graded v2 World Partition level for houses.

The original SKARVIK v1 and protected D project are never saved/changed.
This is a new separate Unreal native landscape, not simply a JSON height curve.
"""
import json,os,traceback,hashlib
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
FILENAME=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
STAGE_V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
OUT=Path(os.environ.get("SKARVIK_GRADED_TERRAIN_REPORT",str(ROOT/"Saved/SkarvikCity/graded-v2-report.json")))
SPEC=Path(os.environ.get("SKARVIK_GRADED_LAYOUT_JSON",""))
state=dict(state="FAILED",newMap=PACKAGE,worldPartition=False,sideKm=48,
           mainV1Modified=False,originalDModified=False,citySampleImported=False,
           importedVehicles=False,importedCrowds=False,buildingsPlaced=False,
           packagedGameTested=False,nativeSM5GameTested=False)
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or ROOT.drive.upper()!="C:":
        raise RuntimeError("Must run in verified isolated C stage")
    if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Wrong protected stage marker")
    if not ORIGINAL.is_file() or not STAGE_V1.is_file():
        raise RuntimeError("Required originals (D source and C v1) are missing")
    if FILENAME.exists() or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("Graded v2 world already exists: never overwrite it")
    for forbidden in ("Crowd","Vehicle"):
        if (ROOT/"Content"/forbidden).exists():
            raise RuntimeError("Forbidden CitySample content: "+forbidden)
    if not SPEC.is_file():
        raise RuntimeError("125-site layout unavailable")
    layout=json.loads(SPEC.read_text(encoding="utf-8"))
    sites=layout["settlements"]
    if len(sites)!=125 or len(set(x["id"] for x in sites))!=125:
        raise RuntimeError("Invalid 125-site map specification")
    sha_d_before=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    sha_v1_before=hashlib.sha256(STAGE_V1.read_bytes()).hexdigest()
    lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(lib,"create_skarvik_graded_landscape") or not hasattr(lib,"skarvik_graded_height"):
        raise RuntimeError("New graded terrain native C++ module not compiled")
    new_height=lib.skarvik_graded_height
    old_height=lib.skarvik_city_height
    for site in sites:
        if site["id"]=="citysample":continue
        e=site["eastKm"]*1000.0;n=site["northKm"]*1000.0
        central=float(new_height(e,n))
        for dx in (-60.0,0.0,60.0):
            for dy in (-60.0,0.0,60.0):
                if abs(float(new_height(e+dx,n+dy))-central)>0.05:
                    raise RuntimeError("Village terrain not level: "+site["id"])
    if abs(float(new_height(2000,-8000))-float(old_height(2000,-8000)))>0.01:
        raise RuntimeError("Native Big City footprint elevation changed")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.new_level(PACKAGE,is_partitioned_world=True):
        raise RuntimeError("Cannot create new graded World Partition UE5 level")
    land=lib.create_skarvik_graded_landscape()
    if not land:raise RuntimeError("Native v2 landscape height import rejected")
    proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    count=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
    coll=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
    state["landscapeComponents"]=count;state["collisionComponents"]=coll
    if count!=576 or coll!=576:
        raise RuntimeError("Landscape/collision components mismatch: "+str((count,coll)))
    first=actors.spawn_actor_from_class(
        unreal.PlayerStart,unreal.Vector(200000,800000,(float(new_height(2000,-8000))+1.8)*100))
    if first:first.set_actor_label("SKARVIK_GRADED_V2_CITY_SAMPLE_PLAYER_START")
    if not levels.save_all_dirty_levels():
        raise RuntimeError("Could not save native graded World Partition map")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Could not save terrain actor packages")
    if not FILENAME.is_file() or FILENAME.stat().st_size<1024:
        raise RuntimeError("New graded .umap absent or invalid")
    if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()!=sha_d_before:
        raise RuntimeError("Protected original D map was modified")
    if hashlib.sha256(STAGE_V1.read_bytes()).hexdigest()!=sha_v1_before:
        raise RuntimeError("Protected original v1 SKARVIK C map was modified")
    state.update(state="SKARVIK_GRADED_V2_NATIVE_LANDSCAPE_SAVED_NOT_PLAYTESTED",
                 originalDModified=False,mainV1Modified=False,worldPartition=True,
                 citySampleFootprintKm=[4,4],extraBuildableSites=124,
                 newNativeMapBytes=FILENAME.stat().st_size)
    unreal.log("SKARVIK_GRADED_V2_124_NATIVE_BUILDABLE_PADS_SAVED=true")
except Exception as exc:
    state["error"]=str(exc)
    state["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_GRADED_V2_NATIVE_ERROR="+str(exc))
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(state,indent=2)+"\n",encoding="utf-8")
    unreal.log("SKARVIK_GRADED_V2_RESULT="+str(OUT))
