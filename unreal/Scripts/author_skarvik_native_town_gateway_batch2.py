"""SKARVIK: pave real UE5 asphalt at safe rural/regional town entrances.

Consumes 24 distinct *audited* gateways, verifies both native terrain grading
and saved World Partition real-building actor bounds before creating complete
small connector + access-lane pairs. If any part of one connector is unsafe,
that entire connector is refused; never leave an isolated partial lane.
Only stages protected C:\ANOMALIAZ_SKARVIK_STAGE_41188816555, never D:.
"""
from pathlib import Path
import hashlib,json,math,os,shutil,traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
MAP=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/Second24RegionalTownGateways20261101/graded-before-gateway.umap"
PLAN=Path(os.environ["SKARVIK_TOWN_GATEWAY_PLAN"])
TRANSPORT=Path(os.environ["SKARVIK_TOWN_GATEWAY_TRANSPORT"])
OUT=Path(os.environ["SKARVIK_TOWN_GATEWAY_RESULT"])
ASSET="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
LABEL="SKARVIK_NATIVE_TOWN_GATEWAY_V2_"
REPORT={"state":"FAILED","world":PKG,"surveyedEntrances":0,
        "nativeCompletedTownEntranceMeshes":0,"nativeTownEntrancesAuthored":0,
        "nativePavedMetres":0.0,"rejectedEntrances":[],"approvedEntrances":[],
        "allLocalTownStreetsConnected":False,"bridgeWaterCrossingsVerified":False,
        "BigCitySourceStreamed":False,"SM5VehicleDriveTestPassed":False,
        "DOriginalModified":False}

try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted stage marker")
 for f in (MAP,ORIGINAL,CITY,V1):
  if not f.is_file():raise RuntimeError("Required protected map absent: "+str(f))
 if BACKUP.exists():raise RuntimeError("Town gateway native batch already attempted; refuse duplicate")
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 if data.get("state")!="TOWN_GATEWAY_BATCH2_SHORT_CANDIDATES_SELECTED_NOT_BUILT" or data.get("selectedCount")!=24:
  raise RuntimeError("Unapproved 24 native gateway source manifest")
 streets=json.loads(TRANSPORT.read_text(encoding="utf-8"))
 townlayouts={s["settlementId"]:s for s in streets["localStreetLayouts"]}
 if len(townlayouts)!=124:raise RuntimeError("Street layout mismatch")
 if data.get("batch")!="second-24-distinct-settlements" or data.get("previouslyAttemptedTownCount")!=24:
  raise RuntimeError("Batch2 source must exclude previous 24 settlement sites")
 if len({i["settlementId"] for i in data["selected"]})!=24:
  raise RuntimeError("Batch2 source has repeated settlement IDs")
 protected={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (ORIGINAL,CITY,V1)}
 terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(terrain,"skarvik_graded_height"):
  raise RuntimeError("Native graded landscape sampler missing")
 mesh=unreal.EditorAssetLibrary.load_asset(ASSET)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Original native road mesh unavailable")
 bounds=mesh.get_bounds()
 width=float(bounds.box_extent.x)*2/100.
 depth=float(bounds.box_extent.y)*2/100.
 if not 17<width<23 or not 5<depth<15:
  raise RuntimeError("Unexpected CitySample road mesh dimensions")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Could not reopen graded 48km SKARVIK")
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 if sum(label.startswith("SKARVIK_GRADED_SITE_") for label in labels)!=1039:
  raise RuntimeError("1039 previous real town 3D mesh actors not present")
 if sum(label.startswith("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_") for label in labels)!=180:
  raise RuntimeError("180 native Big City sample meshes missing")
 if sum(label.startswith("SKARVIK_GRADED_ROAD_") for label in labels)!=126:
  raise RuntimeError("Original road mesh group absent")
 if sum(label.startswith("SKARVIK_EXPANSION_ROAD_") for label in labels)!=1668 or (
    sum(label.startswith("SKARVIK_EXPANSION_B2_ROAD_") for label in labels)!=5157) or (
    sum(label.startswith("SKARVIK_EXPANSION_C3_ROAD_") for label in labels)!=6088):
  raise RuntimeError("Native 13039 old road meshes not preserved")
 if sum(label.startswith("SKARVIK_NATIVE_TOWN_GATEWAY_V1_") for label in labels)!=608:
  raise RuntimeError("Previous verified 608 town gateway road actors absent, refuse second batch")
 if sum(label.startswith("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_") for label in labels)!=180:
  raise RuntimeError("Second City Sample district is not saved in the same native world")
 if any(label.startswith(LABEL) for label in labels):
  raise RuntimeError("Second batch town entrance was already authored, refuse duplicate")
 # Check real saved native WP actor bounding boxes (not only planned footprints).
 # Descriptors for unloaded cells contain the persistent actor bounds in cm.
 buildings=[d.bounds for d in desc if str(d.label).startswith("SKARVIK_GRADED_SITE_")]
 if len(buildings)!=1039:raise RuntimeError("Building bounds unavailable")
 REPORT["existing3DBuildingActorsProtected"]=len(buildings)
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(MAP.read_bytes()).hexdigest():
  raise RuntimeError("Cannot validate original staged map backup SHA256")
 def h(e,n):
  z=float(terrain.skarvik_graded_height(e*1000.,n*1000.))
  if not math.isfinite(z) or z<-50 or z>1900:raise RuntimeError("Invalid graded world height")
  return z
 def blocked_by_building(e,n):
  x=e*100000.;y=-n*100000.
  extra=350.0  # 3.5m from source-building bounds, protects 4.5m asphalt
  return any((box.min.x-extra)<=x<=(box.max.x+extra) and
             (box.min.y-extra)<=y<=(box.max.y+extra) for box in buildings)
 for ix,item in enumerate(data["selected"]):
  REPORT["surveyedEntrances"]+=1
  town=item["settlementId"]
  road=item["roadId"]
  lane=item["accessLaneId"]
  layout=townlayouts.get(town)
  selected=next((s for s in layout["localSegments"] if s["id"]==lane),None) if layout else None
  if not selected or len(selected.get("pointsKm",[]))!=2:
   REPORT["rejectedEntrances"].append({"site":town,"roadId":road,"reason":"planned-local-access-lane-missing"})
   continue
  a=item["regionalRoadEndpointKm"]
  b=item["accessLaneOuterPointKm"]
  points=selected["pointsKm"]
  dx=lambda q:math.hypot((q[0]-b[0])*1000.,(q[1]-b[1])*1000.)
  # Access lane outer endpoint is one of two source points.
  endpoint=min(points,key=dx)
  interior=max(points,key=dx)
  if dx(endpoint)>.3:
   raise RuntimeError("Gateway endpoint does not match source street access lane")
  if math.hypot((a[0]-b[0])*1000,(a[1]-b[1])*1000)>150.1:
   raise RuntimeError("Unexpected long unapproved access gap")
  chain=(a,b,interior)
  segments=[];reason=None
  for p0,p1 in zip(chain,chain[1:]):
   dist=math.hypot((p1[0]-p0[0])*1000.,(p1[1]-p0[1])*1000.)
   pieces=max(1,int(math.ceil(dist/4.5)))
   if dist<.5 or dist>151:
    reason="segment-too-long-or-short";break
   for j in range(pieces):
    t0=j/pieces;t1=(j+1)/pieces
    ea=p0[0]+(p1[0]-p0[0])*t0;na=p0[1]+(p1[1]-p0[1])*t0
    eb=p0[0]+(p1[0]-p0[0])*t1;nb=p0[1]+(p1[1]-p0[1])*t1
    em=(ea+eb)*.5;nm=(na+nb)*.5
    span=math.hypot((eb-ea)*1000.,(nb-na)*1000.)
    if span<.1:reason="degenerate-lane-piece";break
    if any(blocked_by_building(*p) for p in ((ea,na),(em,nm),(eb,nb))):
     reason="persistent-native-building-bounds-collision";break
    ha=h(ea,na);hb=h(eb,nb);hm=h(em,nm)
    if min(ha,hb,hm)<4:
     reason="requires-independent-water-survey";break
    if abs(hb-ha)/span>.12:
     reason="longitudinal-grade-above-12-percent";break
    if abs((ha+hb)*.5-hm)>.16:
     reason="needs-true-local-earthworks";break
    vx=(eb-ea)*1000/span;vy=(nb-na)*1000/span
    cross=(-vy*.002,vx*.002)
    if abs(h(em+cross[0],nm+cross[1])-h(em-cross[0],nm-cross[1]))>.65:
     reason="cross-grade-too-steep";break
    segments.append((em,nm,hm,ha,hb,span,vx,vy))
   if reason:break
  if reason:
   REPORT["rejectedEntrances"].append({"site":town,"roadId":road,"reason":reason})
   continue
  # Do not spawn until every part of the town gateway passes.
  paved=0.
  for j,(em,nm,hm,ha,hb,span,vx,vy) in enumerate(segments):
   zbottom=(float(bounds.origin.z)-float(bounds.box_extent.z))/100.
   actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
              unreal.Vector(em*100000,-nm*100000,(hm-zbottom+.05)*100))
   if not actor:raise RuntimeError("Native road actor spawn failure on "+road)
   actor.set_actor_label(LABEL+town+"_"+road+"_"+str(j))
   actor.tags=[unreal.Name("SKARVIK_REAL_TOWN_ACCESS"),unreal.Name(road)]
   component=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not component or not component.set_static_mesh(mesh):
    raise RuntimeError("Failed assigning authentic City Sample road mesh")
   component.set_collision_profile_name("BlockAll")
   actor.set_actor_rotation(unreal.Rotator(math.degrees(math.atan2(hb-ha,span)),
                    math.degrees(math.atan2(-vy,vx)),0),False)
   actor.set_actor_scale3d(unreal.Vector(span/width,4.5/depth,1.))
   paved+=span
  REPORT["nativeTownEntrancesAuthored"]+=1
  REPORT["nativeCompletedTownEntranceMeshes"]+=len(segments)
  REPORT["nativePavedMetres"]+=paved
  REPORT["approvedEntrances"].append({"road":road,"site":town,"accessLane":lane,
    "physicalMeshActors":len(segments),"nativeAsphaltMetres":round(paved,1),
    "existingTownRingStreetNetworkCompleted":False,"SM5DrivingPassed":False})
  unreal.log("SKARVIK_TOWN_NATIVE_GATEWAY site={} road={} actors={}".format(town,road,len(segments)))
 if REPORT["nativeTownEntrancesAuthored"]<1:
  raise RuntimeError("No safe native town gateway can be constructed; leave native map untouched")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Could not save native gateway actor packages")
 for f in (ORIGINAL,CITY,V1):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=protected[str(f)]:
   raise RuntimeError("Protected production world changed")
 REPORT["nativePavedMetres"]=round(REPORT["nativePavedMetres"],1)
 REPORT["state"]="NATIVE_TOWN_GATEWAY_BATCH2_SHORT_ROAD_SECTIONS_SAVED_NOT_DRIVEN"
 unreal.log("SKARVIK_TOWN_NATIVE_GATEWAY_SAVED="+str(REPORT["nativeTownEntrancesAuthored"]))
except Exception as e:
 REPORT["error"]=str(e);REPORT["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_TOWN_GATEWAY_NATIVE_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
