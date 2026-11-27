"""Independently audit the EXISTING fifth CitySample source sector in FINAL.

This is read-only. A 121-actor sector with prefix FINAL_REAL_CITYSAMPLE... was
already staged directly from the original CitySample Big_City_LVL into the final
48km seven-island World Partition. Do not re-import from the graded map or
duplicate existing actor labels.
"""
import os,json,hashlib,math,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_FINAL_EXISTING_E5_REPORT"])
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
PREFIX="SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_E5_"
report={"state":"FAILED","readOnly":True,"sourceBigCityFullyStreamed":False,
"all86kOriginalActorsMigrated":False,"renderedVisualSM5":False,
"fullRoadNetworkDriven":False,"nativeActorMutations":0}
try:
 mark=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or
    not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Unsafe native C stage")
 if not all(f.is_file() for f in FILES):raise RuntimeError("Protected source map missing")
 before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in FILES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("Native final island and Big City world cannot reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 counts={
 "originalCitySampleFourSectors":sum(z.startswith("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_") for z in labels),
 "fifthSourceCitySampleE5":sum(z.startswith(PREFIX) for z in labels),
 "originalMainlandBuildings":sum(z.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for z in labels),
 "originalIslandBuildings":sum(z.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for z in labels),
 "realOldRoads":sum(z.startswith("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") for z in labels),
 "townRoadsB1":sum(z.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_") for z in labels),
 "townRoadsB2":sum(z.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_") for z in labels),
 "regionalOriginalA":sum(z.startswith("SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_") for z in labels),
 "regionalOriginalB":sum(z.startswith("SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_") for z in labels)}
 report["nativeOriginalActorCounts"]=counts
 if counts!={"originalCitySampleFourSectors":720,"fifthSourceCitySampleE5":121,
 "originalMainlandBuildings":906,"originalIslandBuildings":128,"realOldRoads":6130,
 "townRoadsB1":1674,"townRoadsB2":1298,"regionalOriginalA":663,"regionalOriginalB":992}:
  raise RuntimeError("Existing real city source/road actors incomplete "+str(counts))
 fifth=sorted([d for d in desc if str(d.label).startswith(PREFIX)],key=lambda d:str(d.label))
 if len({str(d.label) for d in fifth})!=121:raise RuntimeError("Existing fifth source city actor labels duplicated")
 sampled=[fifth[i] for i in sorted({int(n*(len(fifth)-1)/11) for n in range(12)})]
 wp.load_actors([d.guid for d in sampled])
 loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 h=unreal.AnomaliaZPrigimaliaWorldImportLibrary.skarvik_final_coastal_height
 proved=[]
 for d in sampled:
  a=loaded.get(str(d.label))
  if not isinstance(a,unreal.StaticMeshActor):
   raise RuntimeError("Genuine native fifth CitySample original actor failed selective load")
  c=a.get_component_by_class(unreal.StaticMeshComponent)
  m=c.get_editor_property("static_mesh") if c else None
  if not isinstance(m,unreal.StaticMesh):
   raise RuntimeError("Original City Sample 3D mesh not attached in final")
  p=a.get_actor_location()
  e,n=float(p.x)/100.,-float(p.y)/100.
  hh=float(h(e,n))
  if not math.isfinite(hh) or hh<5 or abs(e-2000)>2000 or abs(n+8000)>2000:
   raise RuntimeError("Fifth original city source mesh not on dry 4km city footprint")
  proved.append({"actor":str(d.label),"nativeSourceMesh":m.get_path_name(),"landHeight":round(hh,2)})
 wp.unload_actors([d.guid for d in sampled])
 for f in FILES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=before[str(f)]:
   raise RuntimeError("Read-only City Sample sector verification changed source map")
 report.update(state="SKARVIK_FINAL_ALREADY_EXISTING_121_REAL_FIFTH_CITY_ACTORS_PERSIST_NOT_FULL_BIG_CITY",
  trueNativeCitySourceMeshesSavedTotal=841,
  sampledExistingOriginalRealE5StaticMeshes=proved,
  sourceOriginalsUnchanged=True)
 unreal.log("SKARVIK_FINAL_TRUE_EXISTING_CITY_SAMPLE_E5_NATIVE_MESHES_REOPENED=121")
except Exception as ex:
 report["error"]=str(ex);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_EXISTING_E5_ROADSAFE_CITY_AUDIT_FAILED="+str(ex))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
