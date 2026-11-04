"""Audit actual Big City World Partition actor metadata WITHOUT streaming any cell.
Read-only: never call load_actors(), load_level_instance(), save(), or spawn().
Purpose: inspect whether real CitySample static building subsets can be streamed
safely into SKARVIK without forcing 86,608 external actors into editor memory.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,os,traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_CITYSOURCE_DESC_REPORT"])
CITY_PACKAGE="/Game/Map/Big_City_LVL"
CITY_FILE=ROOT/"Content/Map/Big_City_LVL.umap"
GRADED=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
D_ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
DOC={"state":"FAILED","readOnly":True,"BigCitySourceWorldActorStreamingPerformed":False,
     "CitySampleModified":False,"gradedSkarvikModified":False,
     "nativeGameTested":False,"BigCityFullIntegrationConfirmed":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
    ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Wrong isolated stage and marker")
 for p in (CITY_FILE,GRADED,D_ORIGINAL):
  if not p.is_file():raise RuntimeError("Missing protected city/graded/original world: "+str(p))
 sha={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (CITY_FILE,GRADED,D_ORIGINAL)}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not levels.load_level(CITY_PACKAGE):
  raise RuntimeError("Could not open CitySample World Partition source")
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 DOC["actualWorld"]=world.get_path_name() if world else ""
 descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 DOC["descriptorCount"]=len(descs)
 loaded=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 DOC["loadedLevelActorCount"]=len(loaded)
 DOC["allExternalCellsUnloaded"]=len(loaded)<min(len(descs),3000)
 sample=[]
 for d in descs[:min(len(descs),24)]:
  data={"label":str(d.label)[:180],"guid":str(d.guid),"classRepresentation":str(d.class_)[:250]}
  for attr in ("bounds","is_spatially_loaded","native_class"):
   try: data[attr]=str(getattr(d,attr))[:300]
   except Exception as e:data[attr+"Error"]=str(e)[:130]
  sample.append(data)
 DOC["first24ActorDescriptors"]=sample
 DOC["commonLabelPrefixes"]=dict(Counter(str(d.label).split("_")[0][:45] for d in descs).most_common(35))
 DOC["realSourceExternalActorFoldersOnDisk"]=(
   ROOT/"Content/__ExternalActors__/Map/Big_City_LVL").is_dir()
 DOC["sourceReferencedBySkarvikNative"]=(
   ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap").is_file()
 for p in (CITY_FILE,GRADED,D_ORIGINAL):
  if hashlib.sha256(p.read_bytes()).hexdigest()!=sha[str(p)]:
   raise RuntimeError("Read-only Big City metadata inspection modified protected source")
 if len(descs)<1000:
  raise RuntimeError("CitySample actor descriptors absent; cannot plan safe subset")
 DOC["state"]="BIG_CITY_SOURCE_WP_86K_ACTOR_DESCRIPTOR_METADATA_AUDITED_WITHOUT_STREAMING"
 unreal.log("SKARVIK_BIG_CITY_SOURCE_DESCRIPTOR_METADATA_AUDIT_SUCCESS="+str(len(descs)))
except Exception as e:
 DOC["error"]=str(e);DOC["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_BIG_CITY_SOURCE_DESCRIPTOR_AUDIT_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(DOC,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
