#!/usr/bin/env python3
"""Plan the second 24 SKARVIK regional-road-to-town access links.
Source: audited GitHub road graph + exact first 24-town plan and real UE5 result.
Do not choose a settlement attempted before (including unsafe rejected sites).
No road geometry is constructed here; native UE must validate every tile.
"""
import argparse
import json
from pathlib import Path
from plan_skarvik_native_town_gateway_batch import build

def build_second(audit, first_plan, first_native, limit=24):
    if first_plan.get("state") != "TOWN_GATEWAY_SHORT_CANDIDATES_SELECTED_NOT_BUILT" or first_plan.get("selectedCount") != 24:
        raise ValueError("Unexpected first batch plan")
    if first_native.get("state") != "NATIVE_TOWN_GATEWAY_SHORT_ROAD_SECTIONS_SAVED_NOT_DRIVEN":
        raise ValueError("Missing first native result")
    if first_native.get("nativeTownEntrancesAuthored") != 21 or first_native.get("nativeCompletedTownEntranceMeshes") != 608:
        raise ValueError("First native counts unexpected")
    exclude={row["settlementId"] for row in first_plan["selected"]}
    native_done={row["site"] for row in first_native["approvedEntrances"]}
    native_rejected={row["site"] for row in first_native["rejectedEntrances"]}
    if len(exclude)!=24 or native_done|native_rejected!=exclude or native_done & native_rejected:
        raise ValueError("First planned/approved/rejected sites inconsistent")
    amended=json.loads(json.dumps(audit))
    for road in amended["roadCorridors"]:
        road["plannedLocalStreetGateways"]=[gate for gate in road.get("plannedLocalStreetGateways",[])
            if gate["settlementId"] not in exclude]
    second=build(amended,limit=limit,max_distance=150)
    if second.get("selectedCount")!=24:raise ValueError("Expected 24 different new towns")
    if {entry["settlementId"] for entry in second["selected"]}&exclude:
        raise ValueError("Repeated settlement found")
    second["state"]="TOWN_GATEWAY_BATCH2_SHORT_CANDIDATES_SELECTED_NOT_BUILT"
    second["sourcePriorNativeRun"]="41277272235"
    second["sourceGraphAuditRun"]="41277057421"
    second["previouslyAttemptedTownCount"]=len(exclude)
    second["previouslyPavedTownCount"]=len(native_done)
    second["previousRejectedTownCount"]=len(native_rejected)
    second["batch"]="second-24-distinct-settlements"
    second["realAsphaltActorsBuilt"]=0
    second["nativeGradingWaterAndBuildingChecksStillRequired"]=True
    second["roadContinuityAndSM5DrivingNotYetTested"]=True
    return second

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--audit",required=True)
    p.add_argument("--first-plan",required=True)
    p.add_argument("--first-native",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    data=build_second(*[json.loads(Path(k).read_text(encoding="utf-8")) for k in
       (a.audit,a.first_plan,a.first_native)])
    output=Path(a.out)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SKARVIK_TOWN_GATEWAY_BATCH2_APPROVED_CANDIDATES="+str(data["selectedCount"]))
    print("SKARVIK_TOWN_GATEWAY_BATCH2_DIFFERENT_FROM_PREVIOUS="+str(data["previouslyAttemptedTownCount"]))
    print("SKARVIK_TOWN_GATEWAY_BATCH2_REAL_NATIVE_ROADS_BUILT=false")

if __name__=="__main__":
    main()
