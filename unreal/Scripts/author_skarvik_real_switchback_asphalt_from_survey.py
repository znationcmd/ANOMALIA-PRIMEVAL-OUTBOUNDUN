"""Construct REAL grade-checked native City Sample asphalt on terrain-aware SKARVIK
switchback proposals previously calculated by UE5 (run 41246316055).
The source artifact is read-only route geometries, not an instruction to skip
safe slope/bounds checks. All placement is isolated C: graded WP map.
"""
from pathlib import Path
import os,json,math,hashlib,shutil,traceback
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
MAPFILE=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/SwitchbackNativeAsphaltV1_20261031/graded-before-switchback.umap"
SOURCE=Path(os.environ["SKARVIK_REAL_SWITCHBACK_APPROVED_REPORT"])
OUT=Path(os.environ["SKARVIK_REAL_SWITCHBACK_NATIVE_REPORT"])
ROAD="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
LABEL="SKARVIK_REAL_SWITCHBACK_V1_"
doc={"state":"FAILED","sourceTerrainProposalOnly":True,"nativeActorCount":0,
 "nativeAsphaltMetres":0.,"newRealSwitchbackGroups":0,
 "unresolvedTerrainGroups":0,"allRoadContinuityConfirmed":False,
 "SM5VehicleDriveabilityVerified":False,"bridgeAndWaterCrossingsVerified":False,
 "CitySampleBigCityFullyLoaded":False,"DOriginalModified":False,"attempts":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted native stage")
 for f in (MAPFILE,D,CITY,V1):
  if not f.is_file():raise RuntimeError("Missing source native world "+str(f))
 if BACKUP.exists():raise RuntimeError("Road switchback native stage already attempted; refuse duplicate")
 proposal=json.loads(SOURCE.read_text(encoding="utf-8"))
 if proposal.get("state")!="SKARVIK_GRADE_SAFE_ROAD_SWITCHBACKS_SURVEYED_WITHOUT_MODIFYING_TERRAIN":
  raise RuntimeError("Untrusted switchback proposals or missing native height survey")
 choices=[x for x in proposal.get("detourGroups",[]) if x.get("detourCenterlineKm")]
 if len(choices)!=7:raise RuntimeError("Survey expected seven candidate switchbacks, got "+str(len(choices)))
 doc["unresolvedTerrainGroups"]=proposal["unresolvedDetourGroups"]
 original_sha={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (D,CITY,V1)}
 terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 mesh=unreal.EditorAssetLibrary.load_asset(ROAD)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Real asphalt static mesh source missing")
 bounds=mesh.get_bounds()
 width=2*float(bounds.box_extent.x)/100
 depth=2*float(bounds.box_extent.y)/100
 if not (17<width<23 and 5<depth<15):raise RuntimeError("Untrusted native asphalt mesh bounds")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(MAP):raise RuntimeError("Cannot open graded World Partition SKARVIK")
 labels=[str(d.label) for d in (unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or [])]
 if sum(l.startswith("SKARVIK_GRADED_SITE_") for l in labels)!=1039:
  raise RuntimeError("Real 1039 settlement building actors missing")
 if sum(l.startswith("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_") for l in labels)!=180:
  raise RuntimeError("180 native Big City source-mesh assets not persisted")
 if sum(l.startswith("SKARVIK_CONTINUITY_PATCH_V1_") for l in labels)!=375:
  raise RuntimeError("Previous 375 genuine road repair meshes missing")
 if any(l.startswith(LABEL) for l in labels):
  raise RuntimeError("Switchback already in native graded world; refuse duplicate")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAPFILE,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(MAPFILE.read_bytes()).hexdigest():
  raise RuntimeError("Switchback pre-save graded world backup corruption")
 def height(e,n):
  value=float(terrain.skarvik_graded_height(e*1000.,n*1000.))
  if not math.isfinite(value) or not -50<value<1900:raise RuntimeError("Invalid native terrain grade")
  return value
 for proposed in choices:
  route=proposed["route"];group=proposed["group"];points=proposed["detourCenterlineKm"]
  if len(points)>1000 or len(points)<3:raise RuntimeError("Invalid source centerline point count")
  if not all(-23.84<p[0]<23.84 and -23.84<p[1]<23.84 for p in points):
   raise RuntimeError("Detour exceeds SKARVIK terrain boundaries")
  segments=[];reason=None
  for p0,p1 in zip(points,points[1:]):
   dist=math.hypot((p1[0]-p0[0])*1000,(p1[1]-p0[1])*1000)
   if dist<.1:continue
   count=max(1,int(math.ceil(dist/5.0)))
   for i in range(count):
    t=(i+.5)/count
    a=i/count;b=(i+1)/count
    e0=p0[0]+(p1[0]-p0[0])*a;n0=p0[1]+(p1[1]-p0[1])*a
    e1=p0[0]+(p1[0]-p0[0])*b;n1=p0[1]+(p1[1]-p0[1])*b
    em=(e0+e1)/2;nm=(n0+n1)/2
    span=math.hypot((e1-e0)*1000,(n1-n0)*1000)
    h0=height(e0,n0);h1=height(e1,n1);hm=height(em,nm)
    if abs(h1-h0)/span>.15:
     reason="native-5m-grade-above-15-percent";break
    if abs((h0+h1)/2-hm)>.20:
     reason="native-mesh-5m-not-planar";break
    vx=(e1-e0)*1000/span;vy=(n1-n0)*1000/span
    side=(-vy*.002,vx*.002)
    if abs(height(em+side[0],nm+side[1])-height(em-side[0],nm-side[1]))>.95:
     reason="native-cross-grade-too-high";break
    segments.append((em,nm,hm,h0,h1,span,vx,vy))
   if reason:break
  if reason or not segments:
   doc["attempts"].append({"route":route,"group":group,"state":"BLOCKED_DO_NOT_PLACE_PARTIAL_ROUTE","reason":reason or "no-segments"})
   continue
  # All path segments approved before spawning; do not create floating partial repairs.
  distance=0
  for i,(em,nm,hm,h0,h1,span,vx,vy) in enumerate(segments):
   zbottom=(float(bounds.origin.z)-float(bounds.box_extent.z))/100.
   actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
             unreal.Vector(em*100000,-nm*100000,(hm-zbottom+.05)*100))
   if not actor:raise RuntimeError("Cannot spawn native asphalt segment for "+route)
   actor.set_actor_label("{}{}_{}_{}".format(LABEL,route,group,i))
   actor.tags=[unreal.Name("SKARVIK_REAL_ROAD_SWITCHBACK"),unreal.Name(route)]
   component=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not component or not component.set_static_mesh(mesh):raise RuntimeError("Real road mesh assignment error")
   component.set_collision_profile_name("BlockAll")
   actor.set_actor_rotation(unreal.Rotator(math.degrees(math.atan2(h1-h0,span)),
                                        math.degrees(math.atan2(-vy,vx)),0),False)
   actor.set_actor_scale3d(unreal.Vector(span/width,4.0/depth,1.))
   distance+=span
  doc["nativeActorCount"]+=len(segments)
  doc["nativeAsphaltMetres"]+=distance
  doc["newRealSwitchbackGroups"]+=1
  doc["attempts"].append({"route":route,"group":group,"state":"REAL_NATIVE_ASPHALT_SWITCHBACK_SAVED_NOT_DRIVEN",
    "actors":len(segments),"nativeRoadMetres":round(distance,2)})
  unreal.log("SKARVIK_REAL_NATIVE_SWITCHBACK_SEGMENTS route={} group={} actors={}".format(route,group,len(segments)))
 if doc["newRealSwitchbackGroups"]<1:
  raise RuntimeError("No grade-compatible switchback proposals can be physically paved")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Failed saving real switchback actor packages into native WP")
 for file in (D,CITY,V1):
  if hashlib.sha256(file.read_bytes()).hexdigest()!=original_sha[str(file)]:
   raise RuntimeError("Protected original changed during switchback")
 doc["nativeAsphaltMetres"]=round(doc["nativeAsphaltMetres"],2)
 doc["state"]="REAL_TERRAIN_SAFE_SWITCHBACK_ASPHALT_ADDED_NOT_YET_DRIVE_TESTED"
 unreal.log("SKARVIK_REAL_NATIVE_SWITCHBACK_GROUPS_SAVED="+str(doc["newRealSwitchbackGroups"]))
except Exception as e:
 doc["error"]=str(e);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_REAL_SWITCHBACK_NATIVE_SAVE_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
