"""Native read-only Big City LevelInstance World Partition runtime mode audit.
Official UE5.8 supports Partitioned/LevelStreaming and spatially loaded actors.
Check actual saved source reference, runtime behavior and data layer settings
before modifying or trying to stream 86,606 heavy City Sample actors.
"""
from pathlib import Path
import os,json,traceback,hashlib
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_BIGCITY_RUNTIME_AUDIT_REPORT"])
MAIN="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
LABEL="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
FILES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
       ROOT/"Content/Map/Big_City_LVL.umap",
       Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
report={"state":"FAILED","readOnly":True,"allSourceCityActorCellsLoaded":False,
        "fullCityRenderedInSM5":False,"originalDModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Stage marker invalid")
 if not all(p.is_file() for p in FILES):raise RuntimeError("One or more protected map packages missing")
 hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAIN):
  raise RuntimeError("Cannot reopen real 48km graded stage")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=[d for d in wp.get_actor_descs() or [] if str(d.label)==LABEL]
 if len(desc)!=1:raise RuntimeError("Big City actor not persisted or duplicated")
 if desc[0].native_class.get_name()!="LevelInstance":
  raise RuntimeError("Saved Big City actor has wrong native C++ class")
 wp.load_actors([desc[0].guid])
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 inst=next((a for a in actors if a.get_actor_label()==LABEL),None)
 if not inst:raise RuntimeError("Native LevelInstance was not selectively loaded")
 world=inst.get_world_asset()
 if not world or not world.get_path_name().startswith("/Game/Map/Big_City_LVL"):
  raise RuntimeError("Native Big City source UWorld pointer missing")
 report["runtimeWorldSourcePath"]=world.get_path_name()
 report["nativeActorType"]=inst.get_class().get_name()
 report["sourceLevelIsCurrentlyLoaded"]=bool(inst.is_loaded())
 for name in ("desired_runtime_behavior","is_spatially_loaded","is_editor_only_actor","is_main_world_only",
              "hlod_layer","runtime_grid"):
  try:report["editorProperty_"+name]=str(inst.get_editor_property(name))
  except Exception as err:report["editorProperty_"+name+"_error"]=str(err)[:240]
 for method in ("set_desired_runtime_behavior","get_desired_runtime_behavior","get_level_instance_id",
                "supports_partial_editor_loading","get_world_asset","load_level_instance"):
  report["pythonMethodAvailable_"+method]=bool(hasattr(inst,method))
 report["RuntimeBehaviorEnumChoices"]=str(getattr(unreal,"LevelInstanceRuntimeBehavior",None))
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[str(p)]:
   raise RuntimeError("Read-only City Sample runtime behavior survey modified a protected map")
 report["state"]="BIG_CITY_REAL_LEVELINSTANCE_RUNTIME_MODE_AND_STREAMING_GATES_AUDITED_READONLY"
 unreal.log("SKARVIK_BIG_CITY_NATIVE_RUNTIME_BEHAVIOR_AUDITED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_BIGCITY_RUNTIME_MODE_DIAGNOSTIC_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
