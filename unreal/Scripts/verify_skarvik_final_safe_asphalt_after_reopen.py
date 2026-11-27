"""Independent read-only native World Partition reopening gate for final SKARVIK.

Verify the *saved* road actors against the successful previous migration receipt,
not the planned 6,212. Confirm 906 original mainland houses, 128 island houses
and 720 genuine City Sample components coexist in the SAME final 48km world.

This does not certify route continuity, SM5 rendering, driving or interiors.
"""
import hashlib
import json
import math
import os
import traceback
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
WORLD = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
RECEIPT = Path(os.environ["SKARVIK_FINAL_SAFE_ASPHALT_RECEIPT"])
OUTPUT = Path(os.environ["SKARVIK_FINAL_INDEPENDENT_REOPEN_REPORT"])
FILES = (
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
    ROOT / "Content/Map/Big_City_LVL.umap",
    Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
)
PREFIXES = {
    "dryOriginalRoads": "SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",
    "originalMainlandBuildings": "SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",
    "originalIslandBuildings": "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",
    "citySampleBuildings": "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",
}
report = {
    "state": "FAILED",
    "readOnly": True,
    "finalWorld": WORLD,
    "verifiedInUnreal": False,
    "roadNetworkConnected": False,
    "allRegionalRoadsFinished": False,
    "playerDrivingSM5Tested": False,
    "completeCitySampleLoaded": False,
    "originalSourceFilesModified": False,
}
try:
    marker = ROOT / ".skarvik-ci-stage-marker"
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
        raise RuntimeError("Untrusted Unreal staging root")
    if not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip() != "41188816555":
        raise RuntimeError("Untrusted Unreal staging marker")
    if not all(p.is_file() for p in FILES):
        raise RuntimeError("A protected native map is missing")
    if not RECEIPT.is_file():
        raise RuntimeError("Previous native safe-asphalt migration receipt missing")
    previous = json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
    if previous.get("state") != "FINAL_SEVEN_ISLAND_NATIVE_ASPHALT_SAFE_SUBSET_SAVED_NOT_YET_CONTINUOUS_OR_DRIVEN":
        raise RuntimeError("Road migration receipt does not prove a saved world")
    if previous.get("sourceMapsUnchanged") is not True:
        raise RuntimeError("Previous receipt did not verify original map hashes")
    expected_road_count = int(previous["nativeDryAsphaltSaved"])
    if not 5000 <= expected_road_count <= 6212:
        raise RuntimeError("Implausible accepted real-asphalt actor count")
    if (expected_road_count + int(previous["additionalUnsafeRejectedCount"])) != 6212:
        raise RuntimeError("Accepted/rejected audited road total inconsistent")
    original_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(WORLD):
        raise RuntimeError("Native FINAL_v1 world failed independent reload")
    wp = unreal.WorldPartitionBlueprintLibrary
    descs = wp.get_actor_descs() or []
    grouped = {key: [] for key in PREFIXES}
    for desc in descs:
        label = str(desc.label)
        for group, prefix in PREFIXES.items():
            if label.startswith(prefix):
                grouped[group].append(desc)
                break
    counts = {key: len(value) for key, value in grouped.items()}
    report["savedActorDescriptors"] = counts
    expected_counts = {
        "dryOriginalRoads": expected_road_count,
        "originalMainlandBuildings": 906,
        "originalIslandBuildings": 128,
        "citySampleBuildings": 720,
    }
    if counts != expected_counts:
        raise RuntimeError("Saved World Partition actor counts mismatch: " + str(counts))
    labels = [str(d.label) for rows in grouped.values() for d in rows]
    if len(set(labels)) != len(labels):
        raise RuntimeError("Duplicate final-world actor labels")
    roads = sorted(grouped["dryOriginalRoads"], key=lambda d: str(d.label))
    # Sample broadly across the stored road actor set, not just the first 24.
    sample_indices = sorted({int(i * (len(roads) - 1) / 23) for i in range(24)})
    samples = [roads[i] for i in sample_indices]
    wp.load_actors([d.guid for d in samples])
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    loaded = {a.get_actor_label(): a for a in actor_sub.get_all_level_actors()}
    height = unreal.AnomaliaZPrigimaliaWorldImportLibrary.skarvik_final_coastal_height
    verified = []
    for d in samples:
        name = str(d.label)
        actor = loaded.get(name)
        if not actor or not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError("Persisted road actor could not actually be loaded: " + name)
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh = comp.get_editor_property("static_mesh") if comp else None
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError("Real road actor has no StaticMesh reference: " + name)
        position = actor.get_actor_location()
        east, north = float(position.x) / 100.0, -float(position.y) / 100.0
        land = float(height(east, north))
        if not math.isfinite(land) or land < 4.0:
            raise RuntimeError("Sampled reused road has invalid/underwater native terrain: " + name)
        verified.append({
            "label": name,
            "meshAsset": mesh.get_path_name(),
            "nativeLandHeightM": round(land, 2),
            "actorCenterXYMetres": [round(east, 2), round(north, 2)],
        })
    wp.unload_actors([d.guid for d in samples])
    for p in FILES:
        if hashlib.sha256(p.read_bytes()).hexdigest() != original_hashes[str(p)]:
            report["originalSourceFilesModified"] = True
            raise RuntimeError("Read-only native reopen unexpectedly changed map: " + str(p))
    report.update({
        "state": "FINAL_SKARVIK_ORIGINAL_BUILDINGS_CITY_AND_SAFE_ASPHALT_PERSIST_AFTER_NATIVE_REOPEN_NOT_PLAYTESTED",
        "verifiedInUnreal": True,
        "acceptedRoadActors": expected_road_count,
        "nativeDryAsphaltMetresInPriorReceipt": float(previous["nativeDryAsphaltMetresSaved"]),
        "rejectedRoadActorsInitial": int(previous["unmigratedUnsafeOriginalActorCount"]),
        "rejectedRoadActorsAdditional": int(previous["additionalUnsafeRejectedCount"]),
        "independentlyReloadedRoadMeshSamples": verified,
        "readOnlySourceHashesVerified": True,
    })
    unreal.log("SKARVIK_FINAL_REAL_DRY_ASPHALT_NATIVE_REOPEN_VERIFIED=" + str(expected_road_count))
except Exception as exc:
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
    unreal.log_error("SKARVIK_FINAL_DRY_ASPHALT_NATIVE_REOPEN_FAILED=" + str(exc))
finally:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
