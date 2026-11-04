"""UE5.8 safe inspection of the copied City Sample map inside the SKARVIK staging project.
No levels, assets, or original D: files are modified or saved.
"""
import json
import os
import traceback
from pathlib import Path
import unreal

root=Path(unreal.Paths.project_dir()).resolve()
report=Path(os.environ.get("SKARVIK_CITY_AUDIT_REPORT",str(root/"Saved/SkarvikCity/city-asset-audit.json")))
data={"status":"FAILED","sourceCityInUnreal":False,"worldAssetLoadable":False,
      "levelInstanceClassAvailable":False,"levelInstanceCanReferenceWorld":False,
      "fullCityIntegratedIntoSkarvik":False,"sm5Playtested":False,
      "productionDModified":False}
try:
    marker=root/".skarvik-ci-stage-marker"
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(root).upper() or not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Untrusted project or stage marker")
    pkg="/Game/Map/Big_City_LVL"
    terrain="/Game/Maps/PRIGIMALIA_SKARVIK_CITY_v1"
    if not unreal.EditorAssetLibrary.does_asset_exist(pkg):
        raise RuntimeError("City Sample native UWorld is not registered in Unreal content")
    if not unreal.EditorAssetLibrary.does_asset_exist(terrain):
        raise RuntimeError("SKARVIK World Partition terrain map not registered")
    data["sourceCityInUnreal"]=True
    data["nativeWorldPath"]=pkg
    data["existingSkarvikPath"]=terrain
    world=unreal.load_asset(pkg)
    data["worldAssetType"]=str(world.get_class().get_name()) if world else None
    if not world:
        raise RuntimeError("Unreal cannot load CitySample world UWorld from copied package")
    data["worldAssetLoadable"]=True
    cls=getattr(unreal,"LevelInstance",None)
    data["levelInstanceClassAvailable"]=bool(cls)
    data["levelInstanceCanReferenceWorld"]=bool(cls and hasattr(cls,"set_world_asset"))
    data["cityContentFoldersPresent"]={
        name:(root/"Content"/name).is_dir()
        for name in ("__ExternalActors__","Building","City","Map","Material","Road","Prop","Megascans","Crowd","Vehicle")}
    if not cls:
        raise RuntimeError("Python LevelInstance actor class unavailable in UE5 build")
    if not hasattr(cls,"set_world_asset"):
        raise RuntimeError("UE5 LevelInstance cannot reference the copied native world")
    data["status"]="BIG_CITY_UWORLD_LOADABLE_LEVEL_INSTANCE_API_AVAILABLE_NOT_INTEGRATED"
    unreal.log("SKARVIK_CITY_NATIVE_ASSET_PREFLIGHT_OK=true")
except Exception as e:
    data["error"]=str(e)
    data["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_CITY_NATIVE_ASSET_PREFLIGHT_ERROR="+str(e))
finally:
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    unreal.log("SKARVIK_CITY_AUDIT_REPORT="+str(report))
