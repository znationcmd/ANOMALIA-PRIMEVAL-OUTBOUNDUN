"""Reproduce 720 REAL existing City Sample StaticMesh actor components from the
original graded SKARVIK to its new dry 4x4km city plateau in FINAL_v1.
Bounded World Partition source streaming, preserve mesh/material/rotation/scale.
Never stream the 86k Big_City_LVL external actors or pretend complete City Sample.
"""
import os,json,hashlib,math,shutil,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
DEST="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
SOURCES=(
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap")
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/FinalCitySampleSourceMeshMigration20261101/final-before-citysample.umap"
OUT=Path(os.environ["SKARVIK_FINAL_CITYSOURCE_MIGRATION_REPORT"])
DEST_PREFIX="SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_"
PARTS=("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_",
       "SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_",
       "SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_C3_",
       "SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_D4_")
data={"state":"FAILED","copiedOriginalSourceMeshActors":0,
 "sourceOldCitySampleNativeMeshActorCount":0,"copiedCitySamplePartsWithOverrides":0,
 "bigCitySourceWorldPartition86kActorsNotStreamed":True,
 "roadActorsCopied":0,"fullyCitySample4x4kmGameplayValidated":False,
 "sourceMapsNotModified":False,"SM5RenderedAndDriven":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Unapproved C source or marker")
 if not TARGET.is_file() or not all(p.is_file() for p in SOURCES):
  raise RuntimeError("Native original or new world missing")
 if BACKUP.exists():raise RuntimeError("Old City Sample mesh import already attempted")
 checked={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in SOURCES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 wp=unreal.WorldPartitionBlueprintLibrary
 if not lv.load_level(SOURCE):raise RuntimeError("Cannot reopen graded source world")
 desc=wp.get_actor_descs() or []
 chosen=[d for d in desc if any(str(d.label).startswith(p) for p in PARTS)]
 if len(chosen)!=720 or [sum(str(d.label).startswith(p) for d in chosen) for p in PARTS]!=[180]*4:
  raise RuntimeError("720 real CitySample source 3D meshes missing in graded WP map")
 data["sourceOldCitySampleNativeMeshActorCount"]=len(chosen)
 originals=[]
 for offset in range(0,len(chosen),48):
  batch=chosen[offset:offset+48]
  wp.load_actors([d.guid for d in batch])
  loaded={a.get_actor_label():a for a in actors.get_all_level_actors()}
  for d in batch:
   a=loaded.get(str(d.label))
   if not a or not isinstance(a,unreal.StaticMeshActor):
    raise RuntimeError("True source City Sample StaticMeshActor missing "+str(d.label))
   c=a.get_component_by_class(unreal.StaticMeshComponent)
   mesh=c.get_editor_property("static_mesh") if c else None
   if not isinstance(mesh,unreal.StaticMesh):
    raise RuntimeError("No true mesh asset linked for "+str(d.label))
   p=a.get_actor_location()
   rot=a.get_actor_rotation()
   scale=a.get_actor_scale3d()
   overrides=[]
   try:
    materials=c.get_editor_property("override_materials")
    overrides=[m.get_path_name() if m else None for m in materials]
   except Exception:
    overrides=[]
   originals.append({"label":str(d.label),"mesh":mesh.get_path_name(),
       "locationCm":[float(p.x),float(p.y),float(p.z)],
       "rotation":[float(rot.pitch),float(rot.yaw),float(rot.roll)],
       "scale":[float(scale.x),float(scale.y),float(scale.z)],
       "materialOverrides":overrides})
  wp.unload_actors([d.guid for d in batch])
 if len(originals)!=720:raise RuntimeError("CitySample genuine actor data incomplete")
 native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 oldH=float(native.skarvik_graded_height(2000.,-8000.))
 newH=float(native.skarvik_final_coastal_height(2000.,-8000.))
 deltaZ=(newH-oldH)*100.
 if not math.isfinite(deltaZ) or abs(deltaZ)>200000:
  raise RuntimeError("Big City new native terrain height invalid")
 if not lv.load_level(DEST):raise RuntimeError("Final seven-island world cannot reopen")
 labels=[str(d.label) for d in wp.get_actor_descs() or []]
 if any(x.startswith(DEST_PREFIX) for x in labels):
  raise RuntimeError("Actual City Sample actors already copied to final world")
 if sum(x.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for x in labels)<550:
  raise RuntimeError("Real original mainland houses must be migrated before City Sample")
 if sum(x.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for x in labels)<100:
  raise RuntimeError("Real original seven island houses must be migrated before City Sample")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(TARGET,BACKUP)
 if hashlib.sha256(TARGET.read_bytes()).hexdigest()!=hashlib.sha256(BACKUP.read_bytes()).hexdigest():
  raise RuntimeError("Cannot establish final world pre-City Sample backup")
 meshes={};materials={}
 for i,datum in enumerate(originals):
  p=datum["locationCm"]
  e=p[0]/100.;n=-p[1]/100.
  if abs(e-2000.)>2300 or abs(n+8000.)>2300:
   raise RuntimeError("Old city mesh outside original 4x4km city core: "+datum["label"])
  land=float(native.skarvik_final_coastal_height(e,n))
  if land<3.5:
   raise RuntimeError("CitySample building unexpectedly over original ocean "+datum["label"])
  key=datum["mesh"]
  if key not in meshes:
   obj=unreal.EditorAssetLibrary.load_asset(key)
   if not isinstance(obj,unreal.StaticMesh):
    raise RuntimeError("Original CitySample static mesh source unavailable "+key)
   meshes[key]=obj
  new=actors.spawn_actor_from_class(unreal.StaticMeshActor,
        unreal.Vector(p[0],p[1],p[2]+deltaZ))
  if not new:raise RuntimeError("Cannot place CitySample authentic mesh component")
  new.set_actor_label(DEST_PREFIX+str(i).zfill(4))
  new.tags=[unreal.Name("SKARVIK_BIG_CITY_AUTHENTIC_SOURCE_MESH"),
            unreal.Name("SKARVIK_FINAL_NATIVE_BIG_CITY_DRY_PLATEAU")]
  c=new.get_component_by_class(unreal.StaticMeshComponent)
  if not c or not c.set_static_mesh(meshes[key]):
   raise RuntimeError("Cannot assign actual source CitySample StaticMesh")
  c.set_collision_profile_name("BlockAll")
  for ix,mp in enumerate(datum["materialOverrides"]):
   if not mp or not (mp.startswith("/Game/") or mp.startswith("/Engine/")):continue
   if mp not in materials:
    materials[mp]=unreal.EditorAssetLibrary.load_asset(mp)
   if materials[mp]:
    c.set_material(ix,materials[mp])
    data["copiedCitySamplePartsWithOverrides"]+=1
  q=datum["rotation"];size=datum["scale"]
  new.set_actor_rotation(unreal.Rotator(q[0],q[1],q[2]),False)
  new.set_actor_scale3d(unreal.Vector(*size))
  data["copiedOriginalSourceMeshActors"]+=1
 if data["copiedOriginalSourceMeshActors"]!=720:
  raise RuntimeError("Not all four actual CitySample 180 actor sectors copied")
 if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Final authentic CitySample mesh actors failed to save to WP")
 for f in SOURCES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=checked[str(f)]:
   raise RuntimeError("Original source map was modified during read-only City Sample extraction")
 data.update(state="FINAL_SKARVIK_ALL_720_EXISTING_REAL_CITY_SAMPLE_PARTS_MIGRATED_AND_SAVED_NOT_COMPLETE_86K_CITY",
   sourceMapsNotModified=True,bigCityAnchorElevationDeltaMetres=round(deltaZ/100,2),
   uniqueOriginalCityStaticMeshAssets=len(meshes))
 unreal.log("SKARVIK_FINAL_GENUINE_CITY_SAMPLE_MESHES_SAVED=720")
except Exception as exc:
 data["error"]=str(exc);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_BIG_CITY_MIGRATION_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
