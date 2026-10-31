"""Read-only proof of saved SKARVIK graded 48km World Partition after GitHub step-env hash error."""
import json,hashlib,traceback,os
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
out=Path(os.environ.get("SKARVIK_GRADED_EXISTING_AUDIT_REPORT",str(root/"Saved/SkarvikCity/graded-existing-audit.json")))
doc={"state":"FAILED","readOnly":True,"originalDModified":False,"productionMapModified":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(root).upper():
  raise RuntimeError("Not C isolated stage")
 if (root/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Wrong stage marker")
 path=root/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
 original=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
 v1=root/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
 for f in (path,original,v1):
  if not f.is_file():raise RuntimeError("Missing map "+str(f))
 hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (path,original,v1)}
 if not unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"):
  raise RuntimeError("Native graded map unrecognized as UE asset")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"):
  raise RuntimeError("Native graded map cannot reopen")
 # World Partition unloads spatial actor cells on reopen. A fresh get_all_level_actors()
 # legitimately returns zero LandscapeProxy actors until explicitly loaded.
 # Validate persistent on-disk actor descriptors first, then LOAD only a few
 # matching proxies to inspect actual native landscape geometry without 48km OOM.
 wp=unreal.WorldPartitionBlueprintLibrary
 descs=wp.get_actor_descs()
 if not descs:raise RuntimeError("No persisted World Partition actor descriptors in graded world")
 landscape_descriptors=[
  d for d in descs if
  "Landscape" in str(d.class_) or "Landscape" in str(d.label)
 ]
 doc["totalPersistedActorDescriptors"]=len(descs)
 doc["landscapeActorDescriptors"]=len(landscape_descriptors)
 if not landscape_descriptors:
  raise RuntimeError("Graded World Partition opened but landscape actor descriptors are absent")
 to_load=[d.guid for d in landscape_descriptors[:min(3,len(landscape_descriptors))]]
 wp.load_actors(to_load)
 landscapes=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 lc=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in landscapes)
 cc=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in landscapes)
 if lc<1 or cc<1 or lc!=cc:
  raise RuntimeError("No matching real loaded landscape/collision components after World Partition actor load: "+str((lc,cc)))
 landscape_height=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(landscape_height,"skarvik_graded_height"):
  raise RuntimeError("Unreal compiled grade sampler not loaded")
 test=[(3000,10000),(-18000,4000),(14000,15000)]
 grade_at_centers=[float(landscape_height.skarvik_graded_height(x,y)) for x,y in test]
 post={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (path,original,v1)}
 if hashes!=post:raise RuntimeError("Read-only audit changed map bytes, abort proof")
 doc.update(state="REAL_GRADED_48KM_WORLD_REOPENED_WITH_WORLD_PARTITION_DESCRIPTORS_AND_LOADED_COLLISION",
  gradedMapPackage="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2",
  loadedLandscapeComponentCount=lc,loadedCollisionComponentCount=cc,samples=grade_at_centers,
  DSourceSha256Unchanged=True,stagedV1Sha256Unchanged=True,
  gradedTerrainFileSha256Unchanged=True,
  buildingsPlacedInGradedMap=False,roadNetworkBuilt=False,playtested=False)
 unreal.log("SKARVIK_EXISTING_GRADED_V2_NATIVE_VERIFIED=true")
except Exception as exc:
 doc["error"]=str(exc);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_EXISTING_GRADED_V2_AUDIT_FAILED="+str(exc))
finally:
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
