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
 if houses!=1039 or roadA!=126 or roadB!=1668 or roadC!=5157:
  raise RuntimeError("Expected 1039 buildings / 6951 total road tiles, found "+str((houses,roadA,roadB,roadC)))
 b2ids=("SK-RX-097","SK-RX-164","SK-RX-201","SK-RX-150","SK-RX-045",
 "SK-RX-006","SK-RX-009","SK-RX-168","SK-RX-165","SK-RX-138",
 "SK-RX-096","SK-RX-167","SK-RX-005","SK-RX-101","SK-RX-051",
 "SK-RX-151","SK-RX-178","SK-RX-157","SK-RX-046","SK-RX-052",
 "SK-RX-141","SK-RX-173","SK-RX-095","SK-RX-189","SK-RX-169",
 "SK-RX-077","SK-RX-144","SK-RX-170","SK-RX-180","SK-RX-002",
 "SK-RX-085","SK-RX-171","SK-RX-227","SK-RX-176","SK-RX-028",
 "SK-RX-175","SK-RX-186","SK-RX-010","SK-RX-118","SK-RX-016")
 from collections import Counter
 grouped=Counter(label.split("SKARVIK_EXPANSION_B2_ROAD_",1)[-1].split("_",1)[0]
                 for label in labels if label.startswith("SKARVIK_EXPANSION_B2_ROAD_"))
 if set(grouped)!=set(b2ids) or not all(grouped[x]>=16 for x in b2ids):
  raise RuntimeError("Not all 40 new road labels persisted: "+str(grouped))
 data["secondBatchRoadsById"]=dict(grouped)
 if houses!=1039 or roadA!=126 or roadB!=1668:
  raise RuntimeError("Lost prior World Partition building or road actors on graded map")
 softpath=cityref[0].class_
 type_values={"pythonSoftObjectPathRepresentation":str(softpath)}
 for method in ("to_string","get_asset_path_name","get_asset_name","get_long_package_name"):
  if hasattr(softpath,method):
   try:type_values[method]=str(getattr(softpath,method)())
   except Exception as exc:type_values[method+"Error"]=str(exc)
 try:type_values["asset_path_name"]=str(softpath.get_editor_property("asset_path_name"))
 except Exception as exc:type_values["asset_path_nameError"]=str(exc)
 typename=" ".join(type_values.values())
 data["cityClassSoftObjectPathMethods"]=type_values
 data["levelInstanceClassPathConfirmed"]=bool("LevelInstance" in typename)
 data["persistedCityActorDescriptorClass"]=typename
 data["nativeLevelInstanceTypeConfirmed"]=data["levelInstanceClassPathConfirmed"]
 data["levelInstanceTypeConfirmedFromDescriptor"]=data["levelInstanceClassPathConfirmed"]
 data["CitySampleFullActorsStreamed"]=False
 data["sourceWorldReferenceAfterReloadUnverified"]=not data["nativeLevelInstanceTypeConfirmed"]
 unreal.log("SKARVIK_BIGCITY_REOPEN_DESCRIPTOR_TYPE="+data["persistedCityActorDescriptorClass"])
 for f in (TARGET,CITY,ORIGINAL):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=hashes[str(f)]:
   raise RuntimeError("Read-only verification modified protected Unreal world")
 data["state"]="BIG_CITY_NAMED_ACTOR_AND_63_ROAD_ROUTES_PLUS_1039_BUILDINGS_PERSIST_TYPE_UNVERIFIED"
 data["referenceSavedAndReopened"]=data["levelInstanceClassPathConfirmed"]
 data["namedActorDescriptorSavedAndReopened"]=True
 unreal.log("SKARVIK_BIG_CITY_NATIVE_REFERENCE_WP_DESCRIPTOR_PERSISTED=true")
except Exception as e:
 data["error"]=str(e);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_BIG_CITY_REFERENCE_REOPEN_FAILED="+str(e))
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
