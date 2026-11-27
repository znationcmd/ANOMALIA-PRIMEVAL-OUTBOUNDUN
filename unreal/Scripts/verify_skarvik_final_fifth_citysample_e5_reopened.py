"""Reopen final seven-island WP and independently prove genuine 5th city sector."""
import hashlib,json,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_FINAL_CITY_E5_REOPEN_REPORT"])
BUILD=Path(os.environ["SKARVIK_FINAL_CITY_E5_BUILD_RECEIPT"])
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
PREFIX="SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_E5_"
report={"state":"FAILED","readOnly":True,"SM5Rendered":False,
        "allBigCitySourceActorsLoaded":False,"interiorsValidated":False}
try:
 mark=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
     or not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Incorrect isolated native project")
 if any(not p.is_file() for p in FILES) or not BUILD.is_file():
  raise RuntimeError("Protected world or prior city report missing")
 earlier=json.loads(BUILD.read_text(encoding="utf-8-sig"))
 if earlier.get("state")!="FINAL_COAST_REAL_CITY_SAMPLE_FIFTH_SOURCE_DISTRICT_NATIVE_MESHES_SAVED_NOT_FULL_CITY":
  raise RuntimeError("Fifth source city import did not save")
 expected=int(earlier.get("realStaticMeshActorsSaved",0))
 if not 15<=expected<=180:raise RuntimeError("Invalid fifth city source actor count")
 hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("Cannot reopen original-coast final 48 km world")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(prefix):return sum(l.startswith(prefix) for l in labels)
 for prefix,num in (
   ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
   ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
   ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
   ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
   ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
   ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298)):
  if count(prefix)!=num:
   raise RuntimeError("Original native elements missing "+prefix)
 selected=[d for d in desc if str(d.label).startswith(PREFIX)]
 report["newSectorGenuineStaticMeshActorDescriptors"]=len(selected)
 if len(selected)!=expected:raise RuntimeError("New fifth Big City sector actor count changed after re-open")
 chosen=[selected[i] for i in sorted({int(z*(len(selected)-1)/11) for z in range(12)})]
 wp.load_actors([d.guid for d in chosen])
 actors={a.get_actor_label():a for a in
    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
 samples=[]
 for desc in chosen:
  lab=str(desc.label);a=actors.get(lab)
  if not isinstance(a,unreal.StaticMeshActor):raise RuntimeError("Actual CitySample actor missing "+lab)
  c=a.get_component_by_class(unreal.StaticMeshComponent)
  mesh=c.get_editor_property("static_mesh") if c else None
  if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("No actual native building mesh on "+lab)
  samples.append({"label":lab,"trueSourceMesh":mesh.get_path_name()})
 wp.unload_actors([d.guid for d in chosen])
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[str(p)]:
   raise RuntimeError("Read-only verification changed protected source world")
 report.update(state="FINAL_SKARVIK_FIFTH_CITYSAMPLE_GENUINE_MESH_SECTOR_PERSISTS_NOT_FULL_CITY",
               sourceUnchanged=True,realAssetsLoadedAfterReopen=samples,
               totalGenuineCitySourceActorsInFinal=720+expected)
 unreal.log("SKARVIK_FINAL_FIFTH_CITY_REAL_ACTORS_IN_WP="+str(expected))
except Exception as exc:
 report["error"]=str(exc);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_CITY_E5_VERIFY_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
