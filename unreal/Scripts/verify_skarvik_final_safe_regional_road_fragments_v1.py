"""Independently reopen final SKARVIK; confirm all new real regional road mesh actors.

Read-only. Explicitly does NOT establish end-to-end road connectivity,
bridges, PIE SM5 vehicle operation or complete imported Big City.
"""
import hashlib
import json
import math
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
PREFIX="SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
REPORT=Path(os.environ["SKARVIK_FINAL_REGIONAL_BUILD_RESULT"])
OUT=Path(os.environ["SKARVIK_FINAL_REGIONAL_REOPEN_RESULT"])
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
)
doc={"state":"FAILED","readOnly":True,"SM5Driven":False,"all382RoadsConnected":False,
 "allVillageRoutesComplete":False,"fullCitySampleRendered":False}
try:
 marker=ROOT/".skarvik-ci-stage-marker"
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
     not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Unsafe staging project")
 if not all(p.is_file() for p in FILES):
  raise RuntimeError("Required protected world package missing")
 r=json.loads(REPORT.read_text(encoding="utf-8-sig"))
 status=r.get("state")
 good="FINAL_NATIVE_COAST_AUTHENTIC_REGIONAL_SAFE_ROAD_FRAGMENTS_SAVED_NOT_DRIVEN_OR_CONNECTED"
 empty="NO_NEW_COLLISION_FREE_REGIONAL_ASPHALT_AVAILABLE_WITHOUT_BRIDGES_OR_EARTHWORKS"
 if status not in (good,empty):
  raise RuntimeError("No original native regional build receipt")
 original={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not level.load_level(PKG):
  raise RuntimeError("Final SKARVIK native world failed to reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 descs=wp.get_actor_descs() or []
 labels=[str(d.label) for d in descs]
 counts={
  "newRegionalPilotAsphalt":sum(s.startswith(PREFIX) for s in labels),
  "previousOriginalDryRoads":sum(s.startswith("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_") for s in labels),
  "localBatch1":sum(s.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_") for s in labels),
  "localBatch2":sum(s.startswith("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_") for s in labels),
  "mainlandBuildings":sum(s.startswith("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_") for s in labels),
  "islandBuildings":sum(s.startswith("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_") for s in labels),
  "realBigCitySourceMeshes":sum(s.startswith("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_") for s in labels)
 }
 doc["nativePersistedActorCounts"]=counts
 if (counts["previousOriginalDryRoads"]!=6130 or counts["localBatch1"]!=1674 or
     counts["localBatch2"]!=1298 or counts["mainlandBuildings"]!=906 or
     counts["islandBuildings"]!=128 or counts["realBigCitySourceMeshes"]!=720):
  raise RuntimeError("The trusted native final world lost prior 3D actors")
 if counts["newRegionalPilotAsphalt"]!=int(r["newRoadActors"]):
  raise RuntimeError("New genuine native regional road actor count not persistent")
 fragments=[d for d in descs if str(d.label).startswith(PREFIX)]
 if len({str(d.label) for d in fragments})!=len(fragments):
  raise RuntimeError("New regional road actor labels duplicated")
 check=[]
 if fragments:
  chosen=sorted(fragments,key=lambda d:str(d.label))
  selected=[chosen[i] for i in sorted({int(j*(len(chosen)-1)/11) for j in range(12)})]
  wp.load_actors([d.guid for d in selected])
  loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
  native=unreal.AnomaliaZPrigimaliaWorldImportLibrary.skarvik_final_coastal_height
  for d in selected:
   a=loaded.get(str(d.label))
   if not a or not isinstance(a,unreal.StaticMeshActor):
    raise RuntimeError("Regional native 3D actor failed selective reload")
   c=a.get_component_by_class(unreal.StaticMeshComponent)
   mesh=c.get_editor_property("static_mesh") if c else None
   if not isinstance(mesh,unreal.StaticMesh):
    raise RuntimeError("Original source CitySample asphalt missing on reopened actor")
   p=a.get_actor_location()
   h=float(native(float(p.x)/100.,-float(p.y)/100.))
   if not math.isfinite(h) or h<5.:
    raise RuntimeError("Reopened new road actor over actual native ocean")
   check.append({"label":str(d.label),"realMesh":mesh.get_path_name(),"nativeTerrainHeight":round(h,2)})
  wp.unload_actors([d.guid for d in selected])
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=original[str(p)]:
   raise RuntimeError("Read-only reopening altered native project or original D")
 doc["sampleRealStaticMeshActorsLoaded"]=check
 doc["newRegionalMetresInBuildReceipt"]=r["newPavedMetres"]
 doc["sourcesUnchanged"]=True
 doc["state"]=("FINAL_NATIVE_AUTHENTIC_REGIONAL_ROAD_FRAGMENTS_PERSISTED_NOT_DRIVEN"
               if fragments else "FINAL_NATIVE_NO_SAFE_NEW_REGIONAL_FRAGMENTS_NOT_MODIFIED")
 unreal.log("SKARVIK_FINAL_NATIVE_REGIONAL_FRAGMENT_REOPEN_COUNT="+str(len(fragments)))
except Exception as e:
 doc["error"]=str(e);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_NATIVE_REGIONAL_REOPEN_FAILURE="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
