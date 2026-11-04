"""Read-only persistence proof of SKARVIK 21 access roads & genuine second
CitySample district with all old 48km World Partition actor packages intact.
No extra actors created, source modification, or SM5 driving claims.
"""
from pathlib import Path
import hashlib,json,os,traceback
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
OUT=Path(os.environ["SKARVIK_CITY_AND_TOWN_REOPEN_REPORT"])
FILENAMES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
       ROOT/"Content/Map/Big_City_LVL.umap",
       Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
report={"state":"FAILED","readOnly":True,"all4KmBigCityStreamed":False,
        "SM5VisualTestPassed":False,"vehicleDrivingVerified":False,"originalDModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Unsafe staging project")
 if not all(f.is_file() for f in FILENAMES):raise RuntimeError("Missing protected 48km or City Sample UWorld")
 before={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in FILENAMES}
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not level.load_level(PKG):raise RuntimeError("Native 48km graded WP map did not reopen")
 descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(d.label) for d in descs]
 def count(prefix):return sum(x.startswith(prefix) for x in labels)
 counts={
  "existingTownBuildings":count("SKARVIK_GRADED_SITE_"),
  "existingDowntownCore":count("SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_"),
  "newCitySampleSecondDistrict":count("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_"),
  "bigCityNativeLevelInstanceRef":sum(x=="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1" for x in labels),
  "firstRoadPilotMeshes":count("SKARVIK_GRADED_ROAD_"),
  "batchB1RoadMeshes":count("SKARVIK_EXPANSION_ROAD_"),
  "batchB2RoadMeshes":count("SKARVIK_EXPANSION_B2_ROAD_"),
  "batchC3RoadMeshes":count("SKARVIK_EXPANSION_C3_ROAD_"),
  "roadBaseGapRepairMeshes":count("SKARVIK_CONTINUITY_PATCH_V1_"),
  "roadRealSwitchbackMeshes":count("SKARVIK_REAL_SWITCHBACK_V1_"),
  "newTownGatewayRoadMeshes":count("SKARVIK_NATIVE_TOWN_GATEWAY_V1_")}
 report["persistentNativeActors"]=counts
 expected={"existingTownBuildings":1039,"existingDowntownCore":180,
    "bigCityNativeLevelInstanceRef":1,"firstRoadPilotMeshes":126,
    "batchB1RoadMeshes":1668,"batchB2RoadMeshes":5157,
    "batchC3RoadMeshes":6088,"roadBaseGapRepairMeshes":375,
    "roadRealSwitchbackMeshes":142,"newTownGatewayRoadMeshes":608}
 for key,value in expected.items():
  if counts[key]!=value:
   raise RuntimeError("Native map lost actors {} expected {}, observed {}".format(key,value,counts[key]))
 if counts["newCitySampleSecondDistrict"]<15 or counts["newCitySampleSecondDistrict"]>180:
  raise RuntimeError("Real second Big City source actor mesh district not persisted")
 # Loading only a few source-mesh and road actors proves the actual mesh refs
 # survive deserialization; never activate full CitySample nested World Partition.
 to_load=[d for d in descs if str(d.label).startswith("SKARVIK_NATIVE_TOWN_GATEWAY_V1_")][:4]+[
          d for d in descs if str(d.label).startswith("SKARVIK_CENTRE_REAL_CITYSAMPLE_DISTRICT_B2_")][:4]
 unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in to_load])
 actors={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 physical=[]
 for d in to_load:
  actor=actors.get(str(d.label))
  if not isinstance(actor,unreal.StaticMeshActor):
   raise RuntimeError("Saved CitySample/town gateway actor could not be selectively loaded")
  comp=actor.get_component_by_class(unreal.StaticMeshComponent)
  if not comp or not isinstance(comp.get_editor_property("static_mesh"),unreal.StaticMesh):
   raise RuntimeError("Native UE5 actor has no source original StaticMesh reference")
  physical.append({"label":str(d.label),"mesh":comp.get_editor_property("static_mesh").get_path_name()})
 report["selectivelyReopenedMeshActorProof"]=physical
 for f in FILENAMES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=before[str(f)]:
   raise RuntimeError("Read-only verification changed protected file "+str(f))
 report["state"]="NATIVE_BIGCITY_SECOND_REAL_DISTRICT_AND_21_TOWN_ENTRANCES_PERSIST_REOPEN_NOT_DRIVEN"
 report["pavedTownEntranceCountFromPreviousWorkflow"]=21
 unreal.log("SKARVIK_NATIVE_CITY_AND_GATEWAY_ROADS_REOPENED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_NATIVE_CITY_AND_GATEWAY_REOPEN_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
