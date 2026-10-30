"""Unreal Editor 5.8: create an EMPTY 48km draft WORLD PARTITION map safely.

Requires verified draft tiles from generate-playtest-terrain.py first.
The Landscape must still be imported using Landscape Mode in the Unreal Editor.
This script never overwrites an existing .umap and does not claim playable status.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import traceback

import unreal

PROJECT = Path(unreal.Paths.project_dir())
TILES = PROJECT / "TerrainPreview"
TILES_MANIFEST = TILES / "draft-terrain-manifest.json"
MAP_NAME = "ANOMALIA_TerrainDraft"
PACKAGE = f"/Game/Maps/{MAP_NAME}"
MAP = PROJECT / "Content" / "Maps" / f"{MAP_NAME}.umap"
REPORT = PROJECT / "Saved" / "AnomaliaZPrigimaliaMigration" / "draft-level-report.json"


def write_report(status: str, **extra):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    obj = {
        "status": status,
        "mapPackage": PACKAGE,
        "mapFile": str(MAP),
        "tileDirectory": str(TILES),
        "worldPartitionRequested": True,
        "landscapeImported": False,
        "playable": False,
        "testedInEditor": False,
        **extra,
    }
    REPORT.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    unreal.log("ANOMALIA terrain draft: " + json.dumps(obj, ensure_ascii=False))


def validate_sources():
    if not TILES_MANIFEST.is_file():
        raise RuntimeError("Missing verified TerrainPreview manifest; run generate-playtest-terrain.py first")
    data = json.loads(TILES_MANIFEST.read_text(encoding="utf-8"))
    if (data.get("status") != "terrain_sources_verified_not_imported"
            or data.get("tiles") != [12, 12]
            or data.get("heightmapResolution") != [253, 253]
            or data.get("tilesVerified") != 144
            or data.get("seamsVerified") != 264):
        raise RuntimeError("TerrainPreview verification manifest is invalid or incomplete")
    hashes = data.get("tileSHA256")
    if not isinstance(hashes, dict) or len(hashes) != 144:
        raise RuntimeError("Missing 144 terrain SHA256 checksums")
    expected_bytes = 253 * 253 * 2
    for y in range(12):
        for x in range(12):
            filename = TILES / f"ANOMALIA_x{x}_y{y}.r16"
            if not filename.is_file() or filename.stat().st_size != expected_bytes:
                raise RuntimeError(f"Missing or invalid terrain tile: {filename}")
            actual_hash = hashlib.sha256(filename.read_bytes()).hexdigest()
            if hashes.get(filename.name) != actual_hash:
                raise RuntimeError(f"Terrain tile checksum mismatch: {filename}")


def create():
    # Fail BEFORE new_level if sources are missing or malformed.
    validate_sources()
    if MAP.exists():
        write_report("already_exists_not_modified", bytes=MAP.stat().st_size)
        return
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not editor:
        raise RuntimeError("Unreal LevelEditorSubsystem unavailable")

    # The .umap binary is produced by Unreal Engine, never faked in GitHub.
    if not editor.new_level(PACKAGE, is_partitioned_world=True):
        raise RuntimeError("Unreal failed to create new World Partition level")

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not actors:
        raise RuntimeError("Unreal EditorActorSubsystem unavailable")
    sun = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 5000), unreal.Rotator(0, 0, 0))
    if not sun:
        raise RuntimeError("Unable to place daylight")
    sun.set_actor_label("ANOMALIA_DraftSun")
    sun.set_actor_rotation(unreal.Rotator(-50, -20, 0), False)
    # Do not place a player on sea floor before the Landscape is imported.
    if not editor.save_all_dirty_levels():
        raise RuntimeError("Unreal failed to save draft World Partition level")
    if not MAP.is_file() or MAP.stat().st_size < 1024:
        raise RuntimeError("No valid-size .umap emitted by Unreal")
    write_report("partitioned_shell_created_terrain_import_required", bytes=MAP.stat().st_size)


try:
    create()
except Exception as error:
    write_report("failed", error=str(error), traceback=traceback.format_exc())
    unreal.log_error("ANOMALIA: terrain draft bootstrap failed: " + str(error))
    raise
