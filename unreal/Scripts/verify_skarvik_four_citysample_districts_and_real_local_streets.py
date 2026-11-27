"""Verify native SKARVIK after fourth real CitySample district and first physical local streets.
This independent, read-only World Partition reopen checks actor descriptors and
selectively loads six actual StaticMeshActors, never all CitySample source cells.
"""
import hashlib, json, os, traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
WORLD="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
OUT=Path(os.environ["SKARVIK_COMBINED_20261101_REPORT"])
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
)
EXPECTED={
 "settlementBuildingMeshes":("SKARVIK_GRADED_SITE_",1039),
 "CitySampleCoreMeshes":("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_",180),
 "CitySampleDistrictB2Meshes":("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_",180),
 "CitySampleDistrictC3Meshes":("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_C3_",180),
 "CitySampleDistrictD4Meshes":("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_D4_",180),
 "first3RouteMeshes":("SKARVIK_GRADED_ROAD_",126),
 "batch20RouteMeshes":("SKARVIK_EXPANSION_ROAD_",1668),
 "batch40B2RouteMeshes":("SKARVIK_EXPANSION_B2_ROAD_",5157),
 "batch37C3RouteMeshes":("SKARVIK_EXPANSION_C3_ROAD_",6088),
 "shortGapRepairMeshes":("SKARVIK_CONTINUITY_PATCH_V1_",375),
 "switchbackRouteMeshes":("SKARVIK_REAL_SWITCHBACK_V1_",142),
 "firstVillageGateways":("SKARVIK_NATIVE_TOWN_GATEWAY_V1_",608),
 "secondVillageGateways":("SKARVIK_NATIVE_TOWN_GATEWAY_V2_",634),
 "firstVillagePerimeterStreets":("SKARVIK_REAL_LOCAL_RING_V2_",54)
}
CITY_LABEL="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
REPORT={"state":"FAILED","readOnly":True,"sourceBigCityAllActorsLoaded":False,
  "CitySampleAllDistrictsVisuallyRendered":False,"SM5DrivingOrGameplayPassed":False,
  "all382RegionalRoadsBuilt":False,"allVillageStreetsBuilt":False,
  "all15MapsReady":False,"protectedOriginalMapsModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Unexpected native project root")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Invalid protected marker")
 for f in FILES:
  if not f.is_file():raise RuntimeError("Missing protected source "+str(f))
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not levels.load_level(WORLD):raise RuntimeError("Actual graded native world failed to reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 descs=wp.get_actor_descs() or []
 names=[str(d.label) for d in descs]
 REPORT["nativeWorldPartitionActorDescriptorCount"]=len(names)
 counts={k:sum(n.startswith(prefix) for n in names)
         for k,(prefix,num) in EXPECTED.items()}
 REPORT["actualSavedActorGroupCounts"]=counts
 for key,(prefix,num) in EXPECTED.items():
  if key=="firstVillagePerimeterStreets":
   if counts[key]<num:raise RuntimeError("Native local-street actors fewer than 54: "+str(counts[key]))
  elif counts[key]!=num:raise RuntimeError("Native actor count mismatch "+key+": got "+str(counts[key])+" expected "+str(num))
 if names.count(CITY_LABEL)!=1:raise RuntimeError("Source Big City LevelInstance reference missing")
 sam=[]
 for key in ("CitySampleDistrictD4Meshes","firstVillagePerimeterStreets"):
  prefix=EXPECTED[key][0]
  sam.extend([d for d in descs if str(d.label).startswith(prefix)][:3])
 if len(sam)!=6:raise RuntimeError("Insufficient selective actor sample")
 wp.load_actors([d.guid for d in sam])
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 loaded={a.get_actor_label():a for a in actors}
 REPORT["sampleRealNativeMeshActors"]=[]
 for d in sam:
  a=loaded.get(str(d.label))
  if not isinstance(a,unreal.StaticMeshActor):raise RuntimeError("Persisted City/road actor is not real StaticMeshActor "+str(d.label))
  c=a.get_component_by_class(unreal.StaticMeshComponent)
  if not c:raise RuntimeError("No native StaticMeshComponent "+str(d.label))
  mesh=c.get_editor_property("static_mesh")
  if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Missing real mesh asset "+str(d.label))
  REPORT["sampleRealNativeMeshActors"].append({"label":str(d.label),"asset":mesh.get_path_name()})
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
   raise RuntimeError("Protected source changed during supposedly read-only reopen")
 REPORT["citySourceLevelInstanceReferenceCount"]=1
 REPORT["all124TownBuildingGroupsPreserved"]=True
 REPORT["CitySampleArchitecturalMeshActorsPreserved"]=720
 REPORT["villageRoadAccessMeshesPreserved"]=1242
 REPORT["realTownLocalStreetMeshes"]=counts["firstVillagePerimeterStreets"]
 REPORT["savedRegionalAndRepairRoadMeshesPreserved"]=13556
 REPORT["state"]="NATIVE_FOUR_CITYSAMPLE_DISTRICTS_AND_REAL_LOCAL_STREETS_PERSIST_AFTER_REOPEN_NOT_DRIVEN"
 unreal.log("SKARVIK_D4_AND_LOCAL_TOWN_STREETS_REOPEN_VERIFIED=true")
except Exception as exc:
 REPORT["error"]=str(exc)
 REPORT["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_C3_AND_39_GATEWAY_REOPEN_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
