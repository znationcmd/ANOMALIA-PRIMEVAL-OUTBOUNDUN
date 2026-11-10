"""RACCONIA-VARKOVIA: continue the EXISTING 16x16 km map, never create a duplicate.

Reads the user's original RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip,
verifies exactly 29 site records, 33 pre-existing corridors, terrain source,
and derives accurate UE centimeter placement & road centreline CSV/JSON.

Additional access-lane candidates are flagged NEEDS_NATIVE_SURVEY, never built.
Maritime corridors remain water routes, never converted to asphalt.
Writing is restricted to a NEW OUTSIDE-project directory, with no overwrite.

python scripts/ue5/worldgen/audit_racconia_road_access.py \
 --kit /path/RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip \
 --output /path/NEW_RACCONIA_ROAD_AUDIT
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile

SOURCE="Data/RacconiaVarkovia_Map.json"
HEIGHT="Terrain/RACCONIA_VARKOVIA_1025_R16.png"
LAND="Terrain/LandMask_1025.png"
ROOT=Path(__file__).resolve().parents[3]
KINDS={"route_principale","route_secondaire","chemin","liaison_maritime"}
MARITIME={"AZS_21","AZS_22","AZS_27"}  # ships & military island: never road connect automatically


def finite(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)


def _point(row):
    if not isinstance(row,(list,tuple)) or len(row)<2 or not finite(row[0]) or not finite(row[1]):
        raise ValueError("Non-finite or invalid route waypoint")
    if not (0 <= row[0] <= 16 and 0 <= row[1] <= 16):
        raise ValueError("Route waypoint outside 16 km map")
    return float(row[0]),float(row[1])


def load_kit(path:Path)->dict:
    """Read archive in-place, never extract untrusted ZIP paths."""
    with zipfile.ZipFile(path) as z:
        if HEIGHT not in z.namelist() or LAND not in z.namelist() or SOURCE not in z.namelist():
            raise ValueError("Missing ORIGINAL terrain/landmask/map source")
        if z.getinfo(HEIGHT).file_size < 10_000:
            raise ValueError("Missing native terrain pixels")
        payload=z.read(SOURCE)
        data=json.loads(payload.decode("utf-8-sig"))
        if (data.get("map")!="RACCONIA-VARKOVIA" or
                data.get("landscapeWidthKm")!=16 or data.get("landscapeHeightKm")!=16 or
                data.get("heightmapResolution")!=1025 or
                data.get("origin")!="southwest" or data.get("unit")!="km"):
            raise ValueError("Unknown RACCONIA source manifest")
        if len(data.get("sites",[]))!=29 or len(data.get("roads",[]))!=33:
            raise ValueError("Original 29 sites / 33 route count changed")
        if sum(r.get("type")=="liaison_maritime" for r in data["roads"])!=5:
            raise ValueError("Expected five maritime links")
        site_ids=set()
        for site in data["sites"]:
            ident=site["id"]
            if ident in site_ids or not isinstance(ident,str) or not ident.startswith("AZS_"):
                raise ValueError("Duplicate or invalid site ID")
            site_ids.add(ident)
            _point((site["x_km"],site["y_km"]))
            if not finite(site.get("ground_elevation_m")):
                raise ValueError("Invalid site elevation")
        road_ids=set()
        for road in data["roads"]:
            if road["id"] in road_ids or road["type"] not in KINDS:
                raise ValueError("Duplicate road ID or unsupported class")
            road_ids.add(road["id"])
            a=road.get("points_km")
            xyz=road.get("points_xyz_m")
            if not isinstance(a,list) or len(a)<2 or not isinstance(xyz,list) or len(a)!=len(xyz):
                raise ValueError("Route missing original alignment")
            for p,q in zip(a,xyz):
                x,y=_point(p)
                xx,yy=_point(q)
                if abs(x-xx)>0.000001 or abs(y-yy)>0.000001 or len(q)!=3 or not finite(q[2]):
                    raise ValueError("Road x/y source conventions conflict")
        return data | {"originalMapSHA256":hashlib.sha256(payload).hexdigest(),
                        "terrainPNGBytes":z.getinfo(HEIGHT).file_size,
                        "sourceZipName":path.name}


def _closest_point(site,road):
    sx,sy=site["x_km"],site["y_km"]
    best=None
    for p,q in zip(road["points_xyz_m"],road["points_xyz_m"][1:]):
        dx,dy=q[0]-p[0],q[1]-p[1]
        denom=dx*dx+dy*dy
        t=max(0.,min(1.,((sx-p[0])*dx+(sy-p[1])*dy)/denom)) if denom else 0.
        x,y=p[0]+t*dx,p[1]+t*dy
        d=1000*math.hypot(sx-x,sy-y)
        h=p[2]+t*(q[2]-p[2])
        if best is None or d<best[0]:
            best=d,x,y,h
    return best


def analyze(data:dict)->dict:
    sites=data["sites"]
    roads=data["roads"]
    terrestrial=[r for r in roads if r["type"]!="liaison_maritime"]
    routes=[]
    total_land=0.
    total_sea=0.
    high_grade=0
    for r in roads:
        length=0.
        for p,q in zip(r["points_xyz_m"],r["points_xyz_m"][1:]):
            run=math.hypot(q[0]-p[0],q[1]-p[1])*1000.
            length+=run
            if r["type"]!="liaison_maritime" and run and abs(q[2]-p[2])/run>.15:
                high_grade+=1
        routes.append({
            "id":r["id"],"type":r["type"],"from":r["from"],"to":r["to"],
            "lengthMeters":round(length,2),
            "waypoints":len(r["points_xyz_m"]),
            "state":"NAVIGATION_WATER_ONLY" if r["type"]=="liaison_maritime"
                    else "PROPOSED_CENTRELINE_NOT_DRIVEN",
        })
        if r["type"]=="liaison_maritime":total_sea+=length
        else:total_land+=length
    access=[]
    for s in sites:
        candidate=min(((_closest_point(s,r),r) for r in terrestrial),
                      key=lambda pair:pair[0][0])
        (distance,x,y,height),road=candidate
        offshore=s["id"] in MARITIME
        state=("WATER_SITE_FERRY_OR_BOAT_REVIEW_ONLY" if offshore else
               "SHORT_TOWN_ACCESS_NEEDS_TERRAIN_COLLISION_SURVEY" if distance<=200 else
               "DISTANT_TOWN_ROAD_DESIGN_NEEDED")
        access.append({
            "siteId":s["id"],"name":s["name"],"roadId":road["id"],
            "gapMeters":round(distance,2),"roadNearestKm":[round(x,5),round(y,5)],
            "siteKm":[s["x_km"],s["y_km"]],
            "elevationGapMeters":round(s["ground_elevation_m"]-height,2),
            "state":state,"nativeRoadBuilt":False,
            "bridgeAndSeaSurveyRequired":True,
            "unrealCollisionVerified":False,
        })
    return {
        "worldId":"racconia-varkovia","map":"RACCONIA-VARKOVIA",
        "extentKm":[16,16],"siteCount":29,"roadCount":33,
        "landRoadCount":len(terrestrial),"maritimeCount":5,
        "originalMapSHA256":data.get("originalMapSHA256"),
        "totalLandRoadCenterlineKm":round(total_land/1000,2),
        "totalMaritimeLineKm":round(total_sea/1000,2),
        "terrestrialSegmentsOver15PercentGrade":high_grade,
        "nativeTerrainImported":False,"nativeRoadsBuilt":False,
        "nativeSitesPlaced":False,"gameplayReady":False,
        "siteAccess":access,"routes":routes,
    }


def _coords(x_km,y_km):
    # Follows the EXISTING Racconia authoring script, not SKARVIK's -Y north!
    return round((x_km-8)*100000,2),round((y_km-8)*100000,2)


def stage(kit:Path,dest:Path)->dict:
    kit=kit.expanduser().resolve()
    dest=dest.expanduser().resolve()
    if dest==ROOT or ROOT in dest.parents or dest==kit or kit in dest.parents:
        raise ValueError("Output must be OUTSIDE source project and kit")
    if dest.exists():
        raise FileExistsError("Refusing to overwrite existing output")
    source=load_kit(kit)
    report=analyze(source)
    dest.mkdir(parents=True,exist_ok=False)
    with (dest/"racconia-29-sites-ue5.csv").open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.writer(f)
        wr.writerow(["site_id","name","x_cm","y_cm","z_cm","status"])
        for s in source["sites"]:
            x,y=_coords(s["x_km"],s["y_km"])
            wr.writerow([s["id"],s["name"],x,y,round(s["ground_elevation_m"]*100,2),
                         "MARKER_ONLY_NOT_IMPORTED"])
    with (dest/"racconia-33-routes-ue5.csv").open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.writer(f)
        wr.writerow(["road_id","class","point_index","x_cm","y_cm","z_cm","status"])
        for r in source["roads"]:
            for i,(x,y,z) in enumerate(r["points_xyz_m"]):
                cx,cy=_coords(x,y)
                wr.writerow([r["id"],r["type"],i,cx,cy,round(z*100,2),
                         "WATER_NAVIGATION_ONLY" if r["type"]=="liaison_maritime"
                          else "NOT_A_DRIVEABLE_ROAD"])
    with (dest/"racconia-site-access-review.csv").open("w",newline="",encoding="utf-8-sig") as f:
        wr=csv.writer(f)
        wr.writerow(["site_id","site_name","nearby_road","gap_metres","status"])
        for a in report["siteAccess"]:
            wr.writerow([a["siteId"],a["name"],a["roadId"],a["gapMeters"],a["state"]])
    (dest/"racconia-continuation-report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kit",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    doc=stage(args.kit,args.output)
    print(json.dumps({k:v for k,v in doc.items() if k not in ("siteAccess","routes")},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
