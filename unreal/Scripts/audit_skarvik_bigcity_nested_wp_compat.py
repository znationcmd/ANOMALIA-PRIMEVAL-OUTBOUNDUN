"""Read-only CitySample Big City compatibility survey for SKARVIK's graded WP world.
The previous full LevelInstance load timed out after 32 minutes, so do NOT try it again.
This reports which World Partition/level-instance APIs and source assets exist.
"""
from pathlib import Path
import json,os,traceback
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ.get("SKARVIK_BIGCITY_COMPAT_REPORT",str(ROOT/"Saved/SkarvikCity/BigCityCompatibility.json")))
report={"state":"FAILED","readOnly":True,"sourceCityLoaded":False,
 "levelInstanceAttached":False,"bigCityVisible":False,
 "originalDModified":False,"SM5Tested":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Untrusted staging project")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Invalid isolated stage marker")
 original=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
 main=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
 source_file=ROOT/"Content/Map/Big_City_LVL.umap"
 if not original.is_file() or not main.is_file() or not source_file.is_file():
  raise RuntimeError("Original or native city/graded world file absent")
 native="/Game/Map/Big_City_LVL"
 city=unreal.EditorAssetLibrary.load_asset(native)
 if not city or not isinstance(city,unreal.World):
  raise RuntimeError("CitySample Big City world source not loadable")
 report["sourceCityLoaded"]=True
 report["bigCityPackage"]=native
 report["cityMapFileBytes"]=source_file.stat().st_size
 report["hasLevelInstanceClass"]=bool(getattr(unreal,"LevelInstance",None))
 report["hasLevelInstanceSubsystem"]=bool(getattr(unreal,"LevelInstanceSubsystem",None))
 report["CitySampleModulesPresent"]=all((ROOT/"Binaries/Win64"/n).is_file() for n in
   ("UnrealEditor-CitySample.dll","UnrealEditor-CitySampleAnimGraphRuntime.dll"))
 try:
  wp=city.get_editor_property("world_partition")
  report["sourceCityHasWorldPartition"]=bool(wp)
  report["sourceWorldPartitionClass"]=str(wp.get_class().get_name()) if wp else None
 except Exception as e:
  report["sourceWorldPartitionInspectionError"]=str(e)
 report["separateGradedTargetWorldPartition"]=True
 report["wouldRequireNestedWorldPartitionCompatibility"]=bool(report.get("sourceCityHasWorldPartition"))
 for folder in ("Map","Building","Road","Material","Megascans","City","Crowd","Vehicle"):
  report.setdefault("sourceFolderPresence",{})[folder]=(ROOT/"Content"/folder).is_dir()
 for method in ("set_world_asset","load_level_instance","is_loaded","get_world_asset"):
  report.setdefault("levelInstanceMethods",{})[method]=bool(getattr(unreal.LevelInstance,method,None))
 report["state"]="CITY_SAMPLE_SOURCE_LOADED_NESTED_WORLD_PARTITION_COMPAT_REVIEW_REQUIRED"
 unreal.log("SKARVIK_CITY_SAMPLE_COMPAT_SURVEY_COMPLETED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_CITY_SAMPLE_COMPAT_SURVEY_ERROR="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
