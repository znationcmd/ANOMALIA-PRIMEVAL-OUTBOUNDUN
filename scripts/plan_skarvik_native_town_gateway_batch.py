#!/usr/bin/env python3
"""Choose a controlled first group of SKARVIK regional-road to town-access gaps.

No native Unreal or landscape data are present in CI. Every suggestion stays
'needs native terrain/collision survey', never incorrectly marked built.
"""
import argparse
import json
from pathlib import Path


def build(audit, limit=24, max_distance=150):
    corridors = audit["roadCorridors"]
    proposals = []
    for road in corridors:
        # Existing corridor should not have known gaps before adding gateways.
        if road.get("state") != "NO_REPORTED_INTERNAL_BASE_TILE_GAP_BUT_NOT_DRIVEN":
            continue
        for gate in road["plannedLocalStreetGateways"]:
            if gate.get("state") != "CANDIDATE_CONNECTION_NEEDS_TERRAIN_WATER_BUILDING_SURVEY":
                continue
            if gate["straightLineSeparationMetres"] > max_distance:
                continue
            proposals.append({
                "roadId": road["roadId"],
                "roadClass": road.get("batch"),
                "end": gate["end"],
                "settlementId": gate["settlementId"],
                "regionalRoadEndpointKm": gate["existingRegionalRoadEndpointKm"],
                "accessLaneOuterPointKm": gate["nearestPlannedAccessLaneEndpointKm"],
                "accessLaneId": gate["nearestPlannedAccessLaneId"],
                "straightLineGapMetres": gate["straightLineSeparationMetres"],
                "nativeRoadGapPaved": False,
                "nativeTownAccessLanePaved": False,
                "terrainAndCollisionCheckRequired": True,
                "bridgeAndWaterCrossingReviewRequired": True,
                "SM5DrivingTestRequired": True,
            })
    proposals.sort(key=lambda x: (x["straightLineGapMetres"],x["settlementId"],x["roadId"]))
    selected = []
    visited = set()
    for p in proposals:
        if p["settlementId"] in visited:
            continue
        selected.append(p)
        visited.add(p["settlementId"])
        if len(selected) >= limit:
            break
    if len(selected) < 12:
        raise ValueError("Not enough safe short town gateways in native evidence")
    return {
        "schemaVersion": 1,
        "state": "TOWN_GATEWAY_SHORT_CANDIDATES_SELECTED_NOT_BUILT",
        "world": "/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2",
        "candidateSource": "Native 100-road receipts & local street layouts",
        "maxStraightLineDistanceMetres": max_distance,
        "selected": selected,
        "selectedCount": len(selected),
        "shortGatewayCandidatesBeforeOnePerTownLimit": len(proposals),
        "physicalRoadsCreated": 0,
        "nativeTerrainAndBuildingCollisionChecksDone": False,
        "citySampleAndExistingRoadsUntouched": True,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audit",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--max-distance",type=int,default=150)
    p.add_argument("--limit",type=int,default=24)
    a = p.parse_args()
    report=build(json.loads(Path(a.audit).read_text(encoding="utf-8")), a.limit, a.max_distance)
    path=Path(a.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SKARVIK_TOWN_GATEWAY_PLANNING_STATE="+report["state"])
    print("SKARVIK_TOWN_GATEWAY_FIRST_BATCH="+str(report["selectedCount"]))
    print("SKARVIK_TOWN_GATEWAY_CANDIDATES_UNDER_150M="+str(report["shortGatewayCandidatesBeforeOnePerTownLimit"]))
    print("SKARVIK_TOWN_GATEWAY_STILL_REQUIRES_NATIVE_TERRAIN_AND_COLLISION=true")


if __name__=="__main__":
    main()
