"""Build bounded genuine City Sample road-surface segments on FINAL SKARVIK coastline.

Accept only route IDs marked dry-grade-compatible by independent native survey
41314750218. Resample every 4.5m and reject ocean, cliff, cross-slope, actual
building footprints and old road footprints. This intentionally builds *short
separated safe fragments*, not claims of connected 382-route drivable network.
One attempt only, only on isolated C stage, with backup and protected D originals.
"""
import hashlib
import json
import math
import os
import shutil
import traceback
from collections import defaultdict
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
FINAL = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
TARGET = ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCE_MAPS = (
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
    ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
    ROOT / "Content/Map/Big_City_LVL.umap",
    Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
)
PLAN = Path(os.environ["SKARVIK_FINAL_REGIONAL_ROAD_PLAN"])
COAST = Path(os.environ["SKARVIK_FINAL_REGIONAL_SITE_PLAN"])
AUDIT = Path(os.environ["SKARVIK_FINAL_REGIONAL_SURVEY_RECEIPT"])
OUTPUT = Path(os.environ["SKARVIK_FINAL_REGIONAL_PILOT_REPORT"])
BACKUP = ROOT / "Saved/SkarvikCity/FinalRealRegionalCoastalPilot20261101/final-before-regional-pilot.umap"
PREFIX = "SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
ASSET = "/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
MAX_ACTORS = 700
MAX_ROUTE_COUNT = 8
MAX_CANDIDATE_ROUTES = 30
MIN_RUN_SEGMENTS = 16   # 70+ metres before a discrete new road fragment is worth saving
MAX_RUN_SEGMENTS = 160  # 720m per candidate run: bounded native actor creation
CELL = 16000.0         # 160m XY spatial bins, in Unreal centimetres
REPORT = {
    "state": "FAILED",
    "world": FINAL,
    "sourceWorldsUnmodified": False,
    "originalCoastAndSevenIslandsPreserved": True,
    "safeOriginalAsphaltPreserved": False,
    "newRoadActors": 0,
    "newPavedMetres": 0.,
    "newRouteIdentifiersRepresented": 0,
    "newPartialRoadFragments": 0,
    "potentialDrySurveyRoutes": 0,
    "surveyedRealRoadRoutes": 0,
    "all382RoadsFinished": False,
    "fullRouteContinuityValidated": False,
    "hasNewRoadFragmentsNotFullRoutes": True,
    "buildVisualSM5Passed": False,
    "vehicleDrivingTestPassed": False,
    "allBridgesSurveyed": False,
    "ferryLinksTested": False,
    "rejectedRoutes": [],
    "approvedFragments": [],
}
try:
    marker = ROOT / ".skarvik-ci-stage-marker"
    if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
            or not marker.is_file()
            or marker.read_text(encoding="utf-8-sig").strip() != "41188816555"):
        raise RuntimeError("Untrusted isolated Unreal stage; not writing")
    if not TARGET.is_file() or any(not f.is_file() for f in SOURCE_MAPS):
        raise RuntimeError("Protected real native map absent")
    if BACKUP.exists():
        raise RuntimeError("The native regional road pilot was already attempted; no duplicated roads")
    before = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in SOURCE_MAPS}
    roads = json.loads(PLAN.read_text(encoding="utf-8-sig"))["roads"]
    coast = json.loads(COAST.read_text(encoding="utf-8-sig"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8-sig"))
    if len(roads) != 382 or len(coast["sites"]) != 125:
        raise RuntimeError("Untrusted original road/site plan")
    if (audit.get("state") != "SKARVIK_FINAL_382_ROUTE_NATIVE_COAST_FEASIBILITY_SURVEY_ONLY_NO_BUILD"
            or audit.get("noGeometryRoadCount") != 137
            or audit.get("surveyedWaypointRoadCount") != 245):
        raise RuntimeError("Native independently surveyed regional route receipt missing")
    native = unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native, "skarvik_final_coastal_height"):
        raise RuntimeError("Compiled final coastline C++ height source missing")
    mesh = unreal.EditorAssetLibrary.load_asset(ASSET)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Original CitySample road StaticMesh unavailable")
    bounds = mesh.get_bounds()
    source_x = float(bounds.box_extent.x) * 2. / 100.
    source_y = float(bounds.box_extent.y) * 2. / 100.
    bottom = (float(bounds.origin.z) - float(bounds.box_extent.z)) / 100.
    if not 17. < source_x < 23. or not 5. < source_y < 15.:
        raise RuntimeError("Unverified true asphalt mesh dimensions")
    lv = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not lv.load_level(FINAL):
        raise RuntimeError("Cannot reopen final 48km World Partition level")
    wp = unreal.WorldPartitionBlueprintLibrary
    desc = wp.get_actor_descs() or []
    labels = [str(d.label) for d in desc]
    def count(prefix):
        return sum(s.startswith(prefix) for s in labels)
    for p, n in (
        ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_", 6130),
        ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_", 1674),
        ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_", 1298),
        ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_", 906),
        ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_", 128),
        ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_", 720),
    ):
        if count(p) != n:
            raise RuntimeError("Trusted original 3D actors absent: "+p+" expected "+str(n))
    if any(s.startswith(PREFIX) for s in labels):
        raise RuntimeError("Native regional fragments previously saved; refuse duplicate")
    obstacles = defaultdict(list)
    huge = []
    prefixes = (
        "SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",
        "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",
        "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",
        "SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",
        "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",
        "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",
    )
    protected_obstacles = 0
    for d in desc:
        label = str(d.label)
        if not label.startswith(prefixes):
            continue
        b = d.bounds
        row = (float(b.min.x), float(b.min.y), float(b.max.x), float(b.max.y),
               "building" if any(label.startswith(p) for p in prefixes[3:]) else "road")
        if not all(math.isfinite(q) for q in row[:4]):
            raise RuntimeError("A source road or building has nonfinite WP bounds")
        protected_obstacles += 1
        x0, y0, x1, y1, _ = row
        i0, j0 = math.floor(x0 / CELL), math.floor(y0 / CELL)
        i1, j1 = math.floor(x1 / CELL), math.floor(y1 / CELL)
        if (i1 - i0 + 1) * (j1 - j0 + 1) > 100:
            huge.append(row)
            continue
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                obstacles[(i, j)].append(row)
    REPORT["protectedPriorSavedActorCount"] = protected_obstacles
    if protected_obstacles != 6130 + 1674 + 1298 + 906 + 128 + 720:
        raise RuntimeError("Persistent obstacle bounds incomplete")
    def intersects(x, y):
        # Both coordinate arguments in native Unreal cm.
        candidates = obstacles.get((math.floor(x / CELL), math.floor(y / CELL)), [])
        for x0, y0, x1, y1, kind in list(candidates) + huge:
            margin = 600. if kind == "building" else 480.
            if x0-margin <= x <= x1+margin and y0-margin <= y <= y1+margin:
                return kind
        return None
    h = native.skarvik_final_coastal_height
    def height(e, n):  # east/north in metres; C++ native survey coordinates
        value = float(h(e, n))
        if not math.isfinite(value) or not -30. < value < 1900.:
            raise RuntimeError("Invalid native final terrain height")
        return value
    sites = {s["id"]: s for s in coast["sites"]}
    survey = {row["id"]: row for row in audit["routes"]}
    candidates = []
    for route in roads:
        rid = route.get("id")
        if not rid or rid not in survey or not route.get("waypointsKm"):
            continue
        if survey[rid].get("state") != "TERRAIN_SURVEY_DRY_GRADE_ONLY_NO_BUILDING_OR_DRIVE_PROOF":
            continue
        length = float(survey[rid]["metresSurveyed"])
        if not 100. <= length <= 5500.:
            continue
        candidates.append((length, rid, route))
    candidates.sort(key=lambda row: (row[0], row[1]))
    REPORT["potentialDrySurveyRoutes"] = len(candidates)
    selected = []
    selected_labels = set()
    for _, rid, route in candidates[:MAX_CANDIDATE_ROUTES]:
        if REPORT["newRouteIdentifiersRepresented"] >= MAX_ROUTE_COUNT or sum(len(p[2]) for p in selected) >= MAX_ACTORS:
            break
        source_site = sites.get(route.get("from"))
        dest_site = sites.get(route.get("to"))
        if (not source_site or not dest_site
                or bool(source_site.get("relocated"))
                or bool(dest_site.get("relocated"))):
            REPORT["rejectedRoutes"].append({"id": rid, "why": "unapproved-relocated-or-missing-endpoint"})
            continue
        # Some old relocation records are not marked; never use those.
        if any(math.hypot(*[float(s["targetKm"][i])-float(s["sourceKm"][i]) for i in (0, 1)]) > .001
               for s in (source_site, dest_site)):
            REPORT["rejectedRoutes"].append({"id": rid, "why": "unflagged-coordinate-discrepancy"})
            continue
        REPORT["surveyedRealRoadRoutes"] += 1
        parts = []
        for p0, p1 in zip(route["waypointsKm"], route["waypointsKm"][1:]):
            ea, na = float(p0[0])*1000., float(p0[1])*1000.
            eb, nb = float(p1[0])*1000., float(p1[1])*1000.
            distance = math.hypot(eb-ea, nb-na)
            steps = math.ceil(distance/4.5)
            for i in range(steps):
                t0, t1 = i/steps, (i+1)/steps
                e0, n0 = ea+(eb-ea)*t0, na+(nb-na)*t0
                e1, n1 = ea+(eb-ea)*t1, na+(nb-na)*t1
                em, nm = (e0+e1)*.5, (n0+n1)*.5
                metres = math.hypot(e1-e0, n1-n0)
                valid = True
                if metres < .5 or any(abs(e)>23750. or abs(n)>23750. for e,n in ((e0,n0),(em,nm),(e1,n1))):
                    valid = False
                if valid and abs(em-2000.)<2250. and abs(nm+8000.)<2250.:
                    valid = False  # do not damage reserved full 4x4 km Big City source footprint
                if valid and any(intersects(e*100.,-n*100.) for e,n in ((e0,n0),(em,nm),(e1,n1))):
                    valid = False
                if valid:
                    h0, h1, hm = height(e0,n0), height(e1,n1), height(em,nm)
                    if min(h0,h1,hm)<5. or abs(h1-h0)/metres>.12 or abs((h0+h1)/2.-hm)>.16:
                        valid = False
                    else:
                        de=(e1-e0)/metres; dn=(n1-n0)/metres
                        if abs(height(em-dn*2.,nm+de*2.)-height(em+dn*2.,nm-de*2.))>.65:
                            valid = False
                if valid:
                    parts.append((em,nm,hm,h0,h1,metres,(e1-e0)/metres,(n1-n0)/metres))
                else:
                    parts.append(None)
        # Find genuine continuously dry/coast-safe fragments; never fill gaps with fictitious bridges.
        runs = []
        current = []
        for item in parts + [None]:
            if item is None:
                if len(current)>=MIN_RUN_SEGMENTS:
                    for st in range(0,len(current),MAX_RUN_SEGMENTS):
                        piece=current[st:st+MAX_RUN_SEGMENTS]
                        if len(piece)>=MIN_RUN_SEGMENTS: runs.append(piece)
                current=[]
            else:
                current.append(item)
        if not runs:
            REPORT["rejectedRoutes"].append({"id":rid,"why":"no-nonoverlapping-native-dry-fragment-70m"})
            continue
        reserved = sum(len(p[2]) for p in selected)
        kept = 0
        for run in runs:
            if reserved + len(run)>MAX_ACTORS:continue
            # Candidate fragments from different routes also must not overlap one another.
            if any(any(math.hypot(x[0]-q[0],x[1]-q[1])<5. for q in selected_labels) for x in run):
                continue
            selected.append((rid,len(selected),run))
            for item in run:selected_labels.add((round(item[0],1),round(item[1],1)))
            reserved += len(run)
            kept += 1
            if kept>=2:break
        if kept:
            REPORT["newRouteIdentifiersRepresented"] += 1
        else:
            REPORT["rejectedRoutes"].append({"id":rid,"why":"fragment-budget-or-alignment-overlap"})
    REPORT["preflightApprovedRealMeshCount"] = sum(len(t[2]) for t in selected)
    REPORT["preflightApprovedFragmentCount"] = len(selected)
    if not selected:
        REPORT["state"] = "NO_NEW_COLLISION_FREE_REGIONAL_ASPHALT_AVAILABLE_WITHOUT_BRIDGES_OR_EARTHWORKS"
        REPORT["sourceWorldsUnmodified"] = True
        unreal.log("SKARVIK_FINAL_REGIONAL_REAL_ROAD_PILOT_NO_SAFE_PATCH_NO_NATIVE_WRITE=true")
    else:
        BACKUP.parent.mkdir(parents=True,exist_ok=False)
        shutil.copy2(TARGET,BACKUP)
        if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(TARGET.read_bytes()).hexdigest():
            raise RuntimeError("Cannot verify final native level map backup")
        for rid, patch_index, run in selected:
            for i, (e,n,z,z0,z1,span,de,dn) in enumerate(run):
                actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
                     unreal.Vector(e*100.,-n*100.,(z-bottom+.05)*100.))
                if not actor:
                    raise RuntimeError("Native road actor could not be instantiated")
                actor.set_actor_label(PREFIX+rid+"_RUN_"+str(patch_index).zfill(2)+"_"+str(i).zfill(3))
                actor.tags=[unreal.Name("SKARVIK_FINAL_NEW_ORIGINAL_CITY_ROAD_MESH"),
                            unreal.Name("SKARVIK_REGIONAL_ROAD_FRAGMENT_NOT_CONNECTED")]
                component=actor.get_component_by_class(unreal.StaticMeshComponent)
                if not component or not component.set_static_mesh(mesh):
                    raise RuntimeError("Real source asphalt mesh cannot be assigned")
                component.set_collision_profile_name("BlockAll")
                actor.set_actor_rotation(unreal.Rotator(
                    math.degrees(math.atan2(z1-z0,span)),
                    math.degrees(math.atan2(-dn,de)),0),False)
                actor.set_actor_scale3d(unreal.Vector(span/source_x,4.4/source_y,1.))
                REPORT["newRoadActors"]+=1
                REPORT["newPavedMetres"]+=span
            REPORT["newPartialRoadFragments"]+=1
            REPORT["approvedFragments"].append({
                "sourceRoadId":rid,
                "sourceCenterlineNotFullyReproduced":True,
                "native3DRoadActors":len(run),
                "nativePavedMetres":round(sum(p[5] for p in run),1),
                "driveableContinuityTested":False,
                "bridgesOverSeaAutomaticallyBuilt":False,
            })
        if REPORT["newRoadActors"]!=REPORT["preflightApprovedRealMeshCount"]:
            raise RuntimeError("Not every fully surveyed road mesh was constructed")
        if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
            raise RuntimeError("New genuine native regional asphalt actors not persisted")
        REPORT["state"]="FINAL_NATIVE_COAST_AUTHENTIC_REGIONAL_SAFE_ROAD_FRAGMENTS_SAVED_NOT_DRIVEN_OR_CONNECTED"
        REPORT["sourceWorldsUnmodified"]=True
        REPORT["safeOriginalAsphaltPreserved"]=True
        REPORT["newPavedMetres"]=round(REPORT["newPavedMetres"],1)
        unreal.log("SKARVIK_FINAL_REGIONAL_NATIVE_GENUINE_REAL_ASPHALT_ACTORS="+str(REPORT["newRoadActors"]))
    for p in SOURCE_MAPS:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
            raise RuntimeError("Protected original source map changed")
except Exception as exc:
    REPORT["error"]=str(exc)
    REPORT["traceback"]=traceback.format_exc()
    unreal.log_error("SKARVIK_FINAL_REGIONAL_SAFE_NATIVE_PILOT_FAILED="+str(exc))
finally:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
