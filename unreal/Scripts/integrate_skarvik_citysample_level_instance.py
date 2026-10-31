"""Integrate a *native* City Sample World level instance into isolated SKARVIK 48km.

Run only in C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal. Requires
successful read-only Big City UWorld load and editor LevelInstance API.
This is NOT a complete SM5 visual or playability test, and no Crowd/Vehicle
classes or assets are supplied. A Level Instance may still reference them.
"""
import json
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MARKER=ROOT/".skarvik-ci-stage-marker"
REPORT=Path(os.environ.get("SKARVIK_CITY_INTEGRATION_REPORT",str(ROOT/"Saved/SkarvikCity/city-instance.json")))
CITY="/Game/Map/Big_City_LVL"
SKARVIK="/Game/Maps/PRIGIMALIA_SKARVIK_CITY_v1"
LABEL="ANOMALIA_SKARVIK_CITY_SAMPLE_BIG_CITY_STAGED"
report={"state":"BLOCKED","cityWorldInstanceSaved":False,
        "cityStaticActorsConfirmed":False,"nativeSM5PIETested":False,
        "gamePackaged":False,"trafficDisabledValidated":False,
        "crowdDisabledValidated":False,"originalDModified":False}
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
        raise RuntimeError("Wrong isolated UE5 stage")
    if not MARKER.is_file() or MARKER.read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Missing isolated stage marker")
    if not (ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap").is_file():
        raise RuntimeError("48km SKARVIK native map missing")
    if not (ROOT/"Content/Map/Big_City_LVL.umap").is_file():
        raise RuntimeError("Big City map package missing")
    for name in ("Crowd","Vehicle"):
        if (ROOT/"Content"/name).exists():
            raise RuntimeError("Crowd/Vehicle folder already present, refuse unexpected change")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels or not actors:
        raise RuntimeError("Level/Actor editor subsystems unavailable")
    city=unreal.load_asset(CITY)
    if not city or city.get_class().get_name() != "World":
        raise RuntimeError("Copied City Sample world asset did not load")
    clazz=getattr(unreal,"LevelInstance",None)
    if not clazz:
        raise RuntimeError("This editor has no LevelInstance class")
    if not levels.load_level(SKARVIK):
        raise RuntimeError("Failed to open isolated 48km SKARVIK map")
    current=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not current or current.get_path_name().split(".")[0]!=SKARVIK:
        raise RuntimeError("Editor world does not match SKARVIK (refuse writing another map)")
    original=[a for a in actors.get_all_level_actors() if a.get_actor_label()==LABEL]
    if original:
        raise RuntimeError("An instance with this label exists; no double import")
    loc=unreal.Vector(200000.0,800000.0,10000.0)  # east +2km, north -8km, terrain elevation 100m
    inst=actors.spawn_actor_from_class(clazz,loc)
    if not inst:
        raise RuntimeError("Unable to spawn LevelInstance on isolated SKARVIK")
    inst.set_actor_label(LABEL)
    if not inst.set_world_asset(city):
        raise RuntimeError("LevelInstance refused City Sample world reference")
    inst.load_level_instance()
    if not inst.is_loaded():
        raise RuntimeError("City Sample LevelInstance did not load in editor; no save")
    loaded=inst.get_loaded_level()
    if not loaded:
        raise RuntimeError("LevelInstance has no loaded level after load")
    # The real city is in its own partitioned subworld. Loading a Level Instance
    # does NOT prove all 96k external actors, meshes or materials are valid.
    report["levelInstanceLabel"]=LABEL
    report["nativeCityPackage"]=CITY
    report["nativeSkarvikPackage"]=SKARVIK
    report["cityCenterCm"]=[200000,800000,10000]
    report["worldInstanceCurrentlyLoaded"]=True
    # Refuse to resave all CitySample dependency packages; save isolated new SKARVIK only.
    if not levels.save_all_dirty_levels():
        raise RuntimeError("Failed saving isolated SKARVIK map")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Failed saving isolated world actor packages")
    report["state"]="CITY_LEVEL_INSTANCE_LINKED_IN_48KM_SKARVIK_NOT_VISUALLY_VALIDATED"
    report["cityWorldInstanceSaved"]=True
    unreal.log("SKARVIK_CITY_LEVEL_INSTANCE_LINKED=true")
except Exception as exc:
    report["error"]=str(exc)
    report["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_CITY_LEVEL_INSTANCE_FAILED="+str(exc))
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    unreal.log("SKARVIK_CITY_INTEGRATION_REPORT="+str(REPORT))
