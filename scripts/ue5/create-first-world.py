"""ANOMALIA UE 5.8: create a NON-DESTRUCTIVE partitioned first-test map.

Run INSIDE Unreal Editor via -ExecutePythonScript (not ordinary Python).
Creates a small test platform, PlayerStart and daylight inside a real .umap.
This does NOT import the final 48 x 48 km terrain, coastlines, roads or cities.
Never overwrites an existing map or changes the user's default startup map.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import traceback

import unreal

MAP_NAME = "ANOMALIA_FirstTest"
MAP_PACKAGE = f"/Game/Maps/{MAP_NAME}"
PROJECT_DIR = Path(unreal.Paths.project_dir())
OUTPUT_MAP = PROJECT_DIR / "Content" / "Maps" / f"{MAP_NAME}.umap"
REPORT_PATH = Path(os.environ.get("ANOMALIA_WORLD_REPORT", "")) if os.environ.get("ANOMALIA_WORLD_REPORT") else PROJECT_DIR / "Saved" / "AnomaliaMigration" / "first-world-report.json"


def report(status: str, **fields) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "status": status,
        "mapPackage": MAP_PACKAGE,
        "mapFile": str(OUTPUT_MAP),
        "worldPartitionRequested": True,
        "fullTerrainImported": False,
        "gameCompiled": False,
        "playInEditorTested": False,
        "note": "A first-test map; NOT the finished ANOMALIA world",
        **fields,
    }
    REPORT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    unreal.log("ANOMALIA first-world: " + json.dumps(data, ensure_ascii=False))


def spawn(cls, name: str, pos: tuple[float, float, float]):
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(cls, unreal.Vector(*pos), unreal.Rotator(0, 0, 0))
    if not actor:
        raise RuntimeError("Unreal refused to spawn: " + name)
    actor.set_actor_label(name)
    return actor


def create() -> None:
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels:
        raise RuntimeError("LevelEditorSubsystem unavailable: run this in Unreal Editor 5.8")
    # The .umap is binary and must be authored BY Unreal, not by copying a stub from Git.
    # Fails closed if a file exists: no deletion, no overwrite, no silent merging.
    if OUTPUT_MAP.exists():
        if not OUTPUT_MAP.is_file() or OUTPUT_MAP.stat().st_size < 1024:
            raise RuntimeError("Existing map is invalid-size; preserved without modification")
        if not levels.load_level(MAP_PACKAGE):
            raise RuntimeError("Unreal could not open the existing map; preserved without modification")
        report("already_exists_not_modified")
        return

    if not levels.new_level(MAP_PACKAGE, is_partitioned_world=True):
        raise RuntimeError("Unreal failed to create the World Partition level")

    # 200 m square test pad; the final 48 x 48 km landscape is a separate task.
    floor_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    if not floor_mesh:
        raise RuntimeError("Engine basic Cube mesh unavailable")
    pad = spawn(unreal.StaticMeshActor, "ANOMALIA_TestPlatform_200m", (0.0, 0.0, -50.0))
    pad.static_mesh_component.set_static_mesh(floor_mesh)
    pad.set_actor_scale3d(unreal.Vector(200.0, 200.0, 1.0))
    spawn(unreal.PlayerStart, "ANOMALIA_InitialSpawn", (0.0, 0.0, 250.0))
    daylight = spawn(unreal.DirectionalLight, "ANOMALIA_Sun", (0.0, 0.0, 4000.0))
    daylight.set_actor_rotation(unreal.Rotator(-45.0, -25.0, 0.0), False)

    # Exercise actual native rest/harvest actors after the C++ module has compiled.
    # These remain explicit cube placeholders, not finished furniture or animated animals.
    station_class = unreal.load_class(None, "/Script/AnomaliaPrimeval.AnomaliaHomesteadStation")
    if not station_class:
        raise RuntimeError("Native homestead class unavailable: compile the C++ project first")
    station_kinds = unreal.AnomaliaHomesteadObject
    for enum_name, label, position in (
        ("BED", "Lit_test_cube_R_repos", (500.0, 0.0, 50.0)),
        ("TABLE", "Table_test_cube", (500.0, 300.0, 50.0)),
        ("CHAIR", "Chaise_test_cube", (500.0, 450.0, 50.0)),
        ("COW", "Vache_test_cube_E_lait", (900.0, 0.0, 50.0)),
        ("CHICKEN", "Poule_test_cube_E_oeufs", (900.0, 300.0, 50.0)),
        ("BEEHIVE", "Ruche_test_cube_E_miel", (900.0, 600.0, 50.0)),
    ):
        station = spawn(station_class, "ANOMALIA_" + label, position)
        station.set_editor_property("object_type", getattr(station_kinds, enum_name))

    if not levels.save_all_dirty_levels():
        raise RuntimeError("Unreal could not save the new level")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError("Unreal could not save World Partition external actor packages")

    if not OUTPUT_MAP.is_file() or OUTPUT_MAP.stat().st_size < 1024:
        raise RuntimeError("No valid-size .umap was produced by Unreal Editor")

    report("umap_created_needs_ue_play_test", bytes=OUTPUT_MAP.stat().st_size,
           nativeHomesteadTestActors=6, finalModelsIncluded=False)


try:
    create()
except Exception as exc:
    report("failed", error=str(exc), traceback=traceback.format_exc())
    unreal.log_error("ANOMALIA first-world creation failed: " + str(exc))
    raise
