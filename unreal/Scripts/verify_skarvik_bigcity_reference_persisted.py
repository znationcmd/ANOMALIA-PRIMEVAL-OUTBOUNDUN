"""Read-only verification that the native unloaded City Sample LevelInstance and
the original 124-site/23-route actor descriptors persist after editor reload.
Does not load 86k City external actors or claim visible/playable Big City.
"""
import hashlib,json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
REPORT=Path(os.environ["SKARVIK_BIGCITY_REFERENCE_REOPEN_REPORT"])
LABEL="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
data={"state":"FAILED","readOnly":True,"referenceSavedAndReopened":False,
      "actualCityVisibleInSM5":False,"fullCityActorStreamingVerified":False,
      "CitySampleVehiclesOrCrowdsActivated":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Wrong stage")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Wrong stage marker")
 if not all(x.is_file() for x in (TARGET,CITY,ORIGINAL)):
  raise RuntimeError("Native map files missing")
 hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (TARGET,CITY,ORIGINAL)}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Graded 48km map did not reopen")
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(x.label) for x in desc]
 cityref=[d for d in desc if str(d.label)==LABEL]
 houses=sum(name.startswith("SKARVIK_GRADED_SITE_") for name in labels)
 roadA=sum(name.startswith("SKARVIK_GRADED_ROAD_") for name in labels)
 roadB=sum(name.startswith("SKARVIK_EXPANSION_ROAD_") for name in labels)
 roadC=sum(name.startswith("SKARVIK_EXPANSION_B2_ROAD_") for name in labels)
 data.update(nativeLevelInstanceDescriptorCount=len(cityref),
   existing3DBuildingActorDescriptors=houses,
   existingFirst3RoadActorDescriptors=roadA,
   existingBatch20RoadActorDescriptors=roadB,
   additionalSecondBatchRoadActorDescriptors=roadC)
 if len(cityref)!=1:
  raise RuntimeError("Big City native LevelInstance actor not persisted")
 if houses!=1039 or roadA!=126 or roadB!=1668:
  raise RuntimeError("Lost prior World Partition building or road actors on graded map")
 # The Python ActorDesc.class_ field may return a generic UClass wrapper;
 # record its exact value rather than assuming the string contains the C++ type.
 typename=str(cityref[0].class_)
 data["persistedCityActorDescriptorClass"]=typename
 data["levelInstanceTypeConfirmedFromDescriptor"]=bool("LevelInstance" in typename)
 data["sourceWorldReferenceNotYetVerifiedAfterReopen"]=not data["levelInstanceTypeConfirmedFromDescriptor"]
 unreal.log("SKARVIK_BIGCITY_PERSISTED_ACTOR_DESCRIPTOR_TYPE="+typename)

 for f in (TARGET,CITY,ORIGINAL):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=hashes[str(f)]:
   raise RuntimeError("Read-only verification modified protected Unreal world")
 data["state"]="BIG_CITY_NAMED_ACTOR_DESCRIPTOR_PERSISTS_REFERENCE_TYPE_NEEDS_MORE_INSPECTION"
 data["referenceSavedAndReopened"]=bool(data["levelInstanceTypeConfirmedFromDescriptor"])
 data["namedActorDescriptorSavedAndReopened"]=True
 unreal.log("SKARVIK_BIG_CITY_NATIVE_REFERENCE_WP_DESCRIPTOR_PERSISTED=true")
except Exception as e:
 data["error"]=str(e);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_BIG_CITY_REFERENCE_REOPEN_FAILED="+str(e))
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
