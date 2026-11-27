"""Native CitySample downtown slice -- original real building/roof/streets meshes.

Source Big City has ~86k World Partition actors, loading all is unsafe.
Select <=25 source building/roof/street actors near local origin, preserve real
meshes/material source paths and component world transforms. Place <=180 actual
mesh components into C-only graded SKARVIK at its reserved CitySample location.
This is a *small visible district pilot*, NOT the complete 4x4km City Sample.
"""
from pathlib import Path
import hashlib,json,math,os,shutil,traceback
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE="/Game/Map/Big_City_LVL"
TARGET="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
MAP=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
OLD=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
BACKUP=ROOT/"Saved/SkarvikCity/VisibleBigCitySampleDistrictB2_20261101/graded-before-second-real-city-block.umap"
OUT=Path(os.environ["SKARVIK_VISIBLE_CITY_DISTRICT_B2_REPORT"])
LABEL="SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_"
ANCHORED_REFERENCE="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
report={"state":"FAILED","sourceWorld":SOURCE,"targetWorld":TARGET,
   "sourceActorCountSampled":0,"realStaticMeshActorsSaved":0,
   "trueOriginalSourceAssetsReused":False,"fullBigCity4x4KmImported":False,
   "fullCitySourceActorCellsLoaded":False,"npcsOrTrafficEnabled":False,
   "visuallyRenderedInSM5":False,"realBuildingsWithInteriorGameplayVerified":False,
   "roadsDriveabilityVerified":False,"originalDModified":False,
   "BigCityOriginalModified":False,"realMeshSources":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
   ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted C stage marker")
 for f in (CITY,MAP,OLD,D):
  if not f.is_file():raise RuntimeError("Required native map missing "+str(f))
 if BACKUP.exists():raise RuntimeError("City slice attempted before; refuse duplicate placement")
 protected={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (CITY,OLD,D)}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 wp=unreal.WorldPartitionBlueprintLibrary
 if not levels.load_level(SOURCE):raise RuntimeError("Failed to open real City Sample source")
 descs=wp.get_actor_descs() or []
 if len(descs)<80000:raise RuntimeError("Original City Sample World Partition source unexpectedly absent")
 candidates=[]
 for d in descs:
  label=str(d.label)
  group=("building" if label.startswith("BLDG_N") and "COLL" not in label else
         "roof" if label.startswith("BLDG_ROOFGEO") else
         "street" if label.startswith("STREET_FURNITURE_") else None)
  if not group:continue
  b=d.bounds
  cx=(float(b.min.x)+float(b.max.x))/2
  cy=(float(b.min.y)+float(b.max.y))/2
  if math.hypot(cx,cy)<45000 or math.hypot(cx,cy)>95000:continue
  if max(float(b.max.x-b.min.x),float(b.max.y-b.min.y))>25000:continue
  candidates.append((math.hypot(cx,cy),group,label,d))
 chosen=[]
 bycategory={"building":0,"roof":0,"street":0}
 targets={"building":12,"roof":7,"street":5}
 for _,grp,label,d in sorted(candidates,key=lambda x:x[0]):
  if bycategory[grp]>=targets[grp]:continue
  bycategory[grp]+=1;chosen.append((grp,label,d))
  if sum(bycategory.values())>=sum(targets.values()):break
 if bycategory["building"]<3 or bycategory["roof"]<1:
  raise RuntimeError("Not enough real CitySample buildings and roofs near original city center")
 wp.load_actors([d.guid for _,_,d in chosen])
 srcactors=actors.get_all_level_actors()
 srclabels={a.get_actor_label():a for a in srcactors}
 parts=[]
 for group,label,d in chosen:
  actor=srclabels.get(label)
  if not actor:continue
  report["sourceActorCountSampled"]+=1
  for c in actor.get_components_by_class(unreal.StaticMeshComponent):
   if len(parts)>=180:break
   obj=c.get_editor_property("static_mesh")
   if not isinstance(obj,unreal.StaticMesh):continue
   source_path=obj.get_path_name()
   # For instanced static mesh components, sample a strictly bounded number
   # of real source instances, not just its shared origin.
   if isinstance(c,unreal.InstancedStaticMeshComponent):
    n=min(int(c.get_instance_count()),8)
    transforms=[c.get_instance_transform(j,world_space=True) for j in range(n)]
   else:
    transforms=[c.get_world_transform()]
   for trans in transforms:
    if len(parts)>=180:break
    loc=trans.translation
    if not all(math.isfinite(float(x)) for x in (loc.x,loc.y,loc.z)):continue
    if math.hypot(loc.x,loc.y)<45000 or math.hypot(loc.x,loc.y)>115000:continue
    parts.append((group,label,source_path,trans))
 if len(parts)<15:raise RuntimeError("Insufficient real CitySample actor mesh parts to form a visible pilot")
 # Never mutate the original source city. Only switch to C stage target world.
 if not levels.load_level(TARGET):raise RuntimeError("Real graded 48km SKARVIK failed to reopen")
 olddescs=wp.get_actor_descs() or []
 labels=[str(d.label) for d in olddescs]
 if sum(x.startswith("SKARVIK_GRADED_SITE_") for x in labels)!=1039:
  raise RuntimeError("1039 existing real town building actors absent")
 if sum(x.startswith("SKARVIK_GRADED_ROAD_") for x in labels)!=126 or (
    sum(x.startswith("SKARVIK_EXPANSION_ROAD_") for x in labels)!=1668) or (
    sum(x.startswith("SKARVIK_EXPANSION_B2_ROAD_") for x in labels)!=5157) or (
    sum(x.startswith("SKARVIK_EXPANSION_C3_ROAD_") for x in labels)!=6088):
  raise RuntimeError("Existing 13039 paved road mesh actors missing")
 if sum(x.startswith("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_") for x in labels)!=180:
  raise RuntimeError("Previous 180 real CitySample central blocks no longer persisted")
 if sum(x==ANCHORED_REFERENCE for x in labels)!=1:
  raise RuntimeError("Original Big City source UWorld LevelInstance reference not persisted")
 if any(x.startswith(LABEL) for x in labels):
  raise RuntimeError("CitySample pilot mesh actors already created")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP,BACKUP)
 if hashlib.sha256(MAP.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
  raise RuntimeError("Cannot back up graded map before Big City pilot")
 grade=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 anchorheight=float(grade.skarvik_graded_height(2000.,-8000.))
 # Original source city is built approximately at Z=0. Move its city plane
 # onto the actual SKARVIK center grade. Apply no scale modification.
 adjustment=unreal.Vector(200000.,800000.,anchorheight*100.)
 for i,(group,label,path,source_trans) in enumerate(parts):
  obj=unreal.EditorAssetLibrary.load_asset(path)
  if not isinstance(obj,unreal.StaticMesh):raise RuntimeError("Source CitySample mesh package missing "+path)
  original=source_trans.translation
  p=unreal.Vector(original.x+adjustment.x,original.y+adjustment.y,original.z+adjustment.z)
  newactor=actors.spawn_actor_from_class(unreal.StaticMeshActor,p)
  if not newactor:raise RuntimeError("Native world could not spawn genuine building actor")
  newactor.set_actor_label(LABEL+group.upper()+"_"+str(i).zfill(4))
  newactor.tags=[unreal.Name("SKARVIK_BIGCITY_REAL_SOURCE_MESH"),unreal.Name("CITYSAMPLE_SOURCE_COMPONENT")]
  component=newactor.get_component_by_class(unreal.StaticMeshComponent)
  if not component or not component.set_static_mesh(obj):
   raise RuntimeError("Could not assign real original City Sample static mesh")
  component.set_collision_profile_name("BlockAll")
  rot=source_trans.rotation
  transform=unreal.Transform()
  transform.translation=p
  transform.rotation=rot
  transform.scale3d=source_trans.scale3d
  newactor.set_actor_transform(transform,False,True)
  report["realStaticMeshActorsSaved"]+=1
  report["realMeshSources"].append({"kind":group,"originalActor":label,"mesh":path})
 if report["realStaticMeshActorsSaved"]<15:raise RuntimeError("Fewer than 18 native source meshes placed")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("City sample real mesh district pilot failed to save")
 for f in (CITY,OLD,D):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=protected[str(f)]:
   raise RuntimeError("Protected original source modified")
 report["cityCenterKm"]=[2.,-8.]
 report["sourceActorGroups"]=bycategory
 report["trueOriginalSourceAssetsReused"]=True
 report["state"]="REAL_CITY_SAMPLE_SECOND_DISTRICT_NATIVE_MESHES_SAVED_WITH_PREVIOUS_BIG_CITY_NOT_FULL_CITY"
 unreal.log("SKARVIK_REAL_CITY_SAMPLE_STATIC_MESH_ACTORS_SAVED="+str(report["realStaticMeshActorsSaved"]))
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_REAL_CITY_SAMPLE_MESH_CORE_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
