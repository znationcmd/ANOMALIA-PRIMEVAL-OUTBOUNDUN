"""Expand real SKARVIK roads on the EXISTING graded 48km World Partition map.

Real City Sample asphalt meshes, terrain grades and settlement footprints checked.
All work occurs in the trusted isolated C stage, never in the original D project.
Incomplete terrain routes remain flagged, not fake continuous driveable roads.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
MAP_FILE=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
PREV=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/RoadExpansionBatchC3_20261031/graded-pre-expansion.umap"
PLAN=Path(os.environ["SKARVIK_ROAD_EXPANSION_LAYOUT"])
REPORT=Path(os.environ["SKARVIK_ROAD_EXPANSION_REPORT"])
APPROVED=(
 "SK-RX-174",
 "SK-RX-199",
 "SK-RX-202",
 "SK-RX-068",
 "SK-RX-181",
 "SK-RX-177",
 "SK-RX-156",
 "SK-RX-047",
 "SK-RX-183",
 "SK-RX-063",
 "SK-RX-116",
 "SK-RX-126",
 "SK-RX-036",
 "SK-RX-187",
 "SK-RX-203",
 "SK-RX-190",
 "SK-RX-188",
 "SK-RX-074",
 "SK-RX-230",
 "SK-RX-031",
 "SK-RX-148",
 "SK-RX-192",
 "SK-RX-198",
 "SK-RX-193",
 "SK-RX-123",
 "SK-RX-014",
 "SK-RX-053",
 "SK-RX-185",
 "SK-RX-212",
 "SK-RX-154",
 "SK-RX-217",
 "SK-RX-054",
 "SK-RX-205",
 "SK-RX-194",
 "SK-RX-196",
 "SK-RX-090",
 "SK-RX-210",
 "SK-RX-206",
 "SK-RX-082",
 "SK-RX-093"
)
ALREADY=("SK-RX-001","SK-RX-067","SK-RX-155")
ASSET="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
report={"state":"BLOCKED","map":PKG,"additionalRoadMeshActors":0,"additionalRouteCount":0,
        "newRoadSurfaceMetres":0.0,"routes":[],"existingRoadsRetained":0,
        "existingBuildingActorsRetained":0,"gradeAndFootprintOnly":True,
        "bridgeCulvertAndWaterReviewed":False,"SM5Driven":False,
        "entire382RoadsBuilt":False,"originalDModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Unsafe native stage path")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Native stage marker wrong")
 for p in (MAP_FILE,ORIGINAL,PREV):
  if not p.is_file():raise RuntimeError("Missing protected map "+str(p))
 if BACKUP.exists():raise RuntimeError("Already attempted this batch; avoid duplicate roads")
 if any((ROOT/"Content"/x).exists() for x in ("Crowd","Vehicle")):
  raise RuntimeError("Unapproved full City Sample AI and vehicles assets")
 source=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(source["settlements"])!=125 or len(source["roads"])!=382:
  raise RuntimeError("Expected exact 125/382 masterplan")
 roads={r["id"]:r for r in source["roads"] if r.get("id") in APPROVED}
 if len(roads)!=len(APPROVED):raise RuntimeError("Approved new road IDs missing")
 settlements=source["settlements"]
 prior={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (ORIGINAL,PREV)}
 terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(terrain,"skarvik_graded_height"):
  raise RuntimeError("Graded native height sampler not compiled")
 mesh=unreal.EditorAssetLibrary.load_asset(ASSET)
 if not isinstance(mesh,unreal.StaticMesh):
  raise RuntimeError("Real native CitySample paved road missing")
 bounds=mesh.get_bounds()
 dims=(2*bounds.box_extent.x/100.0,2*bounds.box_extent.y/100.0)
 if not (17.<dims[0]<23. and 5.<dims[1]<15.):
  raise RuntimeError("Road mesh geometry dimensions invalid: "+str(dims))
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Cannot reopen populated SKARVIK graded world")
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(x.label) for x in desc]
 building=[x for x in labels if x.startswith("SKARVIK_GRADED_SITE_")]
 existing=[x for x in labels if x.startswith("SKARVIK_GRADED_ROAD_")]
 if len(building)!=1039 or len(existing)!=126:
  raise RuntimeError("Wrong previously validated world: buildings={} roads={}".format(len(building),len(existing)))
 oldexp=[x for x in labels if x.startswith("SKARVIK_EXPANSION_ROAD_SK-RX-")]
 if len(oldexp)!=1668:raise RuntimeError("Previously verified 1668 road expansion actors missing")
 oldb2=[x for x in labels if x.startswith("SKARVIK_EXPANSION_B2_ROAD_")]
 if len(oldb2)!=5157:raise RuntimeError("Previously verified 5157 batch B2 3D road actors absent")
 if any(x.startswith("SKARVIK_EXPANSION_C3_ROAD_") for x in labels):
  raise RuntimeError("Batch 2 roads already exist, refuse duplicate")
 report["existingBuildingActorsRetained"]=len(building)
 report["existingRoadsRetained"]=len(existing)+len(oldexp)+len(oldb2)
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP_FILE,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(MAP_FILE.read_bytes()).hexdigest():
  raise RuntimeError("Graded map backup checksum invalid")
 def height(e,n):
  h=float(terrain.skarvik_graded_height(e*1000.,n*1000.))
  if not math.isfinite(h) or h<-50 or h>1900:
   raise RuntimeError("Unreal landscape returned invalid height")
  return h
 def avoids_towns(e,n):
  # No new asphalt physically crosses existing 3D blocks or City Sample core.
  for site in settlements:
   if abs(e-site["eastKm"])<site["footprintKm"][0]/2+.012 and abs(n-site["northKm"])<site["footprintKm"][1]/2+.012:
    return False
  return True
 def tiles(route):
  approved=[]
  for p0,p1 in zip(route["waypointsKm"],route["waypointsKm"][1:]):
   d=math.hypot((p1[0]-p0[0])*1000.,(p1[1]-p0[1])*1000.)
   if d<12:continue
   divisions=int(math.ceil(d/19.))
   for k in range(divisions):
    a=k/divisions;b=(k+1)/divisions
    e0=p0[0]+(p1[0]-p0[0])*a;n0=p0[1]+(p1[1]-p0[1])*a
    e1=p0[0]+(p1[0]-p0[0])*b;n1=p0[1]+(p1[1]-p0[1])*b
    length=math.hypot((e1-e0)*1000.,(n1-n0)*1000.)
    ce=(e0+e1)/2;cn=(n0+n1)/2
    if not all(avoids_towns(e,n) for e,n in ((e0,n0),(ce,cn),(e1,n1))):
     approved.append(None);continue
    h0=height(e0,n0);h1=height(e1,n1);hmid=height(ce,cn)
    if abs(h1-h0)/max(length,.01)>.13 or abs((h0+h1)/2-hmid)>0.8:
     approved.append(None);continue
    # Crossing grade checks, not yet a proof of no water/bridge need.
    de=(e1-e0)*1000./length;dn=(n1-n0)*1000./length
    if abs(height(ce-dn*.003,cn+de*.003)-height(ce+dn*.003,cn-de*.003))>1.4:
     approved.append(None);continue
    approved.append((ce,cn,hmid,length,de,dn,h0,h1))
  return approved
 for route_id in APPROVED:
  route=roads[route_id]
  candidates=tiles(route)
  good=[entry for entry in candidates if entry is not None]
  coverage=len(good)/max(len(candidates),1)
  if len(good)<16 or coverage<0.70:
   report["routes"].append({"id":route_id,"state":"BLOCKED_STEEP_OR_SETTLEMENT_CROSSING",
                             "surveyedTiles":len(candidates),"gradeApprovedTiles":len(good),
                             "coverageFraction":round(coverage,3)})
   continue
  placed=0;distance=0.0
  for i,element in enumerate(candidates):
   if element is None:continue
   ce,cn,hmid,span,de,dn,h0,h1=element
   origin_bottom=(bounds.origin.z-bounds.box_extent.z)/100.
   actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
             unreal.Vector(ce*100000.,-cn*100000.,(hmid-origin_bottom+.05)*100.))
   if not actor:raise RuntimeError("Native road actor spawn failed on "+route_id)
   actor.set_actor_label("SKARVIK_EXPANSION_C3_ROAD_{}_{}".format(route_id,i))
   actor.tags=[unreal.Name("SKARVIK_REAL_ROAD_EXPANSION"),unreal.Name(route_id)]
   component=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not component or not component.set_static_mesh(mesh):
    raise RuntimeError("Native asphalt mesh assignment failed")
   component.set_collision_profile_name("BlockAll")
   yaw=math.degrees(math.atan2(-dn,de))
   pitch=math.degrees(math.atan2(h1-h0,span))
   actor.set_actor_rotation(unreal.Rotator(pitch,yaw,0),False)
   actor.set_actor_scale3d(unreal.Vector(span/dims[0],7.5/dims[1],1.))
   placed+=1;distance+=span
  report["routes"].append({"id":route_id,"state":"REAL_MESH_ACTORS_SAVED_NOT_DRIVEN",
    "realRoadActors":placed,"realRoadSurfaceMetres":round(distance,1),
    "approvedTileFraction":round(coverage,3),
    "gapCount":len(candidates)-len(good),"roadNetworkConnectedInEngine":False})
  report["additionalRoadMeshActors"]+=placed
  report["additionalRouteCount"]+=1
  report["newRoadSurfaceMetres"]+=distance
  unreal.log("SKARVIK_ROAD_EXPANSION_ROUTE={} nativeActors={} lengthM={:.1f}".format(route_id,placed,distance))
 if report["additionalRouteCount"]<10 or report["additionalRoadMeshActors"]<350:
  raise RuntimeError("Fewer than 10 safely graded actual road routes in this batch; refuse completion")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Could not persist native added asphalt World Partition actors")
 for protected in (ORIGINAL,PREV):
  if hashlib.sha256(protected.read_bytes()).hexdigest()!=prior[str(protected)]:
   raise RuntimeError("Protected original map unexpectedly altered")
 report["newRoadSurfaceMetres"]=round(report["newRoadSurfaceMetres"],1)
 report["newBatchCandidateRoadIds"]=list(APPROVED)
 report["previousExpansionActorsRetained"]=len(oldexp)+len(oldb2)
 report["newBatchName"]="C3"
 report["fullCityOrRoadNetworkPlaytested"]=False
 report["state"]="BATCH_C3_NATIVE_ASPHALT_EXPANSION_SAVED_NOT_DRIVEN"
 report["nativeWorldSaved"]=True
 unreal.log("SKARVIK_REAL_NATIVE_ROAD_EXPANSION_SAVED="+str(report["additionalRoadMeshActors"]))
except Exception as exc:
 report["error"]=str(exc);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_REAL_NATIVE_ROAD_EXPANSION_FAILED="+str(exc))
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
