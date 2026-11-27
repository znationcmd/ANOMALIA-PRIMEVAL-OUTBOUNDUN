"""Independent exact same-route duplicate survey for two regional road imports.

Only call a second actor redundant when SAME planned SK-RX route has two native
World Partition descriptors whose XY centers differ by <=1.25 metres and whose
AABBs overlap. Report exact second-batch labels; NEVER delete anything here.
"""
import os,json,re,hashlib,math,traceback
from pathlib import Path
from collections import defaultdict,Counter
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUT=Path(os.environ["SKARVIK_FINAL_DUPLICATE_ROAD_SURVEY"])
FILES=(ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
PREFIX_A="SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
PREFIX_B="SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
PAT=re.compile(r"SK-RX-\d{3}")
data={"state":"FAILED","readOnly":True,"allRoadsPlaytested":False,"meshVisibilityModified":False,
      "duplicateBActorLabels":[],"actorPairs":[],"routeCounts":{}}
try:
 mark=ROOT/".skarvik-ci-stage-marker"
 if ("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or
      not mark.is_file() or mark.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Untrusted original project")
 if any(not f.is_file() for f in FILES):raise RuntimeError("Protected source map missing")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not level.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("Cannot load true final world")
 d=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 first=[a for a in d if str(a.label).startswith(PREFIX_A)]
 second=[a for a in d if str(a.label).startswith(PREFIX_B)]
 if len(first)!=663 or len(second)!=992:
  raise RuntimeError("Unexpected native regional pilot actors: "+str((len(first),len(second))))
 def point(a):
  b=a.bounds
  return ((float(b.min.x)+float(b.max.x))*.5,
          (float(b.min.y)+float(b.max.y))*.5)
 def route(l):
  k=PAT.search(str(l))
  if not k:raise RuntimeError("Source regional route ID missing "+str(l))
  return k.group(0)
 positions=defaultdict(list)
 for d in first:
  label=str(d.label)
  positions[route(label)].append((label,point(d),d.bounds))
 for a in second:
  label=str(a.label);key=route(label)
  pos=point(a)
  candidates=[]
  for orig,p,bounds in positions.get(key,[]):
   dist=math.hypot(pos[0]-p[0],pos[1]-p[1])/100.
   if dist>1.25:continue
   box=a.bounds
   if not (box.max.x+25>=bounds.min.x and bounds.max.x+25>=box.min.x and
           box.max.y+25>=bounds.min.y and bounds.max.y+25>=box.min.y):
    continue
   candidates.append((dist,orig))
  if candidates:
   dist,orig=min(candidates)
   data["duplicateBActorLabels"].append(label)
   data["actorPairs"].append({"second":label,"first":orig,"route":key,
                              "centerSeparationMetres":round(dist,3)})
 if len(set(data["duplicateBActorLabels"]))!=len(data["duplicateBActorLabels"]):
  raise RuntimeError("Duplicate road survey returned repeated actor labels")
 counts=Counter(x["route"] for x in data["actorPairs"])
 data["routeCounts"]=dict(counts)
 data["firstNativeRegionalActors"]=len(first)
 data["secondNativeRegionalActors"]=len(second)
 data["exactSameRouteXYNearDuplicateCount"]=len(data["duplicateBActorLabels"])
 data["possibleWiderOverlapRequiresVisualReview"]=True
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
   raise RuntimeError("Read-only exact duplicate survey unexpectedly modified a native map")
 data["originalFilesUnchanged"]=True
 data["state"]="EXACT_SAME_ROUTE_REGIONAL_DUPLICATE_SECOND_BATCH_SURVEY_ONLY"
 unreal.log("SKARVIK_FINAL_EXACT_NEAR_DUPLICATE_REGIONAL_B_ACTORS="+str(len(data["actorPairs"])))
except Exception as e:
 data["error"]=str(e);data["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_EXACT_REGIONAL_DUPLICATE_SURVEY_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
