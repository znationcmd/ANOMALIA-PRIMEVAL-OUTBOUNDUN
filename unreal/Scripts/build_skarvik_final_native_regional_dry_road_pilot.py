"""Add a *bounded* set of certified dry, unoccupied regional 3D asphalt routes.

Only route IDs listed as fully dry/grade-surveyed by independently run native
coast survey may be considered. Require original endpoints unchanged, 5m
sampling, actual World Partition building/road bounds and shoulder grade.
Reject entire candidate if any interval conflicts; no disconnected strips,
bridges, partial underwater roads, or duplication of existing final asphalt.

Building successful corridors does NOT certify vehicle driving, multiplayer,
nor all 382 regional routes. The 137 unlocated links remain design-only.
"""
import hashlib
import json
import math
import os
import shutil
import traceback
from collections import Counter
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
WORLD = "/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
WORLD_FILE = ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
ORIGINAL_FILES = (
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
 ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT / "Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT / "Content/Map/Big_City_LVL.umap")
SURVEY = Path(os.environ["SKARVIK_FINAL_REGIONAL_SURVEY"])
ROUTES = Path(os.environ["SKARVIK_FINAL_REGIONAL_PLAN"])
SITES = Path(os.environ["SKARVIK_FINAL_REGIONAL_SITE_PLAN"])
OUT = Path(os.environ["SKARVIK_FINAL_REGIONAL_NATIVE_BUILD_REPORT"])
BACKUP = ROOT / "Saved/SkarvikCity/FinalNativeOriginalCoastRegionalRoadPilot20261101/final-before-native-regional-pilot.umap"
MESH = "/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
PREFIX = "SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
MAX_ROUTES = 3
MAX_ACTORS = 1050
GRID = 15000.0  # ~150 metres in Unreal cm
result = {
 "state": "FAILED", "verifiedRegionalRoutesAdded": 0,
 "actualNativeRoadMeshActorsAdded": 0, "nativeRoadMetresAdded": 0.,
 "all382RoutesConnected": False, "all992LocalStreetsBuilt": False,
 "fullyDrivableSM5Tested": False, "allBridgesAndCulvertsValidated": False,
 "fullCitySamplePlayable": False, "avoidedExistingAsphalt": True,
 "approved": [], "rejected": [], "originalFilesChanged": False}
try:
 marker = ROOT / ".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
     or not marker.is_file()
     or marker.read_text(encoding="utf-8-sig").strip() != "41188816555"):
  raise RuntimeError("Untrusted staging project")
 if not WORLD_FILE.is_file() or any(not p.is_file() for p in ORIGINAL_FILES):
  raise RuntimeError("Protected native source map missing")
 if BACKUP.exists():raise RuntimeError("Native regional road pilot was already attempted; do not repeat")
 audit=json.loads(SURVEY.read_text(encoding="utf-8-sig"))
 roadplan=json.loads(ROUTES.read_text(encoding="utf-8-sig"))
 siteplan=json.loads(SITES.read_text(encoding="utf-8-sig"))
 if audit.get("state")!="SKARVIK_FINAL_382_ROUTE_NATIVE_COAST_FEASIBILITY_SURVEY_ONLY_NO_BUILD":
  raise RuntimeError("Native original coastline feasibility proof missing")
 if (audit.get("fullyDryGradeSurveyedRouteCount")!=45 or
     audit.get("surveyedWaypointRoadCount")!=245 or len(roadplan.get("roads",[]))!=382):
  raise RuntimeError("Unexpected source 382-route native coast audit totals")
 if len(siteplan.get("sites",[]))!=125:
  raise RuntimeError("Unexpected 125-site coast manifest")
 road_by_id={r["id"]:r for r in roadplan["roads"] if r.get("id")}
 sites={s["id"]:s for s in siteplan["sites"]}
 allowed=[x["id"] for x in audit["routes"]
          if x["state"]=="TERRAIN_SURVEY_DRY_GRADE_ONLY_NO_BUILDING_OR_DRIVE_PROOF"]
 if len(allowed)!=45 or len(set(allowed))!=45:
  raise RuntimeError("45 independently audited route IDs missing")
 obj=unreal.EditorAssetLibrary.load_asset(MESH)
 if not isinstance(obj,unreal.StaticMesh):raise RuntimeError("Authentic CitySample road static mesh missing")
 box=obj.get_bounds()
 dimx=float(box.box_extent.x)*2/100.
 dimy=float(box.box_extent.y)*2/100.
 bottom=(float(box.origin.z)-float(box.box_extent.z))/100.
 if not (17<dimx<23 and 5<dimy<15):raise RuntimeError("Road mesh dimensions invalid")
 h=unreal.AnomaliaZPrigimaliaWorldImportLibrary.skarvik_final_coastal_height
 if not callable(h):raise RuntimeError("Native true-coast height sampler missing")
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level(WORLD):raise RuntimeError("Final seven-island native world could not load")
 editor=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(prefix):return sum(x.startswith(prefix) for x in labels)
 for key,num in (
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298)):
  if count(key)!=num:raise RuntimeError("Previously persisted original world actor count changed "+key)
 if count(PREFIX):raise RuntimeError("Regional pilot asphalt already authored")
 protected_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in ORIGINAL_FILES}
 building_prefixes=("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",
                    "SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",
                    "SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",
                    "SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_E5_")
 road_prefixes=("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",
                "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",
                "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",
                "SKARVIK_FINAL_SAFE_TOWN_ACCESS_B3_")
 blocks=[d.bounds for d in desc if str(d.label).startswith(building_prefixes)]
 asphalt=[d.bounds for d in desc if str(d.label).startswith(road_prefixes)]
 result["existingNativeBuildingsProtected"]=len(blocks)
 result["existingNativeAsphaltSegmentsProtected"]=len(asphalt)
 def bins_for(b,margin):
  x0=int(math.floor((float(b.min.x)-margin)/GRID))
  x1=int(math.floor((float(b.max.x)+margin)/GRID))
  y0=int(math.floor((float(b.min.y)-margin)/GRID))
  y1=int(math.floor((float(b.max.y)+margin)/GRID))
  if x1-x0>5 or y1-y0>5:raise RuntimeError("Unexpected oversized bounding collision region")
  for i in range(x0,x1+1):
   for j in range(y0,y1+1):
    yield i,j
 index={}
 for b in asphalt:
  for cell in bins_for(b,550.):
   index.setdefault(cell,[]).append(b)
 def blocked(e,n):
  x=e*100.;y=-n*100.
  for b in blocks:
   if b.min.x-500<=x<=b.max.x+500 and b.min.y-500<=y<=b.max.y+500:
    return "original-building-intersection"
  nearby=index.get((math.floor(x/GRID),math.floor(y/GRID)),[])
  for b in nearby:
   if b.min.x-550<=x<=b.max.x+550 and b.min.y-550<=y<=b.max.y+550:
    return "already-paved-native-road-overlap"
  return None
 def height(e,n):
  v=float(h(e,n))
  if not math.isfinite(v):raise RuntimeError("Nonfinite original coast terrain")
  return v
 planned=[]
 stats=Counter()
 for route_id in allowed:
  if len(planned)>=MAX_ROUTES:break
  route=road_by_id.get(route_id)
  if not route or len(route.get("waypointsKm",[]))<2:
   stats["bad-original-polyline"]+=1
   continue
  from_site=sites.get(route.get("from"))
  to_site=sites.get(route.get("to"))
  if not from_site or not to_site:
   stats["missing-town-source"]+=1
   continue
  if any(s["relocated"] or math.hypot(*(float(s["targetKm"][i])-float(s["sourceKm"][i]) for i in (0,1)))>.00001
         for s in (from_site,to_site)):
   stats["provisional-endpoint-relocation"]+=1
   continue
  parts=[];reason=None
  for p0,p1 in zip(route["waypointsKm"],route["waypointsKm"][1:]):
   x0,y0=float(p0[0])*1000,float(p0[1])*1000
   x1,y1=float(p1[0])*1000,float(p1[1])*1000
   dist=math.hypot(x1-x0,y1-y0)
   if dist<4 or dist>15000:reason="bad-polyline-length";break
   pieces=math.ceil(dist/4.5)
   for k in range(pieces):
    t0,t1=k/pieces,(k+1)/pieces
    a=(x0+(x1-x0)*t0,y0+(y1-y0)*t0)
    b=(x0+(x1-x0)*t1,y0+(y1-y0)*t1)
    e,n=(a[0]+b[0])/2.,(a[1]+b[1])/2.
    span=math.hypot(b[0]-a[0],b[1]-a[1])
    if span<0.5 or any(abs(x)>23750 or abs(y)>23750 for x,y in (a,b,(e,n))):
     reason="road-outside-world";break
    if any(abs(x-2000.)<2050 and abs(y+8000.)<2050 for x,y in (a,b,(e,n))):
     reason="city-4km-no-regional-duplicate";break
    for x,y in (a,b,(e,n)):
     reason=blocked(x,y)
     if reason:break
    if reason:break
    ha,hb,hm=height(*a),height(*b),height(e,n)
    if min(ha,hb,hm)<5:
     reason="coast-ocean-or-beach";break
    if abs(hb-ha)/span>.12 or abs((ha+hb)/2-hm)>.18:
     reason="unapproved-earthworks";break
    vx,vn=(b[0]-a[0])/span,(b[1]-a[1])/span
    if abs(height(e-vn*3,n+vx*3)-height(e+vn*3,n-vx*3))>.65:
     reason="road-cross-grade";break
    parts.append((e,n,hm,ha,hb,span,vx,vn))
   if reason:break
  if reason:
   stats[reason]+=1;result["rejected"].append({"route":route_id,"reason":reason})
   continue
  if len(parts)+sum(len(t[1]) for t in planned)>MAX_ACTORS:
   stats["bounded-run-actor-budget"]+=1
   continue
  if len(parts)<20:stats["unreasonably-short-regional-route"]+=1;continue
  planned.append((route_id,parts))
 result["eligibleFullDryRoutesAfterBuildingsAndRoadOverlap"]=len(planned)
 result["routePreflightRejections"]=dict(stats)
 if not planned:
  result["state"]="NO_NEW_REGIONAL_CORRIDOR_PASSED_ALL_NATIVE_BUILDING_AND_EXISTING_ROAD_GATES"
 else:
  BACKUP.parent.mkdir(parents=True,exist_ok=False)
  shutil.copy2(WORLD_FILE,BACKUP)
  if hashlib.sha256(WORLD_FILE.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
   raise RuntimeError("Staging final pre-road backup mismatch")
  for route_id,parts in planned:
   for j,(e,n,hm,ha,hb,span,vx,vn) in enumerate(parts):
    actor=editor.spawn_actor_from_class(unreal.StaticMeshActor,
                  unreal.Vector(e*100,-n*100,(hm-bottom+.06)*100))
    if not actor:raise RuntimeError("Could not spawn genuine road actor")
    actor.set_actor_label("{}{}_{}".format(PREFIX,route_id,j))
    actor.tags=[unreal.Name("SKARVIK_FINAL_NATIVE_REGIONAL_ROAD"),unreal.Name(route_id)]
    c=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not c or not c.set_static_mesh(obj):
     raise RuntimeError("Cannot attach real road static mesh")
    c.set_collision_profile_name("BlockAll")
    actor.set_actor_rotation(unreal.Rotator(
      math.degrees(math.atan2(hb-ha,span)),
      math.degrees(math.atan2(-vn,vx)),0),False)
    actor.set_actor_scale3d(unreal.Vector(span/dimx,5.5/dimy,1))
   result["approved"].append({"id":route_id,"nativeActors":len(parts),
       "asphaltMetres":round(sum(p[5] for p in parts),1),
       "trulyDrivableTestPassed":False})
   result["verifiedRegionalRoutesAdded"]+=1
   result["actualNativeRoadMeshActorsAdded"]+=len(parts)
   result["nativeRoadMetresAdded"]+=sum(p[5] for p in parts)
  if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
   raise RuntimeError("Native safe regional asphalt actors not saved")
  result["state"]="FINAL_SEVEN_ISLAND_BOUNDED_DRY_REGIONAL_REAL_ASPHALT_SAVED_NOT_DRIVEN"
 for p in ORIGINAL_FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=protected_hashes[str(p)]:
   raise RuntimeError("An original map changed during regional road planning")
 result["nativeRoadMetresAdded"]=round(result["nativeRoadMetresAdded"],1)
 result["originalFilesChanged"]=False
 unreal.log("SKARVIK_FINAL_REAL_DRY_REGIONAL_ROAD_ACTORS="+str(result["actualNativeRoadMeshActorsAdded"]))
except Exception as exc:
 result["error"]=str(exc);result["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_REGIONAL_ASPHALT_PILOT_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
