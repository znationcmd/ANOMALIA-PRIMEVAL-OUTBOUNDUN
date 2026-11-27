r"""Native proof: place REAL City Sample road static meshes on a few SKARVIK
connections in an isolated World Partition overlay, never in the original city.
This tests geometry and the height sampler; does not prove drivable 48km roads.
"""
import json,math,os,traceback,hashlib,shutil
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
FILE=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
BACKUP=ROOT/"Saved/SkarvikCity/BeforeGradedRoadMeshes/graded-with-houses-no-roads.umap"
PROTECTED=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
OLD_MAP=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
OUT=Path(os.environ["SKARVIK_ROADS_PILOT_REPORT"])
PLAN=Path(os.environ["SKARVIK_ROADS_PILOT_LAYOUT"])
ROUTES=["SK-RX-001","SK-RX-067","SK-RX-155"]
ASSETS={"secondary":"/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road",
        "local":"/Game/Road/Kit_City_Road/SM_ROAD_19_5_0_0_road"}
report={"status":"FAILED","mapPackage":MAP,"routes":[],
 "physicalRoadMeshCount":0,"lengthMeters":0.0,"skippedSteepChunks":0,
 "originalDModified":False,"skarvikTerrainModified":False,"bigCityModified":False,
 "roadNetworkFullyConstructed":False,"SM5VehicleDriveTestPassed":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Unsafe project root")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Stage marker invalid")
 if not (ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap").is_file():
  raise RuntimeError("SKARVIK landscape stage absent")
 if not Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
  raise RuntimeError("Protected D original not found")
 if not FILE.is_file() or not unreal.EditorAssetLibrary.does_asset_exist(MAP):
  raise RuntimeError("Verified graded native 48km world missing; refuse modification")
 if BACKUP.exists():raise RuntimeError("Graded 3-route pilot already attempted; refuse duplication")
 if not OLD_MAP.is_file():raise RuntimeError("Original 48km stage V1 must remain unchanged")
 protected_hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (PROTECTED,OLD_MAP)}

 if any((ROOT/"Content"/x).exists() for x in ("Crowd","Vehicle")):
  raise RuntimeError("Do not import CitySample crowd or vehicle simulation")
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(data["roads"])!=382 or len(data["settlements"])!=125:
  raise RuntimeError("Expected checked 382-road / 125-town source layout")
 chosen={route["id"]:route for route in data["roads"] if route.get("id") in ROUTES}
 if set(chosen)!=set(ROUTES):raise RuntimeError("Approved first three road routes are absent")
 native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(native,"skarvik_graded_height"):
  raise RuntimeError("Native road height sampler missing")
 meshes={}
 for kind,path in ASSETS.items():
  obj=unreal.EditorAssetLibrary.load_asset(path)
  if not isinstance(obj,unreal.StaticMesh):raise RuntimeError("Real CitySample road mesh absent: "+path)
  b=obj.get_bounds()
  dimensions=[2*b.box_extent.x/100.,2*b.box_extent.y/100.,2*b.box_extent.z/100.]
  if not (17.<dimensions[0]<23. and 5.<dimensions[1]<15.):
   raise RuntimeError("Source road mesh real dimensions are unexpected: "+str(dimensions))
  meshes[kind]=(obj,b,dimensions)
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels or not actors or not levels.load_level(MAP):
  raise RuntimeError("Unable to reopen verified graded map already populated with real houses")
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 saved_building_descriptors=[d for d in desc if str(d.label).startswith("SKARVIK_GRADED_SITE_")]
 if len(saved_building_descriptors)<1000:
  raise RuntimeError("Graded 124-settlement 3D building geometry not yet present; avoid wrong map")
 if any(str(d.label).startswith("SKARVIK_GRADED_ROAD_") for d in desc):
  raise RuntimeError("A graded road pilot was already authored, no duplicates")
 BACKUP.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(FILE,BACKUP)
 if hashlib.sha256(FILE.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
  raise RuntimeError("Could not back up graded map before road modification")

 def height(east_km,north_km):
  h=float(native.skarvik_graded_height(east_km*1000,north_km*1000))
  if not math.isfinite(h) or h < -100 or h > 2200:raise RuntimeError("Bad terrain height")
  return h
 for road_id in ROUTES:
  r=chosen[road_id];category="secondary" if r["class"]=="secondary" else "local"
  obj,b,dim=meshes[category]
  points=r["waypointsKm"]
  if len(points)!=4:raise RuntimeError("Road does not have four centerline points")
  chunks=0;covered=0.0;steep=0
  for A,B in zip(points,points[1:]):
   x0,y0=A;x1,y1=B
   m=math.hypot((x1-x0)*1000.,(y1-y0)*1000.)
   if m<2.:continue
   divisions=max(1,math.ceil(m/20.))
   for k in range(divisions):
    t0=k/divisions;t1=(k+1)/divisions
    e0=x0+(x1-x0)*t0;n0=y0+(y1-y0)*t0
    e1=x0+(x1-x0)*t1;n1=y0+(y1-y0)*t1
    dc=math.hypot((e1-e0)*1000,(n1-n0)*1000)
    h0=height(e0,n0);h1=height(e1,n1)
    grade=abs(h1-h0)/max(dc,.001)
    if grade>.18:
     steep+=1;report["skippedSteepChunks"]+=1
     continue
    # UE local X = east, Y = minus north. Mesh longitudinal X.
    yaw=math.degrees(math.atan2(-(n1-n0),(e1-e0)))
    pitch=math.degrees(math.atan2(h1-h0,dc))
    ex=(e0+e1)*50000.;ny=-(n0+n1)*50000.
    hmid=height((e0+e1)/2,(n0+n1)/2)
    minmesh=(b.origin.z-b.box_extent.z)/100.
    spawn_z=(hmid-minmesh+0.06)*100.
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(ex,ny,spawn_z))
    if not actor:raise RuntimeError("Could not spawn road actor "+road_id)
    actor.set_actor_label("SKARVIK_GRADED_ROAD_{}_{}".format(road_id,chunks))
    actor.tags=[unreal.Name("SKARVIK_GRADED_ROAD_3"),unreal.Name(road_id)]
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component or not component.set_static_mesh(obj):
     raise RuntimeError("Road mesh assignment failed")
    component.set_collision_profile_name("BlockAll")
    actor.set_actor_rotation(unreal.Rotator(pitch,yaw,0),False)
    actor.set_actor_scale3d(unreal.Vector(dc/dim[0],(8.0 if category=="secondary" else 5.0)/dim[1],1.))
    covered+=dc;chunks+=1;report["physicalRoadMeshCount"]+=1
  report["routes"].append({"id":road_id,"roadClass":category,"realMeshActors":chunks,
   "coveredTerrainMeters":round(covered,1),"skippedSteepChunks":steep,
   "state":"NATIVE_3D_PILOT_SAVED_UNTESTED" if chunks else "NO_SAFE_CHUNKS"})
  report["lengthMeters"]+=covered
  unreal.log("SKARVIK_REAL_ROAD_PILOT_ROUTE={} meshActors={} coveredMeters={} steepRejected={}".format(
   road_id,chunks,round(covered,1),steep))
 if report["physicalRoadMeshCount"]<30:
  raise RuntimeError("Insufficient actual mesh segments, refuse success")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Road level and WP actor packages not saved")
 if not FILE.is_file() or FILE.stat().st_size<1024:
  raise RuntimeError("Graded world file missing after 3-route road placement")
 for src in (PROTECTED,OLD_MAP):
  if protected_hashes[str(src)]!=hashlib.sha256(src.read_bytes()).hexdigest():
   raise RuntimeError("Protected original changed unexpectedly: "+str(src))

 report["status"]="GRADED_48KM_WORLD_WITH_3_REAL_ROAD_SEGMENTS_SAVED_NOT_DRIVEN"
 report["worldPartition"]=True
 report["linkedToActualGradedWorld"]=True
 report["existing124SiteBuildingActorDescriptors"]=len(saved_building_descriptors)
 report["lengthMeters"]=round(report["lengthMeters"],1)
 report["mapFileBytes"]=FILE.stat().st_size
 unreal.log("SKARVIK_REAL_ROAD_PILOT_SAVED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_REAL_ROAD_PILOT_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
