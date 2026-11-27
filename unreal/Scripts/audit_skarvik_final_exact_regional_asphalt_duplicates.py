"""Read-only actor-level verification of same-route regional asphalt duplication.

Two separately saved real-StaticMesh road batches A and B can geometrically
overlap. Prior 479 overlapping World Partition descriptor box pairs are merely
suspects. Compare actual loaded source mesh paths, XY positions and orientation
for sub-metre same-route candidates before any edit. Never delete a road.
"""
import hashlib, json, math, os, re, traceback
from pathlib import Path
from collections import defaultdict
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
A="SKARVIK_FINAL_REGIONAL_DRY_NATIVE_PILOT_"
B="SKARVIK_FINAL_NATIVE_REGIONAL_DRY_PILOT_"
OUT=Path(os.environ["SKARVIK_FINAL_REGIONAL_EXACT_DUPLICATES_REPORT"])
FILES=(
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
 ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
 ROOT/"Content/Map/Big_City_LVL.umap",
 Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"))
REPORT={"state":"FAILED","readOnly":True,"nativeWorldMutated":False,
  "duplicateActorsDeleted":0,"duplicateActorsDisabled":0,
  "actualDrivingAndSM5Playtested":False,
  "allRegionalRoadsCertifiedContinuous":False,
  "sameRouteDescriptorCandidates":0,"exactSameMeshPathAndDirection":0,
  "qualifiedBActorLabels":[],"samples":[]}
try:
 marker=ROOT/".skarvik-ci-stage-marker"
 if("ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper()
   or not marker.is_file()
   or marker.read_text(encoding="utf-8-sig").strip()!="41188816555"):
  raise RuntimeError("Unsafe stage")
 if not all(p.is_file() for p in FILES):raise RuntimeError("Protected source missing")
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 if not level.load_level("/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"):
  raise RuntimeError("Final real SKARVIK World Partition did not reopen")
 wp=unreal.WorldPartitionBlueprintLibrary
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 desc=wp.get_actor_descs() or []
 groupA=[d for d in desc if str(d.label).startswith(A)]
 groupB=[d for d in desc if str(d.label).startswith(B)]
 if len(groupA)!=663 or len(groupB)!=992:
  raise RuntimeError("New real source asphalt count changed: A={} B={}".format(len(groupA),len(groupB)))
 names=[str(d.label) for d in desc]
 for prefix,n in(
  ("SKARVIK_FINAL_DRY_OLD_REAL_ASPHALT_",6130),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B1_",1674),
  ("SKARVIK_FINAL_SAFE_TOWN_ACCESS_B2_",1298),
  ("SKARVIK_FINAL_NATIVE_GRADED_ORIGINAL_MESH_",906),
  ("SKARVIK_FINAL_NATIVE_ISLAND_ORIGINAL_MESH_",128),
  ("SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_",720)):
  if sum(z.startswith(prefix) for z in names)!=n:
   raise RuntimeError("Protected native actor count no longer matches "+prefix)
 def getroute(d):
  m=re.search(r"SK-RX-\d{3}",str(d.label))
  return m.group(0) if m else None
 def center(d):
  bb=d.bounds
  return ((float(bb.min.x)+float(bb.max.x))/2,
          (float(bb.min.y)+float(bb.max.y))/2)
 grouped=defaultdict(list)
 for d in groupA:
  route=getroute(d)
  if route:grouped[route].append(d)
 suspects=[]
 for d in groupB:
  route=getroute(d)
  if not route:continue
  x,y=center(d)
  matches=[]
  for candidate in grouped.get(route,[]):
   xx,yy=center(candidate)
   dist=math.hypot(x-xx,y-yy)/100.
   if dist<1.25:
    matches.append((dist,candidate))
  if matches:
   best=min(matches,key=lambda v:v[0])
   suspects.append((best[1],d,best[0],route))
 REPORT["sameRouteDescriptorCandidates"]=len(suspects)
 REPORT["sourceRegionalAActors"]=len(groupA)
 REPORT["sourceRegionalBActors"]=len(groupB)
 REPORT["candidateSourceRoads"]=sorted({x[3] for x in suspects})
 # Every candidate gets independently reloaded real actor mesh references.
 # Bound loaded cells to keep memory usage sane on 16GB Windows hardware.
 verified=[]
 for offset in range(0,len(suspects),36):
  batch=suspects[offset:offset+36]
  selected={str(d.label):d for a,b,_,_ in batch for d in (a,b)}
  wp.load_actors([d.guid for d in selected.values()])
  loaded={actor.get_actor_label():actor for actor in actors.get_all_level_actors()}
  for a,b,desc_distance,route in batch:
   actorA=loaded.get(str(a.label));actorB=loaded.get(str(b.label))
   if not actorA or not actorB or not isinstance(actorA,unreal.StaticMeshActor) or not isinstance(actorB,unreal.StaticMeshActor):
    raise RuntimeError("Candidate asphalt actor not loadable after World Partition reopen")
   ca=actorA.get_component_by_class(unreal.StaticMeshComponent)
   cb=actorB.get_component_by_class(unreal.StaticMeshComponent)
   ma=ca.get_editor_property("static_mesh") if ca else None
   mb=cb.get_editor_property("static_mesh") if cb else None
   if not isinstance(ma,unreal.StaticMesh) or not isinstance(mb,unreal.StaticMesh):
    raise RuntimeError("Road duplicate candidate lacks real loaded StaticMesh")
   pa=actorA.get_actor_location();pb=actorB.get_actor_location()
   ra=actorA.get_actor_rotation();rb=actorB.get_actor_rotation()
   xy=math.hypot(float(pa.x-pb.x),float(pa.y-pb.y))/100.
   dz=abs(float(pa.z-pb.z))/100.
   yaw=abs((float(ra.yaw)-float(rb.yaw)+180.)%360.-180.)
   pitch=abs((float(ra.pitch)-float(rb.pitch)+180.)%360.-180.)
   same=ma.get_path_name()==mb.get_path_name()
   istrue=(same and xy<=.85 and dz<=.45 and yaw<=2.5 and pitch<=3.)
   if istrue:
    verified.append({
     "olderA":str(a.label),"newerB":str(b.label),"roadId":route,
     "distanceXYMetres":round(xy,3),
     "verticalDeltaMetres":round(dz,3),
     "yawDeltaDegrees":round(yaw,2),
     "pitchDeltaDegrees":round(pitch,2),
     "originalStaticMeshAsset":ma.get_path_name(),
     "actorBIsVerifiedOverlaidAsphalt":True,
     "preservedUntilSafeRemediation":True
    })
   elif len(REPORT["samples"])<25:
    REPORT["samples"].append({
     "road":route,"candidateB":str(b.label),"distanceXYMetres":round(xy,3),
     "heightDifferenceMetres":round(dz,3),"yawDegrees":round(yaw,2),
     "sameSourceMesh":same,"notAcceptedAsCertainOverlap":True})
  wp.unload_actors([d.guid for d in selected.values()])
 REPORT["exactSameMeshPathAndDirection"]=len(verified)
 REPORT["verifiedOverlaidActors"]=verified
 REPORT["qualifiedBActorLabels"]=[row["newerB"] for row in verified]
 REPORT["overlapRoutes"]=sorted({x["roadId"] for x in verified})
 REPORT["confidentOverlapCountNotYetCorrected"]=len(verified)
 for p in FILES:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
   raise RuntimeError("Read-only native overlap audit modified source world")
 REPORT["state"]="SKARVIK_FINAL_TWO_REGIONAL_PILOTS_REAL_DUPLICATE_MESHES_VERIFIED_READ_ONLY"
 REPORT["protectedOriginalsUnchanged"]=True
 unreal.log("SKARVIK_FINAL_REAL_REGIONAL_SUBMETRE_DUPLICATES_VERIFIED="+str(len(verified)))
except Exception as exc:
 REPORT["error"]=str(exc);REPORT["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_NATIVE_REGIONAL_EXACT_DUPLICATE_SURVEY_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
