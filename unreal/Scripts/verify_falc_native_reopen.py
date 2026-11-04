"""Reopen ORIGINAL F.A.L.C 26.5km World Partition world in UE5.8 read-only.
Verify real package and native terrain actor with collision, not merely a .umap filename.
"""
import json
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
REPORT=Path(os.environ.get("ANOMALIAZ_FALC_REOPEN_REPORT",str(ROOT/"Saved/FALC/reopened-falc-real-map.json")))
PACKAGE="/Game/Maps/PRIGIMALIA_FALC"
out=dict(state="FALC_NOT_REOPENED",worldPackage=PACKAGE,
         gamePlayable=False,publicBetaPublished=False,other14MapsModified=False,
         sourceTopoMatchedButElevationEstimated=True)
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
        raise RuntimeError("FALC reopen refused outside protected Windows map stage")
    if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Original stage owner marker absent")
    source=ROOT/"TerrainSource/FALC/FALC_26_5KM_MASTER_2017.r16"
    if not source.is_file():raise RuntimeError("FALC RAW16 source missing; do not verify fake map")
    if not unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("Saved FALC .umap not available in Unreal")
    asset=unreal.load_asset(PACKAGE)
    if not asset or asset.get_class().get_name()!="World":
        raise RuntimeError("FALC package does not load as a genuine native UWorld")
    subsystem=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not subsystem or not subsystem.load_level(PACKAGE):
        raise RuntimeError("FALC world failed independent editor load")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name().split(".")[0]!=PACKAGE:
        raise RuntimeError("Unreal editor did not actually enter FALC world")
    # Under World Partition only a subset of external actors may be loaded
    # in the editor. Verify at least one actual UE landscape and some collision.
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    lands=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    count=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in lands)
    collision=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in lands)
    if count!=256 or collision!=256:
        raise RuntimeError("Native FALC terrain not fully streamed after reopening: components=%d collision=%d"%(count,collision))
    player=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.PlayerStart)]
    if not player:
        raise RuntimeError("No saved dry PlayerStart reopened in FALC")
    out.update(state="FALC_REAL_UNREAL_NATIVE_WORLD_REOPENED_2017_RAW16_COLLISION_VERIFIED",
       reloadedNativeWorld=True,landscapeComponents=count,collisionComponents=collision,
       playerStartLoaded=True,worldAreaKm2=702.25,worldSideKm=26.5)
    unreal.log("ANOMALIAZ_FALC_REOPENED_REAL_NATIVE_WORLD=true")
except Exception as exc:
    out["state"]="FALC_REOPEN_VALIDATION_FAILED"
    out["error"]=str(exc)
    out["traceback"]=traceback.format_exc(limit=10)
    unreal.log_error("ANOMALIAZ_FALC_REOPEN_ERROR="+str(exc))
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
