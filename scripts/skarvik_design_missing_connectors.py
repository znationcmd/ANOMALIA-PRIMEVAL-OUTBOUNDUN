"""SKARVIK 48km: generate NON-DESTRUCTIVE regional road connector study.

Uses exactly the approved original 125-town coastline and 382-route masterplan
on the EXISTING SKARVIK CitySample branch, not the generic 48km worldgen map.
Produces proposed bridge/road/ferry survey lines in new isolated JSON/CSV ONLY.
These lines are NOT native meshes, approved relocation decisions or drivable
roads. No old cities, islands, heightmaps, source metadata, or .umap modified.

python scripts/skarvik_design_missing_connectors.py \
  --out /tmp/SKARVIK_CONNECTORS_REVIEW_NEW
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
ORIGINAL=HERE/"public/config/skarvik-world-layout-48km.json"
COAST=HERE/"public/config/skarvik-final-coastal-migration-125-sites.json"
EXPECTED_WORLD="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"


def distance_metres(a,b):
    return math.hypot(float(a[0])-float(b[0]),float(a[1])-float(b[1]))*1000


def to_ue_cm(pair):
    """SKARVIK uses -Y north, unlike original RACCONIA map conventions."""
    return [round(float(pair[0])*100000,2),round(-float(pair[1])*100000,2)]


def _read(file:Path):
    raw=file.read_bytes()
    return json.loads(raw.decode("utf-8-sig")),hashlib.sha256(raw).hexdigest()


def propose(master,coast):
    if (master.get("world")!="SKARVIK" or coast.get("world")!="SKARVIK" or
        master.get("extentKm",{}).get("width")!=48 or
        master.get("extentKm",{}).get("height")!=48 or
        coast.get("worldSideKm")!=48 or
        coast.get("destinationWorld")!=EXPECTED_WORLD):
        raise ValueError("Refusing another world or another 48 km final level")
    town_rows=coast.get("sites",[])
    roads=master.get("roads",[])
    if (len(town_rows)!=125 or len(roads)!=382 or
        sum(bool(t.get("relocated")) for t in town_rows)!=67):
        raise ValueError("Untrusted original 125 town/382 route/67 coastal move plan")
    towns={s["id"]:s for s in town_rows}
    if len(towns)!=125:
        raise ValueError("Duplicate settlements")
    city=master.get("citySample",{})
    if city.get("cityCenterKm")!=[2,-8] or city.get("fullCityKm")!=[4,4]:
        raise ValueError("Existing full City Sample footprint must remain 4x4 km")
    without=0
    long_route_count=0
    segments=[]
    for index,road in enumerate(roads):
        route_id=road.get("id") or f"UNGEOMETRIED_{index+1:03d}"
        if road.get("from") not in towns or road.get("to") not in towns:
            raise ValueError("Unknown original regional road endpoint")
        points=road.get("waypointsKm")
        if not points:
            without+=1
            continue
        if len(points)<2:
            raise ValueError("Invalid source alignment")
        for end,site_id,original in (("from",road["from"],points[0]),
                                     ("to",road["to"],points[-1])):
            target=towns[site_id]["targetKm"]
            metres=distance_metres(original,target)
            if metres<=25:
                continue
            offshore=towns[site_id]["targetLandmass"]!="original-mainland"
            if offshore:
                kind="ISLAND_FERRY_BRIDGE_DESIGN_ONLY"
            elif site_id=="citysample":
                kind="CITY_SAMPLE_STREET_LINK_NATIVE_GEOMETRY_REQUIRED"
            elif metres>3000:
                kind="RELOCATION_LONG_ROUTE_REPLAN_REQUIRED"
            else:
                kind="LAND_CORRIDOR_NATIVE_COAST_GRADE_COLLISION_SURVEY_REQUIRED"
            # A straight line is an UNAPPROVED placeholder for a terrain survey,
            # never an automatically accepted asphalt road.
            segments.append({
              "id":f"{route_id}:{end}", "routeId":route_id, "endpoint":end,
              "settlementId":site_id,"settlementName":towns[site_id]["name"],
              "siteRelocated":bool(towns[site_id]["relocated"]),
              "targetCoastClearanceMeters":towns[site_id]["targetCoastDistanceM"],
              "sourcePolylineEndpointKm":list(original[:2]),
              "newSettlementCenterKm":list(target),
              "sourceUECm":to_ue_cm(original),
              "targetUECm":to_ue_cm(target),
              "distanceMetres":round(metres,2),
              "state":kind,
              "requiresCoastHeightCheck":True,
              "requiresUnrealActorFootprintCollisionCheck":True,
              "needsBridgeFerryAndWorldPartitionSurvey":True,
              "approvedForNativeAsphaltBuild":False,
              "builtOrDrivable":False,
            })
        long_route_count+=int(
            max(distance_metres(points[0],towns[road["from"]]["targetKm"]),
                distance_metres(points[-1],towns[road["to"]]["targetKm"]))>250)
    if without!=137 or long_route_count!=236:
        raise ValueError(f"Original 137/no geometry and 236 disconnected routes have changed: {without}/{long_route_count}")
    # Prioritize relatively short, mainland, inland endpoints to examine FIRST.
    first=[s for s in segments if
           s["state"]=="LAND_CORRIDOR_NATIVE_COAST_GRADE_COLLISION_SURVEY_REQUIRED"
           and s["targetCoastClearanceMeters"]>=300 and
           25<s["distanceMetres"]<=600 and not s["siteRelocated"]]
    first.sort(key=lambda s:(s["distanceMetres"],s["settlementId"],s["routeId"]))
    result={
        "schemaVersion":1,"world":"SKARVIK","extentKm":[48,48],
        "sourceLevel":EXPECTED_WORLD,"citySample4KmPreserved":True,
        "offshoreIslandsPreserved":7,"existingTownCount":125,
        "unapprovedCoastalRelocations":67,"regionalRoutes":382,
        "routesWithoutPolyline":without,"routesDisconnectedBeyond250M":long_route_count,
        "connectorEndpointsNeedingNativeAssessment":len(segments),
        "first20SurveyCandidates":first[:20],
        "allConnectorCandidates":segments,
        "nativeLandscapeModified":False,"roadMeshesAdded":0,
        "boatFerryAssetsCreated":False,"PIEOrSM5DriveTestPassed":False,
    }
    return result


def stage(master:Path,coast:Path,output:Path):
    master=master.resolve();coast=coast.resolve();output=output.expanduser().resolve()
    if (output==HERE or HERE in output.parents or output in (master,coast) or
        output in (master.parent,coast.parent)):
        raise ValueError("Refusing output inside SKARVIK source or UE project")
    if output.exists():
        raise FileExistsError("Do not overwrite an existing SKARVIK review")
    src,sha1=_read(master);coast_data,sha2=_read(coast)
    result=propose(src,coast_data)
    result["sourceSHA256"]={"originalRoadLayout":sha1,"originalCoastalSitePlan":sha2}
    output.mkdir(parents=True,exist_ok=False)
    (output/"skarvik-all-connector-review.json").write_text(
      json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (output/"skarvik-all-connector-review.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(("id","route","town","oldXcm","oldYcm","targetXcm",
                    "targetYcm","distanceM","type","nativeApproved"))
        for s in result["allConnectorCandidates"]:
            w.writerow((s["id"],s["routeId"],s["settlementName"],
              *s["sourceUECm"],*s["targetUECm"],s["distanceMetres"],
              s["state"],"false"))
    with (output/"skarvik-first20-native-checks.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        w.writerow(("id","road","town","gapM","oldEastKm","oldNorthKm","targetEastKm","targetNorthKm"))
        for s in result["first20SurveyCandidates"]:
            w.writerow((s["id"],s["routeId"],s["settlementName"],s["distanceMetres"],
                        *s["sourcePolylineEndpointKm"],*s["newSettlementCenterKm"]))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--master",type=Path,default=ORIGINAL)
    p.add_argument("--coast",type=Path,default=COAST)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=stage(args.master,args.coast,args.out)
    print(json.dumps({k:v for k,v in report.items() if k not in
       ("allConnectorCandidates","first20SurveyCandidates")},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
