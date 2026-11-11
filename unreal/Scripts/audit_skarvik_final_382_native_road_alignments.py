"""Read-only original-coast regional road feasibility survey for final SKARVIK.

The plan contains 137 connections with no waypoint geometry and 245 with
explicit alignment polylines. Never turn the 137 abstract links into imaginary
3D asphalt. Sample all 245 against actual compiled native coast/grade to
locate water, steep segments and missing bridge design. Building/traffic and
SM5 driving still need separate checks before construction.
"""
import hashlib
import json
import math
import os
import traceback
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = Path(os.environ["SKARVIK_FINAL_REGIONAL_ROAD_SURVEY_RESULT"])
CONFIG = Path(os.environ["SKARVIK_FINAL_REGIONAL_ROAD_LAYOUT"])
FILES = (
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
    ROOT / "Content/Map/Big_City_LVL.umap",
    Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
)
REPORT = {
    "state": "FAILED",
    "readOnly": True,
    "all382RoutesConstructed": False,
    "roadsVisuallyVerified": False,
    "SM5DriveContinuityValidated": False,
    "nativeAsphaltActorsBuiltThisRun": 0,
    "unverifiedBridgesRequired": True,
    "noGeometryRoadCount": 0,
    "surveyedWaypointRoadCount": 0,
    "fullyDryGradeSurveyedRouteCount": 0,
    "routesNeedingWaterOrGradeDesign": 0,
    "metresSurveyed": 0,
    "dryGradeAcceptableMetresApprox": 0,
    "waterRiskMetresApprox": 0,
    "gradeRiskMetresApprox": 0,
    "routes": [],
}
try:
    mark = ROOT / ".skarvik-ci-stage-marker"
    if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
            or not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip() != "41188816555"):
        raise RuntimeError("Untrusted native stage")
    if any(not p.is_file() for p in FILES):
        raise RuntimeError("An original/final map package is missing")
    payload = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    roads = payload.get("roads")
    if not isinstance(roads, list) or len(roads) != 382:
        raise RuntimeError("Expected exactly 382 source road connections")
    if len([r for r in roads if isinstance(r.get("waypointsKm"), list)]) != 245:
        raise RuntimeError("245 explicit alignment route requirement changed")
    protected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
    native = unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native, "skarvik_final_coastal_height"):
        raise RuntimeError("Compiled true-coast native height sampler unavailable")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
        raise RuntimeError("Final seven-island world cannot reopen")
    desc = unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    old_road_count = sum(str(x.label).startswith("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") for x in desc)
    if old_road_count != 6130:
        raise RuntimeError("Missing 6130 previously saved genuine original roads")
    def height(e, n):
        v = float(native.skarvik_final_coastal_height(e, n))
        if not math.isfinite(v):
            raise RuntimeError("Nonfinite native coast height")
        return v
    for k, road in enumerate(roads):
        points = road.get("waypointsKm")
        name = road.get("id") or "LEGACY-{:03d}".format(k + 1)
        if not points:
            REPORT["noGeometryRoadCount"] += 1
            REPORT["routes"].append({
                "id": name,
                "from": road.get("from"),
                "to": road.get("to"),
                "state": "DESIGN_ONLY_NO_SOURCE_WAYPOINTS",
                "metresSurveyed": 0,
                "nativeRoadBuilt": False,
            })
            continue
        REPORT["surveyedWaypointRoadCount"] += 1
        safe, water, grade, measured, bad = 0., 0., 0., 0., []
        for a, b in zip(points, points[1:]):
            x0, y0 = float(a[0]) * 1000., float(a[1]) * 1000.
            x1, y1 = float(b[0]) * 1000., float(b[1]) * 1000.
            length = math.hypot(x1 - x0, y1 - y0)
            if not 0.1 < length < 15000.0:
                raise RuntimeError("Implausible source road waypoint segment: " + name)
            pieces = int(math.ceil(length / 25.0))
            for j in range(pieces):
                t0, t1 = j / pieces, (j + 1) / pieces
                p0 = (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
                p1 = (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)
                cx, cy = (p0[0] + p1[0]) / 2., (p0[1] + p1[1]) / 2.
                m = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                measured += m
                if any(abs(x) > 23750 or abs(y) > 23750 for x, y in (p0, p1, (cx, cy))):
                    water += m
                    if len(bad) < 30: bad.append({"reason": "outside-world", "at": [round(cx), round(cy)]})
                    continue
                h0, h1, hm = height(*p0), height(*p1), height(cx, cy)
                if min(h0, h1, hm) < 5.0:
                    water += m
                    if len(bad) < 30: bad.append({"reason": "coastal-water", "at": [round(cx), round(cy)]})
                    continue
                if abs(h1 - h0) / m > .12 or abs((h0 + h1) / 2. - hm) > .35:
                    grade += m
                    if len(bad) < 30: bad.append({"reason": "grade-earthworks", "at": [round(cx), round(cy)]})
                    continue
                safe += m
        if measured <= 0: raise RuntimeError("Empty native terrain road survey " + name)
        REPORT["metresSurveyed"] += measured
        REPORT["dryGradeAcceptableMetresApprox"] += safe
        REPORT["waterRiskMetresApprox"] += water
        REPORT["gradeRiskMetresApprox"] += grade
        fully_dry = water == 0 and grade == 0
        if fully_dry: REPORT["fullyDryGradeSurveyedRouteCount"] += 1
        else: REPORT["routesNeedingWaterOrGradeDesign"] += 1
        REPORT["routes"].append({
            "id": name,
            "from": road.get("from"),
            "to": road.get("to"),
            "state": "TERRAIN_SURVEY_DRY_GRADE_ONLY_NO_BUILDING_OR_DRIVE_PROOF" if fully_dry else "NEEDS_BRIDGE_GRADING_OR_COASTAL_REROUTE",
            "metresSurveyed": round(measured, 1),
            "potentialDryGradeMetres": round(safe, 1),
            "waterOrOutsideMetres": round(water, 1),
            "steepOrUnevenMetres": round(grade, 1),
            "examples": bad,
            "realAsphaltBuiltHere": False,
        })
    for p in FILES:
        if hashlib.sha256(p.read_bytes()).hexdigest() != protected[str(p)]:
            raise RuntimeError("Read-only survey changed protected original/final Unreal map")
    for field in ("metresSurveyed", "dryGradeAcceptableMetresApprox",
                  "waterRiskMetresApprox", "gradeRiskMetresApprox"):
        REPORT[field] = round(REPORT[field], 1)
    if REPORT["noGeometryRoadCount"] != 137 or REPORT["surveyedWaypointRoadCount"] != 245:
        raise RuntimeError("Regional road source categories no longer sum to 382")
    REPORT.update({
        "state": "SKARVIK_FINAL_382_ROUTE_NATIVE_COAST_FEASIBILITY_SURVEY_ONLY_NO_BUILD",
        "existingOriginalRoad3DActors": old_road_count,
        "sourceMapsUnchanged": True,
        "sampleSpacingMetresMax": 25,
    })
    unreal.log("SKARVIK_FINAL_REAL_NATIVE_382_ROAD_SURVEY_DONE=true")
except Exception as exc:
    REPORT["error"] = str(exc)
    REPORT["traceback"] = traceback.format_exc()
    unreal.log_error("SKARVIK_382_FINAL_COAST_ROAD_AUDIT_FAILED=" + str(exc))
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(REPORT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
