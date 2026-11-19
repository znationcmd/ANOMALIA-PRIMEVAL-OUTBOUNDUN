r"""Read-only after-reopen WP verification for automatic native roads and towns."""
import json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["ANOMALIA_AUTO30_NATIVE_RELOAD_REPORT"])
PKG=os.environ["ANOMALIA_AUTO30_WORLD_PACKAGE"]
IDENT=os.environ["ANOMALIA_AUTO30_MAP_ID"]
r={"state":"FAILED","package":PKG,"mapId":IDENT,"actualNativeRoadsPersisted":0,
    "actualNativeBuildingsPersisted":0,"sourceLevelChanged":False,"gameplayTested":False}
try:
    if ROOT!=Path(r"D:\ANOMALIA\unreal").resolve():
        raise RuntimeError("Original Unreal project not loaded")
    if not PKG.startswith("/Game/Maps/"):
        raise RuntimeError("Unexpected World Partition map")
    lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not lv.load_level(PKG):raise RuntimeError("Target world failed to reopen")
    existing=[a.get_actor_label() for a in actors.get_all_level_actors()]
    try:
        existing.extend(str(d.label) for d in (unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []))
        r["savedWorldPartitionDescriptionsScanned"]=True
    except Exception as ex:
        r["savedWorldPartitionDescriptionsScanned"]=False
        r["descriptionError"]=str(ex)
    labels=set(existing)
    prefix="ANOMALIA_AUTO30_V1_"+IDENT.replace("-","_")+"_"
    r["actualNativeRoadsPersisted"]=sum(v.startswith(prefix) and "_REAL_ROAD_" in v for v in labels)
    r["actualNativeBuildingsPersisted"]=sum(v.startswith(prefix) and "_BUILDING_" in v for v in labels)
    r["unrealLevelActorLabelsScanned"]=len(labels)
    if not r["actualNativeRoadsPersisted"] or not r["actualNativeBuildingsPersisted"]:
        raise RuntimeError("Native real asphalt and houses did not persist after level reload")
    r["state"]="REAL_PROCEDURAL_ROADS_AND_BUILDINGS_PERSISTED_NATIVE_WP_NOT_PLAYTESTED"
except Exception as ex:
    r["error"]=str(ex);r["traceback"]=traceback.format_exc()
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("ANOMALIA_AUTO30_RELOADED_VERIFIED "+json.dumps({k:v for k,v in r.items() if k!="traceback"},ensure_ascii=False))
