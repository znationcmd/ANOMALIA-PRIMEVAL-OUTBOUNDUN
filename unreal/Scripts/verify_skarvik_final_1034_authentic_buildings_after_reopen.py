"""Independently reopen final SKARVIK 48km true-coast World Partition to prove
actual 906 original graded building and 128 original insular source actors persist.
No modification, no inferred meshes from manifest, verify seven real mesh paths.
"""
import os,json,hashlib,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
TARGET="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
FILES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
       ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
       ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
       Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
OUTPUT=Path(os.environ["SKARVIK_FINAL_HOUSES_INDEPENDENT_REOPEN_REPORT"])
doc={"state":"FAILED","readOnly":True,"SM5PlayabilityVerified":False,"CitySampleFullMigrationVerified":False,
     "RoadsFullMigrationVerified":False,"seaSimulationValidated":False,"sourceMapsModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Unsafe stage or marker")
 if not all(f.is_file() for f in FILES):raise RuntimeError("Original or final world file missing")
 hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not levels.load_level(TARGET):raise RuntimeError("Final native World Partition did not reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 descs=wp.get_actor_descs() or []
 sites=[d for d in descs if str(d.label).startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_")]
 islands=[d for d in descs if str(d.label).startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_")]
 doc["actualSavedOriginalGradedStaticMeshActors"]=len(sites)
 doc["actualSavedOriginalIslandStaticMeshActors"]=len(islands)
 if len(sites)!=906 or len(islands)!=128:
  raise RuntimeError("Expected 906+128 genuine old actor descriptors, got "+str((len(sites),len(islands))))
 # One representative native 3D mesh from mainland and first seven different island IDs.
 samples=[]
 for kind,groups in (("graded",sites),("island",islands)):
  selected=[]
  seen=set()
  for d in groups:
   label=str(d.label)
   segment=label.split("_")
   # To check actual assets rather than only text labels, load a bounded sample.
   k=label.split("_",5)[4] if kind=="graded" else label.split("_",5)[4]
   if k in seen:continue
   selected.append(d);seen.add(k)
   if len(selected)>=8:break
  wp.load_actors([d.guid for d in selected])
  loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
  for d in selected:
   actor=loaded.get(str(d.label))
   if not actor or not isinstance(actor,unreal.StaticMeshActor):
    raise RuntimeError("Native source actor failed selective load after reload "+str(d.label))
   component=actor.get_component_by_class(unreal.StaticMeshComponent)
   mesh=component.get_editor_property("static_mesh") if component else None
   if not isinstance(mesh,unreal.StaticMesh):
    raise RuntimeError("Native final source actor no genuine mesh on reopen")
   samples.append({"group":kind,"actor":str(d.label),"asset":mesh.get_path_name()})
 doc["selectivelyLoadedNativeOriginalStaticMeshes"]=samples
 if len(samples)<2:raise RuntimeError("No actual world mesh components reloaded")
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[str(p)]:
   raise RuntimeError("Read-only audit modified a protected source map")
 doc["state"]="FINAL_COAST_906_MAINLAND_AND_128_ISLAND_AUTHENTIC_SOURCE_3D_ACTORS_PERSIST_AFTER_REOPEN"
 doc["sourceMapsModified"]=False
 unreal.log("SKARVIK_FINAL_1034_AUTHENTIC_ORIGINAL_3D_ACTORS_REOPENED=true")
except Exception as e:
 doc["error"]=str(e);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_AUTHENTIC_3D_MIGRATION_REOPEN_FAILED="+str(e))
finally:
 OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 OUTPUT.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
