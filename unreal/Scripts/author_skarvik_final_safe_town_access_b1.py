"""Build a FIRST native on-land local-street access batch on final 48x48km SKARVIK.

The final coastline differs from GRADED_v2. Relocate planned local line coordinates
by the coastal manifest's source->target delta, preserve 67 provisional relocated
sites for manual approval, and reject unsafe terrain/building collisions. Every
accepted lane is completely preflighted before spawning any actor for that lane.
A saved street stub is NOT a connection to a regional paved road, not a vehicle
playtest and not evidence the whole 992-street plan is complete.

Only operate in isolated C: native staging; D: originals never modified.
"""
import hashlib
import json
import math
import os
import shutil
import traceback
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
TARGET_PKG = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
TARGET = ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCE_MAPS = (
    Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
    ROOT / "Content/Map/Big_City_LVL.umap",
)
BACKUP = ROOT / "Saved/SkarvikCity/FinalNativeCoastTownAccessBatch1_20261101/final-before-access-lanes.umap"
COAST = Path(os.environ["SKARVIK_FINAL_COAST_SITE_PLAN"])
STREETS = Path(os.environ["SKARVIK_FINAL_TOWN_ACCESS_PLAN"])
RECEIPT = Path(os.environ["SKARVIK_FINAL_PREVIOUS_ASPHALT_RECEIPT"])
OUTPUT = Path(os.environ["SKARVIK_FINAL_ACCESS_REPORT"])
ROAD = "/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
PREFIX = "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_"
MAX_ACTORS = 1800
MAX_LANES = 90
MAX_PER_SITE = 2
REPORT = {
    "state": "FAILED",
    "finalWorld": TARGET_PKG,
    "originalFilesNotModified": False,
    "accessLanesAttempted": 0,
    "accessLanesFullyBuilt": 0,
    "sitesWithRealNewAsphalt": 0,
    "actorsCreated": 0,
    "pavedMetres": 0.0,
    "skippedRelocationReviewSites": 0,
    "plannedLocalStreetCount": 992,
    "all992LocalStreetsBuilt": False,
    "regionalNetworkContinuous": False,
    "drivingOrRenderingSM5Validated": False,
    "fullCitySampleStreamed": False,
    "allSevenIslandsLinkedByRoad": False,
    "rejectedLanes": [],
    "approvedLanes": [],
}
try:
    if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
        raise RuntimeError("Unsafe staging project path")
    marker = ROOT / ".skarvik-ci-stage-marker"
    if not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip() != "41188816555":
        raise RuntimeError("Untrusted staged Unreal project")
    if not TARGET.is_file() or any(not p.is_file() for p in SOURCE_MAPS):
        raise RuntimeError("Protected final/original native World Partition map missing")
    if BACKUP.exists():
        raise RuntimeError("This town-access batch was already attempted; refuse duplicate")
    source_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE_MAPS}
    coast = json.loads(COAST.read_text(encoding="utf-8-sig"))
    streets = json.loads(STREETS.read_text(encoding="utf-8-sig"))
    previous = json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
    if coast.get("destinationWorld") != TARGET_PKG or len(coast.get("sites", [])) != 125:
        raise RuntimeError("Incorrect final coastal 125-site plan")
    if sum(bool(s.get("relocated")) for s in coast["sites"]) != 67:
        raise RuntimeError("Final coast's 67 provisional relocations not preserved")
    if len(streets.get("localStreetLayouts", [])) != 124 or streets.get("localStreetSegmentCount") != 992:
        raise RuntimeError("Not the approved 992 planned local road segments")
    if previous.get("state") != "FINAL_SEVEN_ISLAND_NATIVE_ASPHALT_SAFE_SUBSET_SAVED_NOT_YET_CONTINUOUS_OR_DRIVEN":
        raise RuntimeError("Saved original dry-asphalt stage receipt missing")
    expected_old_roads = int(previous["nativeDryAsphaltSaved"])
    if not 5000 <= expected_old_roads <= 6212:
        raise RuntimeError("Unexpected previous real 3D road actor count")
    locations = {s["id"]: s for s in coast["sites"]}
    layouts = {s["settlementId"]: s for s in streets["localStreetLayouts"]}
    if len(locations) != 125 or len(layouts) != 124 or set(layouts) != (set(locations) - {"citysample"}):
        raise RuntimeError("Settlement plan and road layout identifiers do not match")
    mesh = unreal.EditorAssetLibrary.load_asset(ROAD)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Known real City Sample road mesh not installed")
    b = mesh.get_bounds()
    width = float(b.box_extent.x) * 2.0 / 100.0
    depth = float(b.box_extent.y) * 2.0 / 100.0
    bottom = (float(b.origin.z) - float(b.box_extent.z)) / 100.0
    if not 17.0 < width < 23.0 or not 5.0 < depth < 15.0:
        raise RuntimeError("Real road StaticMesh bounds unexpectedly changed")
    native = unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native, "skarvik_final_coastal_height"):
        raise RuntimeError("Native final coastal C++ height sampler missing")
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level.load_level(TARGET_PKG):
        raise RuntimeError("Cannot reopen actual final seven-island native level")
    desc = unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    labels = [str(d.label) for d in desc]
    def count(prefix):
        return sum(label.startswith(prefix) for label in labels)
    if count("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") != expected_old_roads:
        raise RuntimeError("Previously confirmed safe existing 3D road segments absent")
    for prefix, expected in (
        ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_", 906),
        ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_", 128),
        ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_", 720),
    ):
        if count(prefix) != expected:
            raise RuntimeError("Existing original 3D buildings absent " + prefix)
    if count(PREFIX) != 0:
        raise RuntimeError("This real road batch was already imported; refuse duplicate")
    # Real persisted actor bounding boxes (not merely design-space lots).
    buildings = [
        d.bounds for d in desc
        if any(str(d.label).startswith(p) for p in (
            "SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",
            "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",
            "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",
        ))
    ]
    if len(buildings) != 1754:
        raise RuntimeError("Cannot reliably protect every native source building")
    def native_height(e, n):
        v = float(native.skarvik_final_coastal_height(e * 1000.0, n * 1000.0))
        if not math.isfinite(v) or not -30.0 < v < 1900.0:
            raise RuntimeError("Native terrain sampler produced invalid height")
        return v
    def building_free(e, n):
        x, y = e * 100000.0, -n * 100000.0
        margin = 350.0
        return not any(box.min.x - margin <= x <= box.max.x + margin and
                       box.min.y - margin <= y <= box.max.y + margin for box in buildings)
    approved = []
    total_actors = 0
    # Prioritize original safe sites. Provisional relocation coordinates must be
    # visually approved before a road changes or locks their placement.
    for site_id in sorted(layouts):
        site = locations[site_id]
        if site["relocated"]:
            REPORT["skippedRelocationReviewSites"] += 1
            continue
        shift = [float(site["targetKm"][i]) - float(site["sourceKm"][i]) for i in (0, 1)]
        if abs(shift[0]) > 0.0001 or abs(shift[1]) > 0.0001:
            raise RuntimeError("Non-relocated site unexpectedly changes location")
        attempted_for_site = 0
        for lane in layouts[site_id]["localSegments"]:
            if lane.get("class") != "access-lane" or len(lane.get("pointsKm", [])) != 2:
                continue
            if total_actors >= MAX_ACTORS or len(approved) >= MAX_LANES or attempted_for_site >= MAX_PER_SITE:
                break
            REPORT["accessLanesAttempted"] += 1
            p0, p1 = [[float(p[i]) + shift[i] for i in range(2)] for p in lane["pointsKm"]]
            distance = math.hypot((p1[0] - p0[0]) * 1000, (p1[1] - p0[1]) * 1000)
            if not 10.0 <= distance <= 460.0:
                REPORT["rejectedLanes"].append({"site": site_id, "lane": lane["id"], "why": "invalid-lane-length"})
                continue
            segments = max(1, int(math.ceil(distance / 4.5)))
            if total_actors + segments > MAX_ACTORS:
                REPORT["rejectedLanes"].append({"site": site_id, "lane": lane["id"], "why": "bounded-first-batch-budget"})
                continue
            parts = []
            reject = None
            for idx in range(segments):
                a, z = idx / segments, (idx + 1) / segments
                ea = p0[0] + (p1[0] - p0[0]) * a
                na = p0[1] + (p1[1] - p0[1]) * a
                eb = p0[0] + (p1[0] - p0[0]) * z
                nb = p0[1] + (p1[1] - p0[1]) * z
                em, nm = (ea + eb) / 2, (na + nb) / 2
                metres = math.hypot((eb - ea) * 1000, (nb - na) * 1000)
                if metres < 0.5 or any(abs(x) > 23.8 or abs(y) > 23.8 for x, y in ((ea, na), (em, nm), (eb, nb))):
                    reject = "world-edge-or-degenerate"
                    break
                if not all(building_free(x, y) for x, y in ((ea, na), (em, nm), (eb, nb))):
                    reject = "authentic-persisted-3d-building-intersection"
                    break
                ha, hb, hm = native_height(ea, na), native_height(eb, nb), native_height(em, nm)
                if min(ha, hb, hm) < 5:
                    reject = "ocean-shore-or-intertidal"
                    break
                if abs(hb - ha) / metres > 0.12:
                    reject = "longitudinal-slope-above-12pct"
                    break
                if abs((ha + hb) / 2 - hm) > 0.16:
                    reject = "uneven-grading"
                    break
                vx, vn = (eb - ea) * 1000 / metres, (nb - na) * 1000 / metres
                de, dn = -vn * .002, vx * .002
                if abs(native_height(em + de, nm + dn) - native_height(em - de, nm - dn)) > .65:
                    reject = "cross-grade-above-65cm"
                    break
                parts.append((em, nm, hm, ha, hb, metres, vx, vn))
            if reject:
                REPORT["rejectedLanes"].append({"site": site_id, "lane": lane["id"], "why": reject})
                continue
            approved.append((site_id, lane["id"], parts))
            total_actors += len(parts)
            attempted_for_site += 1
        if total_actors >= MAX_ACTORS or len(approved) >= MAX_LANES:
            break
    REPORT["safeLanesIdentified"] = len(approved)
    REPORT["safeNativeMeshActorsPreplanned"] = total_actors
    if not approved or total_actors < 20:
        raise RuntimeError("No substantial safe authentic road geometry approved; do not touch native level")
    # Back up the existing master level (not the entire World Partition external
    # actor directory); the protected original D: and graded/staged maps remain.
    BACKUP.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(TARGET, BACKUP)
    if hashlib.sha256(TARGET.read_bytes()).hexdigest() != hashlib.sha256(BACKUP.read_bytes()).hexdigest():
        raise RuntimeError("Cannot checksum staging map safety backup")
    for site_id, lane_id, parts in approved:
        for part_idx, (e, n, h, ha, hb, span, ve, vn) in enumerate(parts):
            actor = actors.spawn_actor_from_class(
                unreal.StaticMeshActor,
                unreal.Vector(e * 100000.0, -n * 100000.0, (h - bottom + .05) * 100.0))
            if not actor:
                raise RuntimeError("Native road StaticMeshActor spawn failed for " + lane_id)
            actor.set_actor_label(PREFIX + site_id + "_" + lane_id + "_" + str(part_idx).zfill(3))
            actor.tags = [unreal.Name("SKARVIK_FINAL_NATIVE_REAL_LOCAL_STREET"),
                          unreal.Name("SKARVIK_TOWN_" + site_id)]
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if not comp or not comp.set_static_mesh(mesh):
                raise RuntimeError("City Sample real road mesh could not be assigned")
            comp.set_collision_profile_name("BlockAll")
            actor.set_actor_rotation(unreal.Rotator(
                math.degrees(math.atan2(hb - ha, span)),
                math.degrees(math.atan2(-vn, ve)), 0), False)
            actor.set_actor_scale3d(unreal.Vector(span / width, 4.0 / depth, 1.0))
            REPORT["actorsCreated"] += 1
            REPORT["pavedMetres"] += span
        REPORT["accessLanesFullyBuilt"] += 1
        REPORT["approvedLanes"].append({
            "site": site_id, "lane": lane_id, "actors": len(parts),
            "pavedMetres": round(sum(p[5] for p in parts), 2),
            "regionalRoadConnectedVerified": False,
        })
    REPORT["sitesWithRealNewAsphalt"] = len(set(s["site"] for s in REPORT["approvedLanes"]))
    if REPORT["actorsCreated"] != total_actors:
        raise RuntimeError("Native road actor count not equal to fully preflighted plan")
    if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError("New real native local road assets failed to save")
    for p in SOURCE_MAPS:
        if hashlib.sha256(p.read_bytes()).hexdigest() != source_hashes[str(p)]:
            raise RuntimeError("A protected source map has unexpectedly changed")
    REPORT["pavedMetres"] = round(REPORT["pavedMetres"], 1)
    REPORT["originalFilesNotModified"] = True
    REPORT["state"] = "FINAL_COAST_SAFE_NATIVE_TOWN_ACCESS_BATCH1_SAVED_NOT_FULLY_CONNECTED_OR_DRIVEN"
    unreal.log("SKARVIK_FINAL_SAVED_REAL_ON_LAND_LOCAL_STREET_ACTORS=" + str(REPORT["actorsCreated"]))
except Exception as exc:
    REPORT["error"] = str(exc)
    REPORT["traceback"] = traceback.format_exc()
    unreal.log_error("SKARVIK_FINAL_TOWN_ACCESS_BATCH_FAILED=" + str(exc))
finally:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
