"""Read-only persistence proof for genuine City Sample downtown source mesh actors.
Checks 180 source-asset actors AND the 1039 sites, 13039 prior road meshes,
375 road gap patches, and the existing native Big City LevelInstance reference.
Selectively load <= 8 city mesh actors to verify real mesh packages and positions.
"""
from pathlib import Path
import os,json,hashlib,traceback,math
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_CITYCORE_REOPEN_REPORT"])
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
FILES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
       ROOT/"Content/Map/Big_City_LVL.umap",
       Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
LABEL="SKARVIK_CENTRE_REAL_CITYSAMPLE_MESH_V1_"
BIGCITY="SKARVIK_CENTRE_CITY_SAMPLE_NATIVE_LEVEL_REFERENCE_V1"
data={"state":"FAILED","readOnly":True,"SM5VisualRenderPassed":False,
      "fullBigCity4KmPopulationPassed":False,"SM5VehicleDrivePassed":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Unsafe stage")
 if not all(p.is_file() for p in FILES):raise RuntimeError("Required protected map missing")
 orig={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(PKG):raise RuntimeError("Actual SKARVIK graded world failed to reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 descs=wp.get_actor_descs() or []
 lab=[str(d.label) for d in descs]
 count=lambda prefix:sum(x.startswith(prefix) for x in lab)
 city=[d for d in descs if str(d.label).startswith(LABEL)]
 citysrc=[d for d in descs if str(d.label)==BIGCITY]
 data["savedWorldCounts"]={
  "citySourceMeshActors":len(city),"CitySampleSourceLevelInstance":len(citysrc),
  "townMeshActors":count("SKARVIK_GRADED_SITE_"),
  "old3RoadActors":count("SKARVIK_GRADED_ROAD_"),
  "batch20RoadActors":count("SKARVIK_EXPANSION_ROAD_"),
  "batch40B2RoadActors":count("SKARVIK_EXPANSION_B2_ROAD_"),
  "batch37C3RoadActors":count("SKARVIK_EXPANSION_C3_ROAD_"),
  "gapRepairRealAsphaltActors":count("SKARVIK_CONTINUITY_PATCH_V1_"),
  "switchbackRealAsphaltActors":count("SKARVIK_REAL_SWITCHBACK_V1_")}
 if data["savedWorldCounts"]!={"citySourceMeshActors":180,"CitySampleSourceLevelInstance":1,
  "townMeshActors":1039,"old3RoadActors":126,"batch20RoadActors":1668,
  "batch40B2RoadActors":5157,"batch37C3RoadActors":6088,
  "gapRepairRealAsphaltActors":375,"switchbackRealAsphaltActors":142}:
  raise RuntimeError("Some previously saved city or road actor packages missing "+str(data["savedWorldCounts"]))
 wp.load_actors([d.guid for d in city[:8]])
 loaded={a.get_actor_label():a for a in actors.get_all_level_actors()}
 meshes=[]
 for d in city[:8]:
  actor=loaded.get(str(d.label))
  if not actor:raise RuntimeError("Selected original city mesh actor does not load: "+str(d.label))
  if not isinstance(actor,unreal.StaticMeshActor):
   raise RuntimeError("City component pilot contains no actual StaticMeshActor class")
  comp=actor.get_component_by_class(unreal.StaticMeshComponent)
  if not comp or not comp.get_editor_property("static_mesh"):
   raise RuntimeError("City actor has no real mesh reference")
  path=comp.get_editor_property("static_mesh").get_path_name()
  p=actor.get_actor_location()
  if not (90000<p.x<320000 and 650000<p.y<950000 and math.isfinite(p.z)):
   raise RuntimeError("City source mesh asset outside reserved SKARVIK-CENTRE region "+str((p.x,p.y,p.z)))
  meshes.append({"actor":str(d.label),"asset":path,
      "locationCm":[round(p.x,1),round(p.y,1),round(p.z,1)]})
 data["selectivelyLoadedCityCoreMeshActors"]=meshes
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=orig[str(p)]:
   raise RuntimeError("Native read-only test changed a protected map")
 data["state"]="BIG_CITY_REAL_CITYSAMPLE_180_MESHES_AND_13556_ASPHALT_ACTORS_PERSIST_AFTER_REOPEN"
 unreal.log("SKARVIK_REAL_CITYSAMPLE_CORE_REOPENED_MESH_COUNT=180")
except Exception as e:
 data["error"]=str(e);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_REAL_CITYSAMPLE_CORE_REOPEN_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
