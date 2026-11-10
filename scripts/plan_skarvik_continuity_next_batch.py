"""Advance the REAL SKARVIK FINAL coastal plan without changing UE5 .umap files.

Existing documents on THIS branch are authoritative design/native receipts:
- 48x48 km masterplan: 125 sites + 382 route records (137 lack geometry)
- Final coastal relocation: 67 sites have proposed, unapproved new centres.
This audit checks city footprint conflicts, route endpoints stranded by moving
sites, and outputs a first manual-survey batch + 125/382 full audit.

NO edits to D: drive, original world or packed .umap/.uasset.
NO assertion that routes are driven, sites moved or buildings placed.

python scripts/plan_skarvik_continuity_next_batch.py \
  --world public/config/skarvik-world-layout-48km.json \
  --coast public/config/skarvik-final-coastal-migration-125-sites.json \
  --output /tmp/SKARVIK_NEXT_REVIEW_NEW
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/"public/config/skarvik-world-layout-48km.json"
COAST=ROOT/"public/config/skarvik-final-coastal-migration-125-sites.json"


def read(path:Path):
    raw=path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), hashlib.sha256(raw).hexdigest()


def distance_m(a,b):
    return math.hypot(float(a[0])-float(b[0]),float(a[1])-float(b[1]))*1000


def rect_overlaps(c1,w1,c2,w2):
    return (abs(float(c1[0])-float(c2[0])) < (float(w1[0])+float(w2[0]))/2 and
            abs(float(c1[1])-float(c2[1])) < (float(w1[1])+float(w2[1]))/2)


def validate(master,coast):
    if master.get("world")!="SKARVIK" or coast.get("world")!="SKARVIK":
        raise ValueError("Mismatched source world")
    if master.get("extentKm",{}).get("width")!=48 or coast.get("worldSideKm")!=48:
        raise ValueError("Refusing to shrink original SKARVIK 48km world")
    if coast.get("destinationWorld")!="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1":
        raise ValueError("Do not silently target the original or another .umap")
    ms=master.get("settlements")
    cs=coast.get("sites")
    roads=master.get("roads")
    if not isinstance(ms,list) or not isinstance(cs,list) or not isinstance(roads,list):
        raise ValueError("Missing source lists")
    if len(ms)!=125 or len(cs)!=125 or len(roads)!=382:
        raise ValueError("Expected existing 125 sites / 382 routes")
    if sum(bool(s.get("relocated")) for s in cs)!=67:
        raise ValueError("67 relocation reviews changed unexpectedly")
    by_master={s["id"]:s for s in ms}
    by_coast={s["id"]:s for s in cs}
    if len(by_master)!=125 or len(by_coast)!=125 or set(by_coast)!=set(by_master):
        raise ValueError("Duplicate or mismatched town IDs")
    if len([r for r in roads if r.get("waypointsKm")])!=245:
        raise ValueError("245 explicit route alignments are required")
    city=master.get("citySample",{})
    if city.get("cityCenterKm")!=[2,-8] or city.get("fullCityKm")!=[4,4]:
        raise ValueError("City Sample 4x4km original footprint changed")
    if by_coast["citysample"].get("targetKm")!=[2,-8]:
        raise ValueError("City Sample city centre moved!")
    if not coast.get("originalC2026WorldsNeverOverwritten"):
        raise ValueError("Source map protection disabled")
    for s in cs:
        p=s.get("targetKm")
        if not isinstance(p,list) or len(p)!=2 or not all(isinstance(q,(int,float))
             and math.isfinite(q) for q in p) or any(abs(q)>24 for q in p):
            raise ValueError("Site outside original World Partition bounds")
        if not isinstance(s.get("originalFootprintKm"),list) or len(s["originalFootprintKm"])!=2:
            raise ValueError("Missing original site footprint")
    return by_coast,roads


def world_to_cm(km):
    # Different from RACCONIA: SKARVIK's ORIGINAL native plan has -Y = North.
    return [round(float(km[0])*100000,1),round(-float(km[1])*100000,1)]


def plan(master,coast):
    sites,roads=validate(master,coast)
    city=sites["citysample"]
    candidates=[]
    for s in coast["sites"]:
        conflicts=[]
        if s["id"]!="citysample" and rect_overlaps(
          s["targetKm"],s["originalFootprintKm"],
          city["targetKm"],city["originalFootprintKm"]):
            conflicts.append("INTERSECTS_PRESERVED_CITYSAMPLE_4X4KM")
        # Pairwise building/plot overlap is a design conflict, not proof of collision.
        for other in coast["sites"]:
            if s["id"]==other["id"]:
                continue
            if rect_overlaps(s["targetKm"],s["originalFootprintKm"],
                             other["targetKm"],other["originalFootprintKm"]):
                conflicts.append("POSSIBLE_FOOTPRINT_CONFLICT:"+other["id"])
        clearance=float(s["targetCoastDistanceM"])
        if clearance<200:
            conflicts.append("NEAR_COAST_OR_PORT_NEEDS_VISUAL_SURVEY")
        if s.get("relocated"):
            conflicts.append("RELOCATION_UNAPPROVED_REQUIRES_HUMAN_REVIEW")
        if s["targetLandmass"]!="original-mainland":
            conflicts.append("PROTECT_EXISTING_ISLAND_NATIVE_CORE")
        candidates.append({
          "id":s["id"],"name":s["name"],"class":s["settlementClass"],
          "sourceKm":s["sourceKm"],"targetKm":s["targetKm"],
          "targetUECentimeters":world_to_cm(s["targetKm"]),
          "relocated":bool(s.get("relocated")),
          "distanceMovedMeters":round(distance_m(s["sourceKm"],s["targetKm"]),1),
          "coastClearanceMeters":round(clearance,1),
          "landmass":s["targetLandmass"],
          "conflicts":sorted(conflicts),
          "nativeTownTransformed":False,"approvedForNativeWriting":False,
        })
    routes=[]
    missing=0
    stranded=0
    for i,r in enumerate(roads):
        rid=r.get("id") or f"LEGACY_NO_GEOMETRY_{i+1:03d}"
        p=r.get("waypointsKm")
        a,b=r.get("from"),r.get("to")
        if a not in sites or b not in sites:
            raise ValueError("Road has unknown endpoint "+rid)
        if not p:
            missing+=1
            routes.append({"id":rid,"from":a,"to":b,
                "status":"NO_WAYPOINT_GEOMETRY_DESIGN_ONLY",
                "physicalRoadVerified":False})
            continue
        if len(p)<2:
            raise ValueError("Truncated road polyline")
        first,last=p[0],p[-1]
        if not all(len(v)>=2 and all(isinstance(k,(int,float)) and math.isfinite(k)
                        for k in v[:2]) for v in (first,last)):
            raise ValueError("Invalid polyline coordinates")
        gap_a=distance_m(first,sites[a]["targetKm"])
        gap_b=distance_m(last,sites[b]["targetKm"])
        disconnected=max(gap_a,gap_b)>250
        stranded+=int(disconnected)
        routes.append({"id":rid,"from":a,"to":b,
           "sourceWaypoints":len(p),
           "endGapsMeters":[round(gap_a,1),round(gap_b,1)],
           "status":"REPLAN_ENDPOINT_AFTER_COASTAL_RELOCATION" if disconnected else
                    "CENTRELINE_REVIEW_NATIVE_COLLISIONS_AND_WATER",
           "roadRebuiltInFinalWorldByThisRun":False,
           "bridgeVerified":False,"vehicleDriveVerified":False})
    if missing!=137:
        raise ValueError("Missing geometry count diverged")
    # First safe review: short inland moves, non-overlap, offshore cores excluded.
    # These remain PENDING even when selected; *no* collision/terrain proof here.
    shortlist=sorted((s for s in candidates if s["relocated"] and
           s["landmass"]=="original-mainland" and s["coastClearanceMeters"]>=300 and
           not any(x.startswith("INTERSECTS_") or x.startswith("POSSIBLE_FOOTPRINT")
                   for x in s["conflicts"])),
           key=lambda s:(s["distanceMovedMeters"],-s["coastClearanceMeters"],s["id"]))[:15]
    return {
      "schemaVersion":1,"state":"SKARVIK_COAST_NEXT_SURVEY_CANDIDATES_ONLY",
      "world":"SKARVIK","worldSizeKm":[48,48],
      "existingCitySampleFootprintKm":[4,4],
      "citySampleCenterKm":[2,-8],
      "originalCoastalUnrealWorldsPreserved":True,
      "allSevenIslandWorldsUntouched":True,
      "existingSettlements":125,"relocationsPendingManualApproval":67,
      "regionalRoadsInMasterplan":382,
      "routeRecordsWithoutGeometry":missing,
      "routeCentrelineEndpointsBeyond250mOfCoastalTarget":stranded,
      "nextReviewBatchCount":len(shortlist),
      "nextReviewBatch":shortlist,
      "allSettlements":candidates,"allRoadChecks":routes,
      "newBuildingActorsBuilt":0,"roadsBuiltHere":0,
      "SM5PIEValidated":False,"finalCoastalMapChanged":False,
    }


def generate(world_path:Path,coast_path:Path,output:Path):
    world_path=world_path.resolve()
    coast_path=coast_path.resolve()
    output=output.expanduser().resolve()
    if (output==ROOT or ROOT in output.parents or output in (world_path,coast_path) or
        output==world_path.parent or output==coast_path.parent):
        raise ValueError("Output must not be inside original Unreal/source project")
    if output.exists():
        raise FileExistsError("Never overwrite existing SKARVIK reports")
    master,h1=read(world_path)
    coast,h2=read(coast_path)
    report=plan(master,coast)
    report["sourceSHA256"]={"worldPlan":h1,"coastPlan":h2}
    output.mkdir(parents=True,exist_ok=False)
    (output/"skarvik-next-native-survey.json").write_text(
       json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (output/"skarvik-relocations-review.csv").open("w",encoding="utf-8-sig",newline="") as fh:
        w=csv.writer(fh)
        w.writerow(["siteId","name","sourceEastKm","sourceNorthKm","targetEastKm",
          "targetNorthKm","targetUEXcm","targetUEYcm","movedMeters","coastClearanceM",
          "warnings","approvedForNativeWriting"])
        for s in report["allSettlements"]:
            if not s["relocated"]:continue
            w.writerow([s["id"],s["name"],*s["sourceKm"],*s["targetKm"],
                 *s["targetUECentimeters"],s["distanceMovedMeters"],
                 s["coastClearanceMeters"],"|".join(s["conflicts"]),"false"])
    with (output/"skarvik-road-endpoint-gaps.csv").open("w",encoding="utf-8-sig",newline="") as fh:
        w=csv.writer(fh)
        w.writerow(["roadId","from","to","gapFromM","gapToM","status"])
        for r in report["allRoadChecks"]:
            gap=r.get("endGapsMeters",[None,None])
            w.writerow([r["id"],r["from"],r["to"],*gap,r["status"]])
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--world",type=Path,default=MASTER)
    ap.add_argument("--coast",type=Path,default=COAST)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    r=generate(args.world,args.coast,args.output)
    print(json.dumps({k:v for k,v in r.items() if k not in
          ("allSettlements","allRoadChecks","nextReviewBatch")},indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
