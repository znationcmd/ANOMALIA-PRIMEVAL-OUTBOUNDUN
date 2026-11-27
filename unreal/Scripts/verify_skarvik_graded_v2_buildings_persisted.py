"""Reopen native graded 48km SKARVIK and audit saved World Partition actor descriptors.
Do not mistake unloaded cells for absent buildings, and do not modify any world.
"""
from pathlib import Path
import json,os,hashlib,traceback
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ.get("SKARVIK_GRADED_REOPEN_BUILDING_REPORT",str(ROOT/"Saved/SkarvikCity/reopened-localities.json")))
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
SPEC=Path(os.environ["SKARVIK_GRADED_REOPEN_MASTERPLAN"])
result={"state":"FAILED","readOnly":True,"gradedWorldReopened":False,"sitesWithSavedMeshActors":0,"savedMeshActors":0}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Untrusted native stage root")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted marker")
 if not TARGET.is_file() or not ORIGINAL.is_file():
  raise RuntimeError("Required original or graded world missing")
 plan=json.loads(SPEC.read_text(encoding="utf-8"))
 sites={s["id"] for s in plan["settlements"]}-{ "citysample" }
 if len(sites)!=124:raise RuntimeError("Expected 124 settlement centers")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ORIGINAL,TARGET)}
 editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not editor.load_level(PKG):raise RuntimeError("Could not reopen graded native world")
 descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(x.label) for x in descs]
 mine=[s for s in labels if s.startswith("SKARVIK_GRADED_SITE_")]
 counts={}
 for site in sites:
  counts[site]=len([p for p in mine if p.startswith("SKARVIK_GRADED_SITE_"+site+"_")])
 missing=sorted(k for k,v in counts.items() if v==0)
 landscape=sum("Landscape" in str(x.class_) or "Landscape" in str(x.label) for x in descs)
 result.update(gradedWorldReopened=True,landscapeDescriptors=landscape,
  sitesWithSavedMeshActors=len(sites)-len(missing),savedMeshActors=len(mine),
  emptySites=missing,allSiteCounts=counts,originalDModified=False)
 if landscape<1:raise RuntimeError("No persisted graded terrain")
 if missing or len(mine)<620:
  raise RuntimeError("Persisted WP actors incomplete: {} sites={} actors={}".format(len(missing),missing[:8],len(mine)))
 after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ORIGINAL,TARGET)}
 if before!=after:raise RuntimeError("Read-only audit unexpectedly changed map")
 result["state"]="GRADED_48KM_WORLD_124_SITES_REAL_MESH_ACTORS_PERSISTED_WP_REOPENED_NOT_PLAYTESTED"
 result["gameplayValidated"]=False
 unreal.log("SKARVIK_124_GRADED_WP_SAVED_BUILDING_ACTORS_VERIFIED="+str(len(mine)))
except Exception as e:
 result["error"]=str(e);result["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_124_GRADED_WP_BUILDING_AUDIT_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
