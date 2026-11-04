"""Create a NEW 48x48 km SKARVIK City World Partition terrain only.

Does not import City Sample or place fake buildings. Does not overwrite the
original SKARVIK. City source content must be migrated and aligned separately,
only after available disk space and native shader/mesh tests pass.
Execute from UnrealEditor-Cmd -ExecutePythonScript in a staging checkout only.
"""
import json
import os
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
NEW_PACKAGE = "/Game/Maps/PRIGIMALIA_SKARVIK_CITY_v1"
OLD_MAP = Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
STAGE_MARKER = ROOT / ".skarvik-ci-stage-marker"
NEW_MAP = ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
REPORT = Path(os.environ.get(
    "PRIGIMALIA_SKARVIK_CITY_REPORT",
    str(ROOT / "Saved/SkarvikCity/preparation.json")))
MIN_DISK_GIB = 30
result = {
    "state": "BLOCKED",
    "package": NEW_PACKAGE,
    "sourceCitySampleRequired": True,
    "citySampleImported": False,
    "newTerrainAuthored": False,
    "otherMapsModified": False,
    "skarvikOriginalModified": False,
    "trafficDisabledInNativeCity": False,
    "crowdsDisabledInNativeCity": False,
    "nativeSM5Tested": False,
    "packagedGameTested": False,
}

try:
    # Require a run-specific CI marker; never author into any user project or an unverified checkout.
    expected_run = os.environ.get("PRIGIMALIA_SKARVIK_CI_RUN_ID", "")
    if not expected_run or not STAGE_MARKER.is_file() or STAGE_MARKER.read_text(encoding="utf-8").strip() != expected_run:
        raise RuntimeError("Refusing non-isolated or unmarked Unreal project")
    if "ANOMALIAZ_SKARVIK_STAGE" not in str(ROOT).upper() or not str(ROOT).upper().startswith("C:\\"):
        raise RuntimeError("Stage must be a dedicated C: ANOMALIAZ_SKARVIK_STAGE folder")
    if not OLD_MAP.is_file():
        raise RuntimeError("Original SKARVIK staged reference missing")
    if NEW_MAP.exists() or (ROOT/"Content/__ExternalActors__/Maps/PRIGIMALIA_SKARVIK_CITY_v1").exists():
        raise RuntimeError("A SKARVIK city level or its World Partition data already exists; refuse overwrite")
    if unreal.EditorAssetLibrary.does_asset_exist(NEW_PACKAGE):
        raise RuntimeError("SKARVIK city package is already registered; refuse overwrite")
    free_gib = shutil.disk_usage(ROOT).free / 1024**3
    result["diskAvailableGiB"] = round(free_gib, 2)
    if free_gib < MIN_DISK_GIB:
        raise RuntimeError(
            f"Insufficient temporary disk headroom ({free_gib:.1f} GiB < {MIN_DISK_GIB} GiB). "
            "City Sample requires substantially more space; do not attempt migration.")
    city = Path("D:/ANOMALIA/FabImports/CitySample")
    if not (city/"CitySample.uproject").is_file() or not (city/"Content/Map/Big_City_LVL.umap").is_file():
        raise RuntimeError("Full Big City source project missing")
    if not (city/"Content/__ExternalActors__").is_dir():
        raise RuntimeError("City Sample World Partition external actors missing")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels or not actors:
        raise RuntimeError("Editor subsystems unavailable")
    if not levels.new_level(NEW_PACKAGE, is_partitioned_world=True):
        raise RuntimeError("Failed creating new standalone World Partition map")
    height = unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(height, "create_skarvik_city_landscape"):
        raise RuntimeError("Native terrain module is not compiled in UE5")
    land = height.create_skarvik_city_landscape()
    if not land:
        raise RuntimeError("Native SKARVIK city 48 km landscape creation failed")
    proxies = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.LandscapeProxy)]
    count = sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
    collisions = sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
    if count != 576 or collisions != 576:
        raise RuntimeError(f"Landscape/collision mismatch: {count}/{collisions}")
    # City Sample placement planned around east +2km, north -8km.
    origin_z = height.skarvik_city_height(2000, -8000)
    if abs(origin_z-100) > 0.1:
        raise RuntimeError("The 4x4 km City Sample pad was not created")
    start = actors.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(200000, 800000, (origin_z+1.8)*100))
    if not start:
        raise RuntimeError("PlayerStart could not be created")
    start.set_actor_label("PRIGIMALIA_SKARVIK_CITY_TerrainOnly_PlayerStart")
    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,100000))
    if sun:
        sun.set_actor_label("PRIGIMALIA_SKARVIK_CITY_Sun")
        sun.set_actor_rotation(unreal.Rotator(-45, -25, 0), False)
    actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0,0,12000))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0,0,0))
    if not levels.save_all_dirty_levels():
        raise RuntimeError("Failed saving new .umap")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError("Failed saving World Partition actors")
    if not NEW_MAP.is_file() or NEW_MAP.stat().st_size < 1024:
        raise RuntimeError("Native .umap file missing or empty")
    result.update(
        state="NEW_48KM_TERRAIN_SAVED_CITY_NOT_IMPORTED",
        newTerrainAuthored=True, heightmapSamples=3025, sideMeters=48000,
        landscapeComponents=count, collisionComponents=collisions,
        worldPartition=True, citySampleAssetsRequired=True, playableCity=False,
        newMapBytes=NEW_MAP.stat().st_size)
except Exception as exc:
    result["error"] = str(exc)
    result["traceback"] = traceback.format_exc()
    raise
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    unreal.log("SKARVIK_CITY_AUTHORING_REPORT="+str(REPORT))
