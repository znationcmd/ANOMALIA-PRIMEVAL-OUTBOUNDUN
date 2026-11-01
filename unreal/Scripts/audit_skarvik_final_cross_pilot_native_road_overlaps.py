"""Read-only independent WP audit for overlapping regional road import pilots.

Never delete or alter road actors automatically. Compare original asphalt,
village asphalt and both regional staging batches. Find cross-import centers
and overlapping native descriptor boxes. Flag manual review where needed.
"""
import os,json,hashlib,math,traceback
from pathlib import Path
from collections import Counter,defaultdict
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_FINAL_REGIONAL_CROSS_PILOT_AUDIT"])
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
GROUPS={
 "newRegionalA":"SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_",
 "newRegionalB":"SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_",
 "oldAsphalt":"SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",
 "townB1":"SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",
 "townB2":"SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",
 "townB3":"SKARVIK_FINAL_SAFE_TOWN_ACCESS_B3_"}
doc={"state":"FAILED","readOnly":True,"routeContinuityOrDrivingVerified":False,
     "regionalImportsAutomaticallyMerged":False,"worldMutated":False}
try:
 mark=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
     or not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Untrusted local stage")
 if any(not p.is_file() for p in FILES):
  raise RuntimeError("Protected native map missing")
 hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not lv.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("Cannot reopen original seven-island map")
 desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 labels=[str(d.label) for d in desc]
 def count(prefix):return sum(x.startswith(prefix) for x in labels)
 for pre,num in (
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720),
  ("SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_E5_",121),
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298)):
  if count(pre)!=num:raise RuntimeError("An original native map actor count changed "+pre)
 grouped={key:[d for d in desc if str(d.label).startswith(pre)] for key,pre in GROUPS.items()}
 doc["nativeRealRoadActorCounts"]={key:len(v) for key,v in grouped.items()}
 doc["allExistingRoadsKept"]=(len(grouped["oldAsphalt"])==6130 and
                              len(grouped["townB1"])==1674 and len(grouped["townB2"])==1298)
 roads=[(g,d) for g in GROUPS for d in grouped[g]]
 # Only check cross-batch overlap; adjacent pieces within same strip are expected.
 # A 9m bounding-box overlap is a *potential* conflict, not proof of collision.
 bins=defaultdict(list);cell=20000.
 def center(desc):
  b=desc.bounds
  return ((float(b.min.x)+float(b.max.x))*.5,
          (float(b.min.y)+float(b.max.y))*.5)
 for group,d in roads:
  x,y=center(d)
  bins[int(math.floor(x/cell)),int(math.floor(y/cell))].append((group,d,x,y))
 results=Counter();examples=[]
 for group,d in roads:
  if group not in ("newRegionalA","newRegionalB"):continue
  x,y=center(d)
  ix,iy=int(math.floor(x/cell)),int(math.floor(y/cell))
  for dx in (-1,0,1):
   for dy in (-1,0,1):
    for other,dd,ox,oy in bins.get((ix+dx,iy+dy),[]):
     if group==other:continue
     # Only count A-B once, other road types only on one directional pass.
     if other in ("newRegionalA","newRegionalB") and group>other:continue
     if abs(x-ox)>750. or abs(y-oy)>750.:continue
     a,b=d.bounds,dd.bounds
     if not(a.max.x+150>=b.min.x and b.max.x+150>=a.min.x and
            a.max.y+150>=b.min.y and b.max.y+150>=a.min.y):continue
     key=group+"__vs__"+other
     results[key]+=1
     if len(examples)<50:
      examples.append({"a":str(d.label),"b":str(dd.label),
        "centerSeparationM":round(math.hypot(x-ox,y-oy)/100.,2)})
 doc["possibleCrossImportRoadFootprintIntersections"]=dict(results)
 doc["intersectionExamplesForReview"]=examples
 doc["requiresVehicleAndFootprintVisualReview"]=any(results.values())
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[str(p)]:
   raise RuntimeError("Read-only road overlap audit changed source world")
 doc.update(state="SKARVIK_FINAL_MULTIPLE_NATIVE_ROAD_BATCHES_READONLY_OVERLAP_REVIEW_READY",
            originalMapHashesUnchanged=True)
 unreal.log("SKARVIK_FINAL_POSSIBLE_CROSS_REGIONAL_ROAD_OVERLAPS="+str(sum(results.values())))
except Exception as exc:
 doc["error"]=str(exc);doc["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_ROAD_OVERLAP_AUDIT_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
