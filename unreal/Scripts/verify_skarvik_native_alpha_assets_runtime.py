"""Read-only Unreal Engine 5.8 native alpha readiness checks.

Verify the TRUE existing SKARVIK map, local playable runtime module and real,
locally licensed Manny, German Shepherd animations and BMW E39 assets.
Do not edit any map, original D: file, derived data source or asset.
"""
import os, json, traceback
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = Path(os.environ["ANOMALIA_SKARVIK_ALPHA_ASSET_REPORT"])
PACKAGES = {
    "final_7_island_world": "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1",
    "visible_player_manny": "/Game/ControlRig/Characters/Mannequins/Meshes/SKM_Manny",
    "dog_german_shepherd": "/Game/German_Shepherd_3D_Model/Models/SK_GermanShepherd_01",
    "dog_idle": "/Game/German_Shepherd_3D_Model/Animations/A_type1_Idle_Playing_v01",
    "dog_walk": "/Game/German_Shepherd_3D_Model/Animations/A_type1_Walk_Loop_v01",
    "dog_run": "/Game/German_Shepherd_3D_Model/Animations/A_type1_Run_Loop_v01",
    "real_bmw_e39": "/Game/Anomalia/NamedVehicles1/bmw_e39/SM_bmw_e39",
}
status = {
    "state": "NATIVE_ALPHA_REAL_ASSETS_NOT_YET_VERIFIED",
    "sourceDir": str(ROOT),
    "realMapNotRegenerated": True,
    "originalDModified": False,
    "nativeWin64GamePackaged": False,
    "realMenuRenderedInGame": False,
    "dogFollowingInGame": False,
    "carDrivingInGame": False,
    "evidence": {},
}
try:
    if ROOT.name != "ANOMALIAZ_SKARVIK_NATIVE_ALPHA_CANDIDATE":
        raise RuntimeError("Refusing to audit anything but isolated genuine candidate")
    stage = Path("C:/ANOMALIAZ_SKARVIK_STAGE_41188816555/unreal")
    if (stage / ".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip() != "41188816555":
        raise RuntimeError("Trusted 7-island original stage not validated")
    for key, package in PACKAGES.items():
        exists = bool(unreal.EditorAssetLibrary.does_asset_exist(package))
        asset = unreal.load_asset(package) if exists else None
        status["evidence"][key] = {
            "package": package,
            "savedPackageRegistered": exists,
            "loaded": bool(asset),
            "class": asset.get_class().get_name() if asset else None,
        }
    expected = {
        "final_7_island_world": "World",
        "visible_player_manny": "SkeletalMesh",
        "dog_german_shepherd": "SkeletalMesh",
        "dog_idle": "AnimSequence",
        "dog_walk": "AnimSequence",
        "dog_run": "AnimSequence",
        "real_bmw_e39": "StaticMesh",
    }
    invalid = [
        key for key, cls in expected.items()
        if status["evidence"][key]["class"] != cls
    ]
    if invalid:
        raise RuntimeError("Authentic native alpha assets missing/incorrect: " + ",".join(invalid))
    status["state"] = "GENUINE_SKARVIK_AND_ALL_PLAYER_DOG_CAR_ASSETS_LOADED_IN_REAL_UNREAL_EDITOR"
    unreal.log("SKARVIK_NATIVE_ALPHA_ALL_7_REAL_ASSETS_LOADED=true")
except Exception as exc:
    status["error"] = str(exc)
    status["traceback"] = traceback.format_exc(limit=8)
    unreal.log_error("SKARVIK_NATIVE_ALPHA_ASSET_GATE_FAILED=" + str(exc))
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
