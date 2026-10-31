"""Read-only targeted verification of persisted native City Sample UWorld reference.
Loads only one SKARVIK World Partition LevelInstance actor descriptor GUID.
No explicit load_level_instance(): CitySample's 86,606 actor cells stay unmanaged.
Never saves map, copies CitySample actors, enables traffic or edits original D:.
"""
import hashlib,json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
SOURCE="/Game/Map/Big_City_LVL"
LABEL="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
OUT=Path(os.environ["SKARVIK_NATIVE_CITY_POINTER_REPORT"])
report={"state":"FAILED","readOnly":True,
        "FullCityVisualStreamingVerified":False,"AllSourceCityActorsCopied":False,
        "SM5LevelGameTested":False,"CitySourceModified":False,
        "ProductionDModified":False,"NativeLevelInstanceActorLoaded":False,
        "WorldAssetReferenceAfterReloadVerified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
   ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted staging project")
 for f in (TARGET,CITY,ORIGINAL):
  if not f.is_file():raise RuntimeError("Missing protected World Partition file "+str(f))
 prior={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (TARGET,CITY,ORIGINAL)}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Graded SKARVIK world failed to reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 descriptors=wp.get_actor_descs() or []
 found=[desc for desc in descriptors if str(desc.label)==LABEL]
 if len(found)!=1:raise RuntimeError("Big City level actor missing or duplicated")
 native_class=found[0].native_class
 name=native_class.get_name() if native_class else "NONE"
 report["actorDescNativeClass"]=name
 if "LevelInstance" not in name:raise RuntimeError("Not a native LevelInstance: "+name)
 current=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 actor=next((a for a in current if a.get_actor_label()==LABEL),None)
 if actor is None:
  # Selection only: avoid loading the city map or all 86k nested source actors.
  wp.load_actors([found[0].guid])
  current=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
  actor=next((a for a in current if a.get_actor_label()==LABEL),None)
 if actor is None:raise RuntimeError("Specific city LevelInstance actor cannot be selectively loaded")
 report["NativeLevelInstanceActorLoaded"]=True
 report["actorUClass"]=actor.get_class().get_name()
 if "LevelInstance" not in report["actorUClass"]:
  raise RuntimeError("Selective loaded actor is not LevelInstance")
 pointer=actor.get_world_asset()
 report["actorWorldAssetPath"]=pointer.get_path_name() if pointer else None
 if not pointer or pointer.get_path_name().split(".")[0]!=SOURCE:
  raise RuntimeError("CitySample original native World asset pointer not persisted after re-open")
 report["WorldAssetReferenceAfterReloadVerified"]=True
 report["IsBigCityNestedLevelActuallyLoaded"]=bool(actor.is_loaded())
 # This is NOT a full city visual / 86k actor cell integration claim.
 for f in (TARGET,CITY,ORIGINAL):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=prior[str(f)]:
   raise RuntimeError("Read-only targeted actor lookup unexpectedly changed protected source")
 report["state"]="BIG_CITY_NATIVE_LEVELINSTANCE_UWORLD_POINTER_PERSISTED_NOT_VISUALLY_STREAMED"
 unreal.log("SKARVIK_BIG_CITY_NATIVE_LEVELINSTANCE_WORLD_POINTER_PERSISTED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_BIG_CITY_POINTER_READONLY_VERIFICATION_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
