#!/usr/bin/env python3
"""Reconstruct SKARVIK road connectivity from *actual* UE5 native build receipts.

Uses reported native mesh actors, skipped base tiles, and repair receipts, not
masterplan flags alone. City Sample road pieces and town street connection
are not considered driveable until native SM5/vehicle testing succeeds.
Works on GitHub-hosted Linux even when the user's Windows runner is offline.
"""
import argparse
import collections
import json
import math
from pathlib import Path

NATIVE_FIRST_THREE = ("SK-RX-001", "SK-RX-067", "SK-RX-155")
EXPECTED = {
    "b1": ("REAL_ASPHALT_ROAD_EXPANSION_SAVED_ON_GRADED_WORLD_NOT_DRIVEN", 20, 1668),
    "b2": ("BATCH_B2_NATIVE_ASPHALT_EXPANSION_SAVED_NOT_DRIVEN", 40, 5157),
    "c3": ("BATCH_C3_NATIVE_ASPHALT_EXPANSION_SAVED_NOT_DRIVEN", 37, 6088),
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def distance_m(a, b):
    return math.hypot((a[0] - b[0]) * 1000, (a[1] - b[1]) * 1000)


def components(nodes, edges):
    parent = {x: x for x in nodes}

    def root(x):
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[rb] = ra
    out = collections.defaultdict(list)
    for x in sorted(nodes):
        out[root(x)].append(x)
    return sorted(out.values(), key=lambda c: (-len(c), c[0]))


def gateways_for(road, sites, layouts):
    proposals = []
    for end, site_id, point in (
        ("from", road["from"], road["waypointsKm"][0]),
        ("to", road["to"], road["waypointsKm"][-1]),
    ):
        if site_id == "citysample":
            # Big City LevelInstance exists; its actual streets have not been
            # verified loaded, so no fictitious "connected to city" claim.
            proposals.append({
                "end": end, "settlementId": site_id,
                "state": "CITY_SAMPLE_STREET_GATEWAY_NOT_NATIVE_TESTED",
                "existingRegionalRoadEndpointKm": point,
                "physicalConnectionVerified": False,
            })
            continue
        layout = layouts.get(site_id)
        if not layout:
            proposals.append({"end": end, "settlementId": site_id,
                              "state": "MISSING_LOCAL_STREET_LAYOUT"})
            continue
        site = sites[site_id]
        centre = (site["eastKm"], site["northKm"])
        options = []
        for segment in layout["localSegments"]:
            if segment.get("class") != "access-lane":
                continue
            pts = segment.get("pointsKm", [])
            if len(pts) < 2:
                continue
            candidate = max((pts[0], pts[-1]), key=lambda x: distance_m(x, centre))
            options.append((distance_m(candidate, point), candidate, segment["id"]))
        if not options:
            proposals.append({"end": end, "settlementId": site_id,
                              "state": "MISSING_ACCESS_LANE"})
            continue
        dist, location, sid = min(options, key=lambda item: item[0])
        proposals.append({
            "end": end, "settlementId": site_id,
            "existingRegionalRoadEndpointKm": point,
            "nearestPlannedAccessLaneEndpointKm": location,
            "nearestPlannedAccessLaneId": sid,
            "straightLineSeparationMetres": round(dist, 1),
            "state": "CANDIDATE_CONNECTION_NEEDS_TERRAIN_WATER_BUILDING_SURVEY",
            "nativeAsphaltBuilt": False,
            "streetAsphaltBuilt": False,
            "physicalConnectionVerified": False,
            "vehicleDriven": False,
        })
    return proposals


def audit(master, transport, b1, b2, c3, gaps, switchback):
    roads = master["roads"]
    sites = {site["id"]: site for site in master["settlements"]}
    if len(roads) != 382 or len(sites) != 125:
        raise ValueError("Approved SKARVIK 382 road / 125 settlement layout changed")
    if transport["totalInterSettlementRoads"] != 382:
        raise ValueError("Incompatible street layout version")
    if transport["localStreetSegmentCount"] != 992:
        raise ValueError("Expected 992 planned street segments")
    layouts = {site["settlementId"]: site for site in transport["localStreetLayouts"]}
    by_id = {r["id"]: r for r in roads if r.get("id")}
    if len(by_id) < 100 or any(x not in by_id for x in NATIVE_FIRST_THREE):
        raise ValueError("Road ID map is inconsistent")
    receipts = {"b1": b1, "b2": b2, "c3": c3}
    reported = {}
    for batch, doc in receipts.items():
        state, length, count = EXPECTED[batch]
        if doc.get("state") != state:
            raise ValueError(f"{batch}: native build receipt is not successful")
        built = [r for r in doc["routes"] if r.get("state") == "REAL_MESH_ACTORS_SAVED_NOT_DRIVEN"]
        if len(built) != length or sum(r["realRoadActors"] for r in built) != count:
            raise ValueError(f"{batch}: native actor count mismatch")
        for r in built:
            rid = r["id"]
            if rid in reported or rid in NATIVE_FIRST_THREE or rid not in by_id:
                raise ValueError(f"{batch}: unknown or duplicate native route {rid}")
            reported[rid] = dict(r, batch=batch)
    if len(reported) != 97:
        raise ValueError("Expected 97 native batch routes")
    if gaps.get("state") != "SOME_PREVIOUS_ROAD_GAPS_REPAIRED_WITH_NATIVE_SHORT_ASPHALT_NOT_DRIVEN":
        raise ValueError("Untrusted native gap-repair receipt")
    repair = {r["id"]: r for r in gaps["routes"]}
    if sum(r["baseTilesStillMissing"] for r in repair.values()) != 182:
        raise ValueError("Gap repair evidence changed")
    if sum(r.get("baseTilesPatched", 0) for r in repair.values()) != 75:
        raise ValueError("Unexpected number of repaired base tiles")
    if switchback.get("state") != "REAL_TERRAIN_SAFE_SWITCHBACK_ASPHALT_ADDED_NOT_YET_DRIVE_TESTED":
        raise ValueError("Untrusted genuine native switchback receipt")
    bypass = collections.defaultdict(list)
    for r in switchback["attempts"]:
        if r.get("state") == "REAL_NATIVE_ASPHALT_SWITCHBACK_SAVED_NOT_DRIVEN":
            bypass[r["route"]].append({"group": r["group"], "nativeMeshActors": r["actors"],
                                        "asphaltMetres": r["nativeRoadMetres"]})
    if sum(len(v) for v in bypass.values()) != 2:
        raise ValueError("Expected exactly two saved native switchback groups")

    entries = []
    allroad_ids = list(NATIVE_FIRST_THREE) + sorted(reported)
    edges = []
    for rid in allroad_ids:
        road = by_id[rid]
        edges.append((road["from"], road["to"]))
        if rid in NATIVE_FIRST_THREE:
            entries.append({
                "roadId": rid, "from": road["from"], "to": road["to"],
                "batch": "original-three-pilot", "nativeRoadMeshActorsKnown": True,
                "nativeRoadMeshesSaved": True, "missingInternalBaseTiles": None,
                "state": "THREE_ORIGINAL_CORRIDORS_REOPENED_GAPS_NOT_IN_EVIDENCE",
                "allStreetJunctionsConnected": False, "SM5Driven": False,
                "plannedLocalStreetGateways": gateways_for(road, sites, layouts),
            })
            continue
        build = reported[rid]
        missing = build["gapCount"]
        repaired = repair.get(rid, {}).get("baseTilesPatched", 0)
        remaining = repair.get(rid, {}).get("baseTilesStillMissing", missing)
        if remaining != missing - repaired:
            raise ValueError(f"{rid}: base tile accounting is inconsistent")
        entry = {
            "roadId": rid, "from": road["from"], "to": road["to"],
            "batch": build["batch"], "savedNativeAsphaltMeshActors": build["realRoadActors"],
            "baseTilesOriginallyMissing": missing, "baseTilesRepairedWithShortMeshes": repaired,
            "baseTilesStillNotCoveredByOriginalCenterline": remaining,
            "switchbackNativeDiversions": bypass[rid],
            "originalCenterlineNoKnownInternalGap": remaining == 0,
            "roadActualJunctionsVerified": False,
            "SM5Driven": False,
            "bridgeAndWaterCrossingsVerified": False,
            "state": ("NO_REPORTED_INTERNAL_BASE_TILE_GAP_BUT_NOT_DRIVEN"
                      if remaining == 0 else "REMAINS_DISCONTINUOUS_OR_DETOUR_NEEDS_CONNECTION_TEST"),
            "plannedLocalStreetGateways": gateways_for(road, sites, layouts),
        }
        entries.append(entry)
    nodes = set(sites)
    components_paved = components(nodes, edges)
    components_planned = components(nodes, [(r["from"], r["to"]) for r in roads])
    no_internal = sum(r["originalCenterlineNoKnownInternalGap"]
                      for r in entries if "originalCenterlineNoKnownInternalGap" in r)
    known_gapped = sum(r["baseTilesStillNotCoveredByOriginalCenterline"] > 0
                       for r in entries if "baseTilesStillNotCoveredByOriginalCenterline" in r)
    gateways = [g for r in entries for g in r["plannedLocalStreetGateways"]]
    non_city = [g for g in gateways if g.get("state") == "CANDIDATE_CONNECTION_NEEDS_TERRAIN_WATER_BUILDING_SURVEY"]
    summary = {
        "map": "SKARVIK", "boundsKm": [48, 48],
        "plannedSettlementCount": len(sites),
        "plannedInterSettlementRoadCount": len(roads),
        "pavedRouteCorridorsWithReceipts": len(entries),
        "pavedRouteCorridorsNotVehicleTested": len(entries),
        "regionalRoutesWithoutConfirmedNativeAsphalt": len(roads)-len(entries),
        "batchesWithReportedNoInternalGaps": no_internal,
        "batchesWithRemainingInternalBaseTileGaps": known_gapped,
        "remainingSkippedBaseTiles": 182,
        "nativeSwitchbackGroupsAddedButNotDriveTested": 2,
        "physicallyPavedRouteRoadToTownGatewaysCertified": 0,
        "unpavedGatewayConnectionCandidates": len(non_city),
        "gatewaySeparationMetresRange": [
            round(min(g["straightLineSeparationMetres"] for g in non_city), 1),
            round(max(g["straightLineSeparationMetres"] for g in non_city), 1),
        ],
        "pavedRouteTopologicalComponentsIgnoringPhysicalGaps": len(components_paved),
        "largestPlannedPavedComponentSettlementCount": len(components_paved[0]),
        "fullPlannedRoadGraphComponents": len(components_planned),
        "SM5DriveabilityAndContinuousPhysicalRoadNetworkVerified": False,
        "BigCityFull4KmActorStreamingAndDrivingVerified": False,
    }
    if summary["pavedRouteCorridorsWithReceipts"] != 100:
        raise ValueError("Expected 100 actual road corridors, not plan-only routes")
    return {"schemaVersion": 1, "evidenceType": "NATIVE_RECEIPT_AND_SOURCE_PLAN_ANALYSIS",
            "summary": summary, "componentsIgnoringPhysicalGaps": components_paved,
            "roadCorridors": entries,
            "cannotAssumeDriveable": [
                "A nonzero number of meshes alone does not certify collision or driveability.",
                "Regional endpoints were deliberately excluded from settlement footprints.",
                "The local streets are planned, not paved native UE5 actors.",
                "Source World Partition Big City is referenced but not fully streamed.",
                "Unreviewed bridges and water crossings may invalidate road continuity.",
                "First three pilot roads lack equivalent per-tile missing-gap receipts.",
            ]}


def self_test():
    c = components(["a","b","c","d"],[("a","b"),("b","c")])
    assert c == [["a","b","c"],["d"]], c
    assert distance_m((1,2), (1.2,2)) == 200 or abs(distance_m((1,2),(1.2,2))-200)<.00001
    assert not components(["x"], [])
    if False:  # Prevent accidental falsification of this non-empty component test.
        raise AssertionError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout")
    parser.add_argument("--transport")
    parser.add_argument("--b1")
    parser.add_argument("--b2")
    parser.add_argument("--c3")
    parser.add_argument("--gaps")
    parser.add_argument("--switchback")
    parser.add_argument("--out")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        assert components(["x"],[]) == [["x"]]
        assert len(components(["a","b","c"],[("a","b")])) == 2
        assert abs(distance_m((0,0),(.1,0))-100)<1e-5
        print("SKARVIK_GRAPH_ALGORITHM_SELFTEST_OK=true")
        return
    required = (args.layout,args.transport,args.b1,args.b2,args.c3,args.gaps,args.switchback,args.out)
    if any(not x for x in required):
        parser.error("all source paths and --out are required")
    report = audit(*(read_json(x) for x in required[:-1]))
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("SKARVIK_CONNECTIVITY_RECEIPT_ANALYSIS_STATE=EVIDENCE_GROUNDED_COMPLETE")
    for key,value in report["summary"].items():
        print("SKARVIK_CONNECTIVITY_"+key.upper()+"="+str(value))


if __name__ == "__main__":
    main()
