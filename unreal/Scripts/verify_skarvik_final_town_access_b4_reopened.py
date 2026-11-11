"""Independent read-only persistence check for final SKARVIK town street access.

Only certifies saved World Partition actor descriptors + a spread of actual loaded
StaticMesh assets, native coast terrain and source-file hash stability.
Does not certify regional connectivity, the entire 992 streets or SM5 driving.
"""
import hashlib
import json
import math
import os
import traceback
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
TARGET = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
ROOT_MAP = ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCES = (
    ROOT_MAP,
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
    ROOT / "Content/Map/Big_City_LVL.umap",
    Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
)
PLAN = Path(os.environ["SKARVIK_FINAL_LOCAL_ROADS_B4_BUILD_REPORT"])
OUTPUT = Path(os.environ["SKARVIK_FINAL_LOCAL_ROADS_B4_REOPEN_REPORT"])
PREFIX = "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B4_"
report = {"state": "FAILED", "readOnly": True,
          "gameplayPassed": False, "realVehicleDrivingTested": False,
          "allRoadsConnected": False, "fullBigCityReady": False}
try:
    mark = ROOT / ".skarvik-ci-stage-marker"
    if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
            or not mark.is_file()
            or mark.read_text(encoding="utf-8-sig").strip() != "41188816555"):
        raise RuntimeError("Untrusted C stage")
    if any(not p.is_file() for p in SOURCES):
        raise RuntimeError("Protected native source missing")
    build = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    if build.get("state") != "FINAL_COAST_SAFE_NATIVE_TOWN_ACCESS_BATCH4_SAVED_NOT_FULLY_CONNECTED_OR_DRIVEN":
        raise RuntimeError("Previous local roads were not saved")
    if build.get("actorsCreated", 0) < 20 or build.get("accessLanesFullyBuilt", 0) < 1:
        raise RuntimeError("Previous road source report contains no substantial native actors")
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(TARGET):
        raise RuntimeError("Final World Partition map cannot be reopened")
    wp = unreal.WorldPartitionBlueprintLibrary
    desc = wp.get_actor_descs() or []
    labels = [str(x.label) for x in desc]
    local = [d for d in desc if str(d.label).startswith(PREFIX)]
    counts = {
        "newTownRoadActors": len(local),
        "previousSafeOldAsphalt": sum(x.startswith("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") for x in labels),
        "priorNativeTownRoadsB1": sum(x.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_") for x in labels),
        "priorNativeTownRoadsB2": sum(x.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_") for x in labels),
        "priorNativeTownRoadsB3": sum(x.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B3_") for x in labels),
        "mainlandOldBuildings": sum(x.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for x in labels),
        "islandOldBuildings": sum(x.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for x in labels),
        "genuineBigCityMeshes": sum(x.startswith("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_") for x in labels),
    }
    report["persistentActorCounts"] = counts
    if counts["newTownRoadActors"] != build["actorsCreated"]:
        raise RuntimeError("New real local asphalt actor descriptors disappeared or duplicated")
    if (counts["priorNativeTownRoadsB3"] != 1100 or counts["priorNativeTownRoadsB2"] != 1298 or counts["priorNativeTownRoadsB1"] != 1674
            or counts["previousSafeOldAsphalt"] != 6130 or
            counts["mainlandOldBuildings"] != 906 or
            counts["islandOldBuildings"] != 128 or
            counts["genuineBigCityMeshes"] != 720):
        raise RuntimeError("Original staged native geometry was lost or modified")
    if len(set(str(d.label) for d in local)) != len(local):
        raise RuntimeError("Duplicated road actor label")
    # A few physical assets must resolve after reopening unloaded WP cells.
    sample = sorted(local, key=lambda d: str(d.label))
    indices = sorted({int(i * (len(sample) - 1) / 11) for i in range(12)})
    chosen = [sample[i] for i in indices]
    wp.load_actors([d.guid for d in chosen])
    loaded = {a.get_actor_label(): a for a in
              unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    native_h = unreal.AnomaliaZPrigimaliaWorldImportLibrary.skarvik_final_coastal_height
    meshes = []
    for d in chosen:
        actor = loaded.get(str(d.label))
        if not actor or not isinstance(actor, unreal.StaticMeshActor):
            raise RuntimeError("Selected real street actor cannot reload")
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh = component.get_editor_property("static_mesh") if component else None
        if not isinstance(mesh, unreal.StaticMesh):
            raise RuntimeError("Selected native local asphalt missing StaticMesh asset")
        p = actor.get_actor_location()
        h = float(native_h(float(p.x) / 100., -float(p.y) / 100.))
        if not math.isfinite(h) or h < 5:
            raise RuntimeError("Road appears on sea after reopening")
        meshes.append({"actor": str(d.label), "realMesh": mesh.get_path_name()})
    wp.unload_actors([d.guid for d in chosen])
    for p in SOURCES:
        if hashlib.sha256(p.read_bytes()).hexdigest() != before[str(p)]:
            raise RuntimeError("Read-only audit changed a native World Partition source")
    report.update({
        "state": "FINAL_SKARVIK_NEW_REAL_LOCAL_ROADS_B4_PERSIST_IN_WORLD_PARTITION_NOT_DRIVEN",
        "originalFilesUnchanged": True,
        "newRoadSiteCount": build["sitesWithRealNewAsphalt"],
        "newRoadMetres": build["pavedMetres"],
        "loadedRealRoadMeshSamples": meshes,
    })
    unreal.log("SKARVIK_FINAL_REAL_LOCAL_ROADS_REOPENED=" + str(len(local)))
except Exception as exc:
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
    unreal.log_error("SKARVIK_FINAL_REAL_LOCAL_ROAD_REOPEN_FAILED=" + str(exc))
finally:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
