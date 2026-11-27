"""Build authentic asphalt street segments from 39 already paved native village gateways.

Each sidewalk-free ring extension is a genuine CitySample StaticMeshActor on the
existing 48km World Partition. It is connected geometrically at the approved
gateway's interior endpoint (which lies on the perimeter ring). The terrain and
persisted house actor bounds reject unsafe road sections. This does not finish
all 992 planned streets or prove SM5 vehicle navigation.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
MAP=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/NativeStreetRingAt39GatewaysRetry2_20261101/graded-before-local-ring.umap"
PLAN=Path(os.environ["SKARVIK_LOCAL_RING_MASTERPLAN"])
FIRST=Path(os.environ["SKARVIK_LOCAL_RING_GATEWAYS_V1"])
SECOND=Path(os.environ["SKARVIK_LOCAL_RING_GATEWAYS_V2"])
OUT=Path(os.environ["SKARVIK_LOCAL_RING_NATIVE_REPORT"])
PREFIX="SKARVIK_REAL_LOCAL_RING_V2_"
ROAD="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
RESULT={"state":"FAILED","realLocalStreetActors":0,"realLocalStreetMetres":0.0,
 "localStreetLegsSaved":0,"settlementsWithFirstRingRoad":0,"attemptedTownSites":0,
 "rejects":[],"approved":[],"all992StreetsBuilt":False,
 "fullCitySampleStreamed":False,"SM5VehicleDrivingVerified":False,
 "roadAndBridgeContinuityVerified":False,"originalDModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Not trusted isolated stage")
 if any(not p.is_file() for p in (MAP,D,CITY,V1)):
  raise RuntimeError("Protected native Unreal map source missing")
 if BACKUP.exists():raise RuntimeError("Native local-ring batch previously attempted")
 layouts=json.loads(PLAN.read_text(encoding="utf-8"))
 if layouts.get("localStreetSegmentCount")!=992 or len(layouts.get("localStreetLayouts",[]))!=124:
  raise RuntimeError("Unapproved local street masterplan")
 receipts=[json.loads(x.read_text(encoding="utf-8")) for x in (FIRST,SECOND)]
 if (receipts[0].get("nativeTownEntrancesAuthored")!=21 or
     receipts[1].get("nativeTownEntrancesAuthored")!=18 or
     receipts[0].get("nativeCompletedTownEntranceMeshes")!=608 or
     receipts[1].get("nativeCompletedTownEntranceMeshes")!=634):
  raise RuntimeError("Prior 39 native village gateways are not attested")
 bysite={}
 for receipt in receipts:
  for row in receipt["approvedEntrances"]:
   if row["site"] in bysite:raise RuntimeError("Duplicate town entrance approval")
   bysite[row["site"]]=row
 if len(bysite)!=39:raise RuntimeError("Expected 39 unique previous connected village sites")
 layouts={x["settlementId"]:x for x in layouts["localStreetLayouts"]}
 original_hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (D,CITY,V1)}
 terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 mesh=unreal.EditorAssetLibrary.load_asset(ROAD)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Original CitySample road mesh absent")
 box=mesh.get_bounds()
 width=2*float(box.box_extent.x)/100.;depth=2*float(box.box_extent.y)/100.
 if not(17<width<23 and 5<depth<15):raise RuntimeError("Road native StaticMesh bounds unsupported")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Cannot load graded WP map")
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(s):return sum(label.startswith(s) for label in labels)
 for prefix,n in (("SKARVIK_GRADED_SITE_",1039),("SKARVIK_NATIVE_TOWN_GATEWAY_V1_",608),
                 ("SKARVIK_NATIVE_TOWN_GATEWAY_V2_",634),
                 ("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_",180),
                 ("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_",180),
                 ("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_C3_",180)):
  if count(prefix)!=n:raise RuntimeError("Saved native geometry changed "+prefix+" expected "+str(n))
 if any(label.startswith("SKARVIK_REAL_LOCAL_RING_V1_") for label in labels):
  raise RuntimeError("First aborted local-ring run unexpectedly produced actors; refuse re-issue")
 if any(label.startswith(PREFIX) for label in labels):
  raise RuntimeError("Local-ring retry road meshes already saved; refuse duplicate")
 building_boxes=[d.bounds for d in desc if str(d.label).startswith("SKARVIK_GRADED_SITE_")]
 if len(building_boxes)!=1039:raise RuntimeError("Building collision descriptor bounds unavailable")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP,BACKUP)
 if hashlib.sha256(MAP.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
  raise RuntimeError("Staged map could not be backed up safely")
 def h(e,n):
  v=float(terrain.skarvik_graded_height(e*1000.,n*1000.))
  if not math.isfinite(v) or not -50<v<1900:raise RuntimeError("Invalid native terrain height")
  return v
 def building_free(e,n):
  x=e*100000.;y=-n*100000.;margin=375
  return not any(b.min.x-margin<=x<=b.max.x+margin and b.min.y-margin<=y<=b.max.y+margin for b in building_boxes)
 approved_sites=set()
 for site,entrance in sorted(bysite.items()):
  RESULT["attemptedTownSites"]+=1
  layout=layouts.get(site)
  if not layout:
   RESULT["rejects"].append({"site":site,"reason":"missing-street-layout"});continue
  gateway=next((x for x in layout["localSegments"] if x["id"]==entrance["accessLane"]),None)
  if not gateway or len(gateway.get("pointsKm",[]))!=2:
   RESULT["rejects"].append({"site":site,"reason":"missing-saved-gateway-source-lane"});continue
  lines=[x for x in layout["localSegments"] if x["id"].startswith(site+"-perimeter-")]
  if len(lines)!=4:raise RuntimeError("Expected four perimeter edges even for village-lane street class: "+site)
  # The end of the local access lane lying on one of 4 perimeter edges.
  p1,p2=gateway["pointsKm"]
  def on_segment(p,a,b):
   cross=abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
   dot=(p[0]-a[0])*(b[0]-a[0])+(p[1]-a[1])*(b[1]-a[1])
   return cross<1.e-6 and -.000001<=dot<=sum((b[j]-a[j])**2 for j in range(2))+.000001
  edge=next(((line,p) for line in lines for p in (p1,p2)
             if on_segment(p,*line["pointsKm"])),None)
  if not edge:
   RESULT["rejects"].append({"site":site,"reason":"gateway-not-on-perimeter"});continue
  line,start=edge; a,b=line["pointsKm"]
  length=math.hypot((b[0]-a[0])*1000,(b[1]-a[1])*1000)
  tangent=((b[0]-a[0])*1000/length,(b[1]-a[1])*1000/length)
  for direction in (-1,1):
   # A short 80m street starts at the actual previously-paved gateway.
   # No claim that the remainder of the huge settlement perimeter is connected.
   e0,n0=float(start[0]),float(start[1])
   e1=e0+direction*tangent[0]*.080
   n1=n0+direction*tangent[1]*.080
   pieces=int(math.ceil(80/4.5))
   steps=[];reject=None
   for i in range(pieces):
    va=i/pieces;vb=(i+1)/pieces
    ea=e0+(e1-e0)*va;na=n0+(n1-n0)*va
    eb=e0+(e1-e0)*vb;nb=n0+(n1-n0)*vb
    em=(ea+eb)*.5;nm=(na+nb)*.5
    dist=math.hypot((eb-ea)*1000,(nb-na)*1000)
    if not all(-23.8<e<23.8 and -23.8<n<23.8 for e,n in ((ea,na),(em,nm),(eb,nb))):
     reject="outside-native-world";break
    if not all(building_free(e,n) for e,n in ((ea,na),(em,nm),(eb,nb))):
     reject="real-house-collision";break
    ha=h(ea,na);hb=h(eb,nb);hm=h(em,nm)
    if min(ha,hb,hm)<4:reject="possible-water-crossing";break
    if abs(hb-ha)/dist>.12:reject="grade-above-12-percent";break
    if abs((ha+hb)*.5-hm)>.16:reject="uneven-road-grade";break
    vx=(eb-ea)*1000/dist;vy=(nb-na)*1000/dist
    ortho=(-vy*.002,vx*.002)
    if abs(h(em+ortho[0],nm+ortho[1])-h(em-ortho[0],nm-ortho[1]))>.65:
     reject="cross-grade";break
    steps.append((em,nm,hm,ha,hb,dist,vx,vy))
   if reject:
    RESULT["rejects"].append({"site":site,"perimeter":line["id"],"side":direction,"reason":reject})
    continue
   paved=0
   for i,(em,nm,hm,ha,hb,dist,vx,vy) in enumerate(steps):
    base=(float(box.origin.z)-float(box.box_extent.z))/100.
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
      unreal.Vector(em*100000.,-nm*100000.,(hm-base+.05)*100.))
    if not actor:raise RuntimeError("Local ring native asphalt spawn failed: "+site)
    actor.set_actor_label("{}{}_{}_{}".format(PREFIX,site,"L" if direction<0 else "R",i))
    actor.tags=[unreal.Name("SKARVIK_REAL_LOCAL_STREET"),unreal.Name("GATEWAY_"+site)]
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not comp or not comp.set_static_mesh(mesh):raise RuntimeError("Local ring real StaticMesh missing")
    comp.set_collision_profile_name("BlockAll")
    actor.set_actor_rotation(unreal.Rotator(math.degrees(math.atan2(hb-ha,dist)),
                    math.degrees(math.atan2(-vy,vx)),0),False)
    actor.set_actor_scale3d(unreal.Vector(dist/width,4.5/depth,1.))
    paved+=dist
   RESULT["approved"].append({"site":site,"perimeterStreetId":line["id"],
     "side":direction,"realMeshActors":len(steps),"pavedMetres":round(paved,1),
     "SM5RoadTrafficVerified":False})
   RESULT["realLocalStreetActors"]+=len(steps)
   RESULT["realLocalStreetMetres"]+=paved
   RESULT["localStreetLegsSaved"]+=1
   approved_sites.add(site)
  unreal.log("SKARVIK_LOCAL_RING_SITE={} legs={}".format(site,len([q for q in RESULT["approved"] if q["site"]==site])))
 RESULT["settlementsWithFirstRingRoad"]=len(approved_sites)
 if RESULT["localStreetLegsSaved"]<3:
  raise RuntimeError("Too few safe real local street extensions, no completion claim")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Native local street meshes failed to persist")
 for file in (D,CITY,V1):
  if hashlib.sha256(file.read_bytes()).hexdigest()!=original_hashes[str(file)]:
   raise RuntimeError("Protected D or Big City native world was modified")
 RESULT["realLocalStreetMetres"]=round(RESULT["realLocalStreetMetres"],1)
 RESULT["state"]="REAL_NATIVE_SHORT_LOCAL_STREETS_AT_EXISTING_GATEWAYS_SAVED_NOT_DRIVEN"
 unreal.log("SKARVIK_NATIVE_LOCAL_RING_STREET_ACTORS_SAVED="+str(RESULT["realLocalStreetActors"]))
except Exception as e:
 RESULT["error"]=str(e);RESULT["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_NATIVE_LOCAL_RING_STREET_SAVE_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
