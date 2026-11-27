"""Migrate ONLY verified genuine fifth City Sample sector mesh actors from
graded 48km SKARVIK onto the existing final seven-island coastal World Partition.

Keep the original 4x4km City Sample footprint at scale 1. Never stream all 86k
source actors, never alter D:/ANOMALIA or older city/road assets. Any E5 source
mesh outside the city's agreed square/true dry terrace is rejected for later
urban planning, not force-placed underwater or into protected town geometry.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OLD="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
FINAL="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCE_FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
BACKUP=ROOT/"Saved/SkarvikCity/FinalFifthRealCitySampleDistrictE5_20261101/final-before-fifth-original-city-slice.umap"
OUT=Path(os.environ["SKARVIK_FINAL_E5_CITY_MIGRATION_REPORT"])
SRC_PREFIX="SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_E5_"
DST_PREFIX="SKARVIK_FINAL_CITYSAMPLE_E5_ORIGINAL_MESH_"
report={"state":"FAILED","sourceBigCityFullyStreamed":False,
        "full4x4KmCityPlayable":False,"renderedSM5":False,
        "realVehicleRoadTestsPassed":False,"native3DCityMeshesAdded":0,
        "sourceActorDescriptors":0,"outOfFootprintOrUnsafeRejected":[],
        "sourceMapsModified":False,"actorDuplicatesCreated":False}
try:
 marker=ROOT/".skarvik-ci-stage-marker"
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
   not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Unsafe native staged project")
 if not TARGET.is_file() or any(not f.is_file() for f in SOURCE_FILES):
  raise RuntimeError("Required real original city/graded/island/source map missing")
 if BACKUP.exists():raise RuntimeError("City Sample fifth original sector already attempted; refuse duplicate")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE_FILES}
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(lib,"skarvik_final_coastal_height") or not hasattr(lib,"skarvik_graded_height"):
  raise RuntimeError("Native source/final terrain samplers not built")
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 wp=unreal.WorldPartitionBlueprintLibrary
 if not lv.load_level(OLD):raise RuntimeError("Cannot reopen genuine graded City Sample fifth slice")
 descriptors=[d for d in wp.get_actor_descs() or [] if str(d.label).startswith(SRC_PREFIX)]
 report["sourceActorDescriptors"]=len(descriptors)
 if len(descriptors)!=121:raise RuntimeError("Exact previous fifth native real source district 121 actor count absent")
 data=[]
 for off in range(0,len(descriptors),40):
  chunk=descriptors[off:off+40]
  wp.load_actors([d.guid for d in chunk])
  loaded={a.get_actor_label():a for a in actors.get_all_level_actors()}
  for d in chunk:
   label=str(d.label);actor=loaded.get(label)
   if not actor or not isinstance(actor,unreal.StaticMeshActor):
    raise RuntimeError("Original source fifth city sector not actual native StaticMeshActor")
   comp=actor.get_component_by_class(unreal.StaticMeshComponent)
   mesh=comp.get_editor_property("static_mesh") if comp else None
   if not isinstance(mesh,unreal.StaticMesh):
    raise RuntimeError("Real original City Sample E5 actor mesh absent "+label)
   p=actor.get_actor_location();r=actor.get_actor_rotation();s=actor.get_actor_scale3d()
   overrides=[]
   try:overrides=[m.get_path_name() if m else None for m in comp.get_editor_property("override_materials")]
   except Exception:pass
   data.append({"sourceLabel":label,"mesh":mesh.get_path_name(),
    "locationCm":[float(p.x),float(p.y),float(p.z)],
    "rotation":[float(r.pitch),float(r.yaw),float(r.roll)],
    "scale":[float(s.x),float(s.y),float(s.z)],
    "materials":overrides})
  wp.unload_actors([d.guid for d in chunk])
 if len(data)!=121:raise RuntimeError("Fifth source district native actor batch incomplete")
 oldCityHeight=float(lib.skarvik_graded_height(2000.,-8000.))
 finalCityHeight=float(lib.skarvik_final_coastal_height(2000.,-8000.))
 adjustment=(finalCityHeight-oldCityHeight)*100.
 if not math.isfinite(adjustment) or abs(adjustment)>200000:
  raise RuntimeError("Native 4km Big City plateau Z difference invalid")
 approved=[]
 for item in data:
  e=item["locationCm"][0]/100.;n=-item["locationCm"][1]/100.
  if abs(e-2000.)>2000. or abs(n+8000.)>2000.:
   report["outOfFootprintOrUnsafeRejected"].append({"actor":item["sourceLabel"],"reason":"outside-exact-4km-city-square"})
   continue
  h=float(lib.skarvik_final_coastal_height(e,n))
  if h<5. or not math.isfinite(h):
   report["outOfFootprintOrUnsafeRejected"].append({"actor":item["sourceLabel"],"reason":"ocean-or-invalid-coast"})
   continue
  approved.append(item)
 if len(approved)<15:
  raise RuntimeError("Fewer than 15 true fifth original CitySample mesh actors fit final dry city 4x4km footprint")
 if not lv.load_level(FINAL):raise RuntimeError("Cannot reopen populated final coast after source read")
 labels=[str(d.label) for d in wp.get_actor_descs() or []]
 for prefix,required in (
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298),
  ("SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_",663),
  ("SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_",992)):
  if sum(z.startswith(prefix) for z in labels)!=required:
   raise RuntimeError("Previous source houses, City Sample or real asphalt was lost: "+prefix)
 if any(z.startswith(DST_PREFIX) for z in labels):
  raise RuntimeError("Fifth real city sector already imported, refuse 3D duplication")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(TARGET,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(TARGET.read_bytes()).hexdigest():
  raise RuntimeError("Cannot checksum backup of true final native world")
 models={};materials={}
 for idx,item in enumerate(approved):
  p=item["locationCm"];meshpath=item["mesh"]
  if meshpath not in models:
   models[meshpath]=unreal.EditorAssetLibrary.load_asset(meshpath)
   if not isinstance(models[meshpath],unreal.StaticMesh):
    raise RuntimeError("Original fifth City Sample native static mesh asset missing")
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,
      unreal.Vector(p[0],p[1],p[2]+adjustment))
  if not a:raise RuntimeError("Fifth original native city actor spawn failed")
  a.set_actor_label(DST_PREFIX+str(idx).zfill(4))
  a.tags=[unreal.Name("SKARVIK_FINAL_CITYSAMPLE_FIFTH_AUTHENTIC_3D_SECTOR"),
          unreal.Name("CITY_SAMPLE_FULL_4KM_NOT_LOADED")]
  c=a.get_component_by_class(unreal.StaticMeshComponent)
  if not c or not c.set_static_mesh(models[meshpath]):
   raise RuntimeError("Real fifth city source StaticMesh assignment failed")
  c.set_collision_profile_name("BlockAll")
  for j,path in enumerate(item["materials"]):
   if not path or not (path.startswith("/Game/") or path.startswith("/Engine/")):continue
   if path not in materials:materials[path]=unreal.EditorAssetLibrary.load_asset(path)
   if materials[path]:c.set_material(j,materials[path])
  rot=item["rotation"];size=item["scale"]
  a.set_actor_rotation(unreal.Rotator(*rot),False)
  a.set_actor_scale3d(unreal.Vector(*size))
  report["native3DCityMeshesAdded"]+=1
 if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Native 4km fifth city real mesh save failed")
 for f in SOURCE_FILES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=before[str(f)]:
   raise RuntimeError("Protected original graded City Sample or D map was modified")
 report.update(state="SKARVIK_FINAL_FIFTH_SOURCE_CITYSAMPLE_SECTOR_REAL_MESHES_SAVED_PARTIAL_CITY",
  originalSourceCityMeshActors=121,
  sourceMapsModified=False,
  partialFifthSectorNotFullCity=True,
  realMeshTypes=len(models),
  previouslyMigratedCityMeshesPreserved=720,
  genuineCityTotalNowSaved=720+len(approved),
  fullCitySourceApproxActorCountNotMigrated=86608,
  nativeCityFootprintKm=[4,4],
  world=FINAL)
 unreal.log("SKARVIK_FINAL_REAL_FIFTH_CITY_SOURCE_MESHES_SAVED="+str(len(approved)))
except Exception as exc:
 report["error"]=str(exc);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_CITY_SAMPLE_E5_NATIVE_MIGRATION_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
