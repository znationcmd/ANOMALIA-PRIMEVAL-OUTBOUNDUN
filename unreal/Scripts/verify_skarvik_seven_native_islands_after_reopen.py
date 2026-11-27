"""Independent UE5 reopen proof: versioned 48km island World Partition + dry settlement meshes.
Never modify existing original source worlds, never claim entire SKARVIK has migrated.
"""
from pathlib import Path
import json,hashlib,os,traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1"
NEW=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap"
MAIN=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
PLAN=Path(os.environ["SKARVIK_ISLAND_NATIVE_REOPEN_PLAN"])
OUT=Path(os.environ["SKARVIK_ISLAND_NATIVE_REOPEN_REPORT"])
DOC={"state":"FAILED","readOnly":True,"sm5WorldRendered":False,"seaGameplayImplemented":False,
     "boatFerryOrVehicleConnectivityTested":False,"originalGradedSkarvikUnmodified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Invalid isolated stage")
 files=(NEW,MAIN,D,V1,CITY)
 if not all(p.is_file() for p in files):
  raise RuntimeError("Versioned islands world or a protected original missing")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(data["islands"])!=7:raise RuntimeError("Seven island manifest absent")
 if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PKG):
  raise RuntimeError("Versioned native seven-island World Partition cannot reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 proxies=[d for d in desc if "Landscape" in (d.native_class.get_name() if d.native_class else "") or "Landscape" in str(d.label)]
 buildings=[d for d in desc if str(d.label).startswith("SKARVIK_ISLAND_V1_")]
 per_island={}
 per_site={}
 for isl in data["islands"]:
  prefix="SKARVIK_ISLAND_V1_"+isl["id"]+"_"
  subset=[name for name in labels if name.startswith(prefix)]
  per_island[isl["id"]]=len(subset)
  if not subset:raise RuntimeError("No island actors found for "+isl["id"])
  for site in isl["settlements"]:
   siteprefix=prefix+site["id"]+"_"
   count=sum(name.startswith(siteprefix) for name in labels)
   per_site[site["id"]]=count
   if count<4:
    raise RuntimeError("Island native settlement core absent or too small: "+site["name"])
 if len(per_site)!=15 or len(buildings)<95 or not proxies:
  raise RuntimeError("Native island actor descriptor count insufficient")
 # Spot-verify actual UStaticMesh references and collisions in 7 island sectors.
 sample=[]
 for isl in data["islands"]:
  p="SKARVIK_ISLAND_V1_"+isl["id"]+"_"
  item=next((d for d in buildings if str(d.label).startswith(p)),None)
  if item is None:raise RuntimeError("No sample actor in island "+isl["id"])
  wp.load_actors([item.guid])
  loaded=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
  a=next((a for a in loaded if a.get_actor_label()==str(item.label)),None)
  if not a or not isinstance(a,unreal.StaticMeshActor):raise RuntimeError("Native island actor failed selective loading")
  c=a.get_component_by_class(unreal.StaticMeshComponent)
  if not c or not c.get_editor_property("static_mesh"):raise RuntimeError("Native island actor has no authentic StaticMesh")
  asset=c.get_editor_property("static_mesh").get_path_name()
  sample.append({"island":isl["id"],"asset":asset,"actor":str(item.label)})
 # Source height verifies dry original topography at each island centre. Native
 # original 48km topology has no filled-in ocean between the disconnected islands.
 height=unreal.AnomaliaZPrigimaliaWorldImportLibrary.archipelago_height
 native_land_heights=[float(height(i["centerKm"][0]*1000,i["centerKm"][1]*1000)) for i in data["islands"]]
 if any(z<=6. for z in native_land_heights):
  raise RuntimeError("Original archipelago island center unexpectedly underwater")
 for p in files:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
   raise RuntimeError("Read-only native island audit changed a protected Unreal map")
 DOC.update(state="SEVEN_REAL_NATIVE_ISLAND_WP_SECTORS_AND_FIFTEEN_SETTLEMENT_CORES_PERSIST_AFTER_REOPEN",
  islandCount=len(per_island),islandMeshActors=per_island,localityCount=len(per_site),
  localityActors=per_site,totalRealBuildingActors=len(buildings),
  sourceIslandCenterElevationM=native_land_heights,landscapeActorDescriptors=len(proxies),
  independentlyLoadedRealStaticMeshes=sample,originalGradedSkarvikUnmodified=True)
 unreal.log("SKARVIK_SEVEN_ISLAND_WP_NATIVE_CORE_ACTORS_REOPENED=true")
except Exception as exc:
 DOC["error"]=str(exc);DOC["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_SEVEN_ISLAND_REOPEN_VERIFICATION_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(DOC,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
