"""Read-only original road 3D actor route/grade audit for a single final SKARVIK.
Check every source paved mesh's native WP descriptor against final seven-island
terrain, coastal dry mask, road width/crossgrade. This does not migrate/claim
contiguous roads. Candidate labels are used in controlled future replay.
"""
import os,json,math,hashlib,traceback
from pathlib import Path
from collections import Counter
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
FINAL=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
GRADED=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
OUT=Path(os.environ["SKARVIK_FINAL_ROAD_AUDIT_REPORT"])
PREFIXES=(
 "SKARVIK_GRADED_ROAD_",
 "SKARVIK_EXPANSION_ROAD_",
 "SKARVIK_EXPANSION_B2_ROAD_",
 "SKARVIK_EXPANSION_C3_ROAD_",
 "SKARVIK_CONTINUITY_PATCH_V1_",
 "SKARVIK_REAL_SWITCHBACK_V1_",
 "SKARVIK_NATIVE_TOWN_GATEWAY_V1_",
 "SKARVIK_NATIVE_TOWN_GATEWAY_V2_",
 "SKARVIK_REAL_LOCAL_RING_V1_"
)
doc={"state":"FAILED","readOnly":True,"trueSourceRealRoadsCopied":0,
 "fullRoadNetworkDriveable":False,"allBridgesWaterCrossingsMigrated":False,
 "visuallyTested":False,"safeExistingRoadActorLabels":[],"blockedActorExamples":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
  ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Wrong native stage")
 for p in (FINAL,GRADED,D):
  if not p.is_file():raise RuntimeError("Protected map missing "+str(p))
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (FINAL,GRADED,D)}
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not level.load_level(SOURCE):raise RuntimeError("Cannot open source World Partition roads")
 wp=unreal.WorldPartitionBlueprintLibrary
 desc=wp.get_actor_descs() or []
 actual=[d for d in desc if any(str(d.label).startswith(prefix) for prefix in PREFIXES)]
 counts=Counter(next(p for p in PREFIXES if str(d.label).startswith(p)) for d in actual)
 doc["originalNativeReal3DRoadActors"]=len(actual)
 doc["sourceRoadPrefixCounts"]=dict(counts)
 if len(actual)<14000:raise RuntimeError("Original 14k+ real road actor descriptors not found")
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 h=lib.skarvik_final_coastal_height
 if not h:raise RuntimeError("Native final island terrace C++ sampler missing")
 reasons=Counter()
 perPrefixSafe=Counter()
 examples=[]
 for d in actual:
  label=str(d.label);prefix=next(p for p in PREFIXES if label.startswith(p))
  b=d.bounds
  e=(float(b.min.x)+float(b.max.x))/200.
  north=-(float(b.min.y)+float(b.max.y))/200.
  widthE=abs(float(b.max.x-b.min.x))/100.
  widthN=abs(float(b.max.y-b.min.y))/100.
  reason=None
  if not all(math.isfinite(t) for t in (e,north,widthE,widthN)):
   reason="nonfinite-wp-source-bounds"
  elif max(widthE,widthN)>85 or min(widthE,widthN)<.4:
   reason="unexpected-slope-mesh-bounds"
  elif abs(e)>23900 or abs(north)>23900:
   reason="outside-final-world"
  else:
   dx=min(max(widthE*.36,2.5),16.)
   dn=min(max(widthN*.36,2.5),16.)
   samples=[float(h(e+xx,north+yy)) for xx in (-dx,0,dx) for yy in (-dn,0,dn)]
   if not all(math.isfinite(v) for v in samples):
    reason="nonfinite-final-terrain-height"
   elif min(samples)<4.0:
    reason="ocean-or-unsafe-coastal-beach"
   elif max(samples)-min(samples)>2.6:
    reason="steep-or-uneven-final-terrain"
  if reason:
   reasons[reason]+=1
   if len(examples)<45:examples.append({"actor":label,"reason":reason,"eastKm":round(e/1000,3),"northKm":round(north/1000,3)})
  else:
   perPrefixSafe[prefix]+=1
   doc["safeExistingRoadActorLabels"].append(label)
 doc["nativeCoastSafeSourceRoadActorCount"]=len(doc["safeExistingRoadActorLabels"])
 doc["unsafeSourceRoadActorCount"]=len(actual)-doc["nativeCoastSafeSourceRoadActorCount"]
 doc["rejectionReasons"]=dict(reasons)
 doc["coastSafeByOriginalRoadType"]=dict(perPrefixSafe)
 doc["blockedActorExamples"]=examples
 doc["sourceRoadsStillNotMigrated"]=True
 doc["plannedConnectivityRebuildRequired"]=doc["unsafeSourceRoadActorCount"]>0
 for p in (FINAL,GRADED,D):
  if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
   raise RuntimeError("Source road read-only audit unexpectedly modified native World")
 doc["state"]="FINAL_SEVEN_ISLAND_ROAD_3D_SOURCE_COAST_AND_SLOPE_AUDITED_NOT_YET_MIGRATED"
 unreal.log("SKARVIK_FINAL_COAST_SAFE_SOURCE_ROAD_SEGMENTS="+str(doc["nativeCoastSafeSourceRoadActorCount"]))
 unreal.log("SKARVIK_FINAL_UNSAFE_OCEAN_OR_GRADE_SOURCE_ROAD_SEGMENTS="+str(doc["unsafeSourceRoadActorCount"]))
except Exception as e:
 doc["error"]=str(e);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_ROAD_ACTORS_COAST_AUDIT_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
