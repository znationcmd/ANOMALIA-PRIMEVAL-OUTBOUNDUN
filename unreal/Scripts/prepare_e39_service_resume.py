import json,os,traceback
from pathlib import Path
import unreal
out=Path(os.environ["E39_RESUME_DIR"])
report={"state":"FAILED","originalMapModified":False,"installedProjectModified":False}
try:
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not editor.load_level("/Game/Maps/ANOMALIA_E39DriveReview_v1"):
        raise RuntimeError("Existing v7 proving map could not load")
    cars=unreal.GameplayStatics.get_all_actors_of_class(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),unreal.AnomaliaChaosRoadVehicle)
    if len(cars)!=1:raise RuntimeError("Expected unique actual E39")
    car=cars[0]
    if not car.has_valid_road_rig():raise RuntimeError("Actual E39 rig rejected")
    car.get_editor_property("survival_systems").set_editor_property("enabled",True)
    car.get_editor_property("survival_systems").set_editor_property("battery_access_panel",unreal.Name("trunk"))
    manifest=json.loads((Path(unreal.Paths.project_dir())/"SourceAssets/BMWE39Review_v7/manifest.json").read_text(encoding="utf-8-sig"))
    for m in manifest["models"]:
        mesh=unreal.load_asset(m["objectPath"])
        if not mesh or unreal.EditorAssetLibrary.get_metadata_tag(mesh,"AnomaliaNativeSedanSha256")!=m["sha256"]:
            raise RuntimeError("v7 mesh metadata identity rejected "+m["id"])
    package="/Game/Anomalia/CharacterTests/E39Resume_"+os.environ["GITHUB_RUN_ID"]+"/ANOMALIA_E39DriveReview_v1"
    if unreal.EditorAssetLibrary.does_asset_exist(package):raise RuntimeError("Existing test map preserved")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,package):raise RuntimeError("New E39 isolated test map save failed")
    report.update(state="UNCHANGED_E39_NEW_SERVICE_TEST_MAP_SAVED",map=package,source=manifest["source"],modelCount=len(manifest["models"]))
except Exception as exc:
    report["error"]=str(exc);report["traceback"]=traceback.format_exc()
finally:
    (out/"prepare-report.json").write_text(json.dumps(report,indent=2)+"\n")
