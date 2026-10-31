"""Safely install a tiny native road-mesh pilot into isolated C: SKARVIK v1.
Roads beyond the pilot remain route-plan only. No CitySample traffic or crowds.
Never alter D: or overwrite existing UE world assets without explicit stage marker.
"""
from pathlib import Path
import hashlib,json,math,os,shutil,traceback
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
stage="/Game/Maps/PRIGIMALIA_SKARVIK_CITY_v1"
world_file=root/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
old_map=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
layout_file=Path(os.environ["SKARVIK_ROAD_MASTERPLAN"])
report_file=Path(os.environ["SKARVIK_NATIVE_ROAD_PILOT_REPORT"])
backup=root/"Saved/SkarvikRoadPilot/pre-road-pilot-20261031.umap"
result=dict(state="FAILED",realStaticMeshActorsSaved=0,lengthMetres=0,
            projectMap=stage,citySampleOriginalModified=False,otherMapsModified=False,
            SM5DrivingValidated=False,completeNetworkBuilt=False)
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(root).upper():
  raise RuntimeError("Only isolated C stage allowed")
 if (root/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Incorrect stage marker")
 if not old_map.is_file() or not world_file.is_file():raise RuntimeError("Protected world files missing")
 if any((root/"Content"/x).exists() for x in ("Crowd","Vehicle")):raise RuntimeError("Excluded City Sample simulation folders present")
 if backup.exists():raise RuntimeError("Pilot has already been attempted, refuse overwrite")
 layout=json.loads(layout_file.read_text(encoding="utf-8"))
 if len(layout["roads"])!=382 or len(layout["settlements"])!=125:
  raise RuntimeError("Expected verified 125/382 world layout")
 terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(terrain,"skarvik_city_height"):raise RuntimeError("Native height function unavailable")
 path="/Game/Road/Kit_City_Road/SM_ROAD_19_20_0_0_road"
 mesh=unreal.EditorAssetLibrary.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Genuine City Sample road mesh missing")
 bounds=mesh.get_bounds()
 # Measured 20x21m source: X is roadway width, Y is roadway length.
 width_m=2*float(bounds.box_extent.x)/100.
 length_m=2*float(bounds.box_extent.y)/100.
 if not (19<width_m<22 and 19<length_m<23):
  raise RuntimeError("Unexpected road geometry extents: {},{}".format(width_m,length_m))
 tile_len=10.0
 xscale=7.5/width_m
 yscale=tile_len/length_m
 zscale=1.0
 min_z_m=(float(bounds.origin.z)-float(bounds.box_extent.z))/100.
 base_old=hashlib.sha256(old_map.read_bytes()).hexdigest()
 baseline=hashlib.sha256(world_file.read_bytes()).hexdigest()
 # Backup C map exactly, but do not touch original D.
 backup.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(world_file,backup)
 if hashlib.sha256(backup.read_bytes()).hexdigest()!=baseline:
  raise RuntimeError("Stage map backup integrity failure")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(stage):raise RuntimeError("Cannot load actual staged SKARVIK v1")
 if any(a.get_actor_label().startswith("SKARVIK_ROUTE_PILOT_") for a in actors.get_all_level_actors()):
  raise RuntimeError("Previous pilot road actors found, refuse overwrite")
 def geoheight(x,y):return float(terrain.skarvik_city_height(x,y))
 def tiles_for(route):
  points=route["waypointsKm"]
  candidates=[]
  for seg_id,(u,v) in enumerate(zip(points,points[1:])):
   sx,sy=u[0]*1000,u[1]*1000
   dx,dy=(v[0]-u[0])*1000,(v[1]-u[1])*1000
   D=math.hypot(dx,dy)
   if D<tile_len:continue
   ux,uy=dx/D,dy/D
   sides=(-uy,ux)
   for i in range(int(D//tile_len)):
    t=(i+.5)*tile_len
    x,y=sx+t*ux,sy+t*uy
    h=[
      geoheight(x+ox*ux+oy*sides[0],y+ox*uy+oy*sides[1])
      for ox in (-tile_len*.5,tile_len*.5) for oy in (-4.,4.)
    ]
    max_delta=max(h)-min(h)
    if max_delta>1.4 or not all(-50<v<1800 for v in h):
     candidates.append(None)
     continue
    candidates.append((x,y,ux,uy,max(h),max_delta))
  best=[];current=[]
  for t in candidates+[None]:
   if t is None:
    if len(current)>len(best):best=current
    current=[]
   else:current.append(t)
  return best
 good_routes=[]
 for route in layout["roads"]:
  if not route.get("id","").startswith("SK-RX-"):continue
  if route["estimatedAlignmentKm"]>3.:
   continue
  good=tiles_for(route)
  if len(good)>=30:
   good_routes.append((route,good))
  if len(good_routes)>=1:break
 if not good_routes:
  raise RuntimeError("No level/continuous 300m of road: refuse floating road meshes")
 route,tiles=good_routes[0]
 for i,(e,n,ux,uy,height,grade) in enumerate(tiles[:60]):
  pos=unreal.Vector(e*100,-n*100,(height-min_z_m*zscale)*100)
  actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,pos)
  if not actor:raise RuntimeError("Native road actor failed")
  actor.set_actor_label("SKARVIK_ROUTE_PILOT_{}_{}".format(route["id"],i))
  actor.tags=[unreal.Name("SKARVIK_ROUTE_PILOT"),unreal.Name("SKARVIK_REAL_ROAD_MESH")]
  comp=actor.get_component_by_class(unreal.StaticMeshComponent)
  if not comp or not comp.set_static_mesh(mesh):raise RuntimeError("Native road mesh unavailable")
  comp.set_collision_profile_name("BlockAll")
  actor.set_actor_scale3d(unreal.Vector(xscale,yscale,zscale))
  yaw=math.degrees(math.atan2(-uy,ux))-90.0
  actor.set_actor_rotation(unreal.Rotator(0,yaw,0),False)
  result["realStaticMeshActorsSaved"]+=1
 result["roadId"]=route["id"]
 result["lengthMetres"]=result["realStaticMeshActorsSaved"]*tile_len
 result["sourceRoadAsset"]=path
 if result["realStaticMeshActorsSaved"]<30:raise RuntimeError("Less than 300m of genuine 3D road placed")
 if not levels.save_all_dirty_levels():raise RuntimeError("Failed saving pilot road actors in C stage")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Failed saving WP actor road packages")
 if hashlib.sha256(old_map.read_bytes()).hexdigest()!=base_old:
  raise RuntimeError("Original D map changed, critical safety issue")
 result["state"]="REAL_ROAD_MESH_PILOT_SAVED_NOT_DRIVEN"
 unreal.log("SKARVIK_NATIVE_ROAD_PILOT_SAVED_MESH_ACTORS={}".format(result["realStaticMeshActorsSaved"]))
except Exception as e:
 result["error"]=str(e);result["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_NATIVE_ROAD_PILOT_FAILED="+str(e))
finally:
 report_file.parent.mkdir(parents=True,exist_ok=True)
 report_file.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
