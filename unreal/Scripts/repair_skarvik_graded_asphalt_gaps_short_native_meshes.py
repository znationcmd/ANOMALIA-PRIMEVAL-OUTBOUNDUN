"""Repair *missing* asphalt tiles on SKARVIK's 97 native paved route candidates.

Recover small skipped gaps with <=6m short genuine City Sample road meshes.
Only grade-compatible, planar, non-town-crossing patches may be placed.
Never invent drivable continuity: every remaining skipped tile is reported.
No forced landscape cuts, bridges, water crossings or SM5 driving claims.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MAP="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
MAP_FILE=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
OLD=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
BACKUP=ROOT/"Saved/SkarvikCity/GapFixSmallMeshV1_20261031/graded-before-repair.umap"
PLAN=Path(os.environ["SKARVIK_GAPFIX_PLAN"])
OUT=Path(os.environ["SKARVIK_GAPFIX_REPORT"])
LABEL="SKARVIK_CONTINUITY_PATCH_V1_"
ROADMESH="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
sourcePrefixes=("SKARVIK_EXPANSION_ROAD_","SKARVIK_EXPANSION_B2_ROAD_","SKARVIK_EXPANSION_C3_ROAD_")
report={"state":"FAILED","map":MAP,"actualNewPatchActors":0,
        "actualNewPatchMetres":0,"routesWithNewPatches":0,
        "fullyPatchedAdditionalRoutes":0,"totalCandidateMissingTiles":0,
        "stillUnrepairedBaseTiles":0,"roadContinuitySM5Driven":False,
        "waterBridgeCulvertsChecked":False,"buildingGameplayTested":False,
        "bigCityLoaded":False,"OriginalDModified":False,"routes":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
    ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Invalid isolated stage marker")
 for f in (MAP_FILE,D,CITY,OLD):
  if not f.is_file():raise RuntimeError("Missing protected native map "+str(f))
 if BACKUP.exists():raise RuntimeError("Gap fix batch attempted before, refuse duplicate")
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(data["roads"])!=382 or len(data["settlements"])!=125:
  raise RuntimeError("Untrusted road/settlement layout")
 source={r["id"]:r for r in data["roads"] if r.get("id","").startswith("SK-RX-")}
 protected={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (D,CITY,OLD)}
 terrain=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(terrain,"skarvik_graded_height"):
  raise RuntimeError("Native graded landscape sampler missing")
 mesh=unreal.EditorAssetLibrary.load_asset(ROADMESH)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("Actual City Sample road mesh not installed")
 box=mesh.get_bounds()
 dimX=2*float(box.box_extent.x)/100.
 dimY=2*float(box.box_extent.y)/100.
 if not (17<dimX<23 and 5<dimY<15):raise RuntimeError("Unexpected native source road mesh dimensions")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(MAP):raise RuntimeError("Cannot load 48km graded world")
 labels=[str(d.label) for d in (unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or [])]
 if sum(s.startswith("SKARVIK_GRADED_SITE_") for s in labels)!=1039:
  raise RuntimeError("Saved houses unexpectedly absent")
 counts=[sum(s.startswith(prefix) for s in labels) for prefix in (
   "SKARVIK_GRADED_ROAD_","SKARVIK_EXPANSION_ROAD_",
   "SKARVIK_EXPANSION_B2_ROAD_","SKARVIK_EXPANSION_C3_ROAD_")]
 if counts!=[126,1668,5157,6088]:
  raise RuntimeError("Expected previous verified 13039 real road actors; got "+str(counts))
 if any(s.startswith(LABEL) for s in labels):
  raise RuntimeError("Gap fix actors already present, refuse duplicate")
 report["previousRoadMeshesPreserved"]=sum(counts)
 report["previousBuildingMeshesPreserved"]=1039
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAP_FILE,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=hashlib.sha256(MAP_FILE.read_bytes()).hexdigest():
  raise RuntimeError("Failed safe graded map backup")
 def h(e,n):
  v=float(terrain.skarvik_graded_height(e*1000,n*1000))
  if not math.isfinite(v) or not -50<v<1900:raise RuntimeError("Non-finite height")
  return v
 def townclear(e,n):
  for town in data["settlements"]:
   if abs(e-town["eastKm"])<town["footprintKm"][0]/2+.013 and abs(n-town["northKm"])<town["footprintKm"][1]/2+.013:
    return False
  return True
 # Only those 97 source routes previously paved in batch A/B/C.
 existingroutes={}
 for road in source.values():
  for prefix in sourcePrefixes:
   stem=prefix+road["id"]+"_"
   existing=[lab for lab in labels if lab.startswith(stem)]
   if existing:
    existingroutes[road["id"]]=(prefix,{int(lab[len(stem):]) for lab in existing if lab[len(stem):].isdigit()})
    break
 if len(existingroutes)!=97:raise RuntimeError("Unexpected number of 97 previously paved batch road alignments: "+str(len(existingroutes)))
 for road_id,(prefix,already) in sorted(existingroutes.items()):
  road=source[road_id]
  intervals=[]
  for p0,p1 in zip(road["waypointsKm"],road["waypointsKm"][1:]):
   dist=math.hypot((p1[0]-p0[0])*1000.,(p1[1]-p0[1])*1000.)
   if dist<12:continue
   count=int(math.ceil(dist/19.))
   for k in range(count):
    t0=k/count;t1=(k+1)/count
    e0=p0[0]+(p1[0]-p0[0])*t0;n0=p0[1]+(p1[1]-p0[1])*t0
    e1=p0[0]+(p1[0]-p0[0])*t1;n1=p0[1]+(p1[1]-p0[1])*t1
    intervals.append((e0,n0,e1,n1))
  missing=[(idx,v) for idx,v in enumerate(intervals) if idx not in already]
  if not missing:continue
  report["totalCandidateMissingTiles"]+=len(missing)
  patched=0;actors_added=0;metres=0.;reasons={}
  for index,(e0,n0,e1,n1) in missing:
   # Re-grading with <=5m short road sections. Entire original 19m base tile
   # must pass checks; otherwise leave it unaltered and record remaining gap.
   kmspan=math.hypot(e1-e0,n1-n0)
   subdivisions=max(2,int(math.ceil(kmspan*1000/4.5)))
   subtiles=[]
   rejected=None
   for sub in range(subdivisions):
    a=sub/subdivisions;b=(sub+1)/subdivisions
    ea=e0+(e1-e0)*a;na=n0+(n1-n0)*a
    eb=e0+(e1-e0)*b;nb=n0+(n1-n0)*b
    em=(ea+eb)*.5;nm=(na+nb)*.5
    leng=math.hypot((eb-ea)*1000,(nb-na)*1000)
    if leng<1:rejected="short-or-degenerate";break
    if not all(townclear(x,y) for x,y in ((ea,na),(em,nm),(eb,nb))):
     rejected="town-or-building-footprint";break
    ha=h(ea,na);hb=h(eb,nb);hm=h(em,nm)
    grade=abs(hb-ha)/leng
    if grade>.15:rejected="grade-above-15-percent";break
    if abs((ha+hb)/2-hm)>.19:rejected="non-planar-vertical-relief";break
    vx=(eb-ea)*1000/leng;vy=(nb-na)*1000/leng
    # Width is 4m for this local road defect patch; 2m each side.
    nx=-vy;ny=vx;delta=.002
    sideH0=h(em+nx*delta,nm+ny*delta);sideH1=h(em-nx*delta,nm-ny*delta)
    if abs(sideH0-sideH1)>0.85:
     rejected="road-width-crossgrade-too-steep";break
    subtiles.append((em,nm,hm,leng,vx,vy,ha,hb,sub))
   if rejected:
    reasons[rejected]=reasons.get(rejected,0)+1
    continue
   for em,nm,hm,leng,vx,vy,ha,hb,sub in subtiles:
    bottom=(float(box.origin.z)-float(box.box_extent.z))/100.
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
       unreal.Vector(em*100000,-nm*100000,(hm-bottom+.06)*100))
    if not actor:raise RuntimeError("Native actor failed for gap "+road_id)
    actor.set_actor_label("{}{}_{}_{}".format(LABEL,road_id,index,sub))
    actor.tags=[unreal.Name("SKARVIK_GAP_REPAIR"),unreal.Name(road_id)]
    c=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not c or not c.set_static_mesh(mesh):raise RuntimeError("Genuine asphalt mesh reference failed")
    c.set_collision_profile_name("BlockAll")
    yaw=math.degrees(math.atan2(-vy,vx))
    pitch=math.degrees(math.atan2(hb-ha,leng))
    actor.set_actor_rotation(unreal.Rotator(pitch,yaw,0),False)
    actor.set_actor_scale3d(unreal.Vector(leng/dimX,4.0/dimY,1.))
    actors_added+=1;metres+=leng
   patched+=1
  report["stillUnrepairedBaseTiles"]+=len(missing)-patched
  report["actualNewPatchActors"]+=actors_added
  report["actualNewPatchMetres"]+=metres
  if patched:report["routesWithNewPatches"]+=1
  if patched==len(missing):report["fullyPatchedAdditionalRoutes"]+=1
  report["routes"].append({"id":road_id,"sourcePrefix":prefix,"baseTilesMissing":len(missing),
    "baseTilesPatched":patched,"baseTilesStillMissing":len(missing)-patched,
    "newRealMeshActors":actors_added,"newMeshMetres":round(metres,2),
    "blockReasons":reasons,"nativeDriveContinuityTested":False})
  unreal.log("SKARVIK_GAP_REPAIR_ROUTE={} missing={} repaired={} blocked={}".format(
    road_id,len(missing),patched,len(missing)-patched))
 if report["actualNewPatchActors"]<5:raise RuntimeError("No meaningful safe physical road gap patches available")
 if not levels.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Native asphalt patch actors not saved in World Partition")
 for file in (D,CITY,OLD):
  if hashlib.sha256(file.read_bytes()).hexdigest()!=protected[str(file)]:
   raise RuntimeError("Protected source unexpectedly modified")
 report["actualNewPatchMetres"]=round(report["actualNewPatchMetres"],2)
 report["state"]="SOME_PREVIOUS_ROAD_GAPS_REPAIRED_WITH_NATIVE_SHORT_ASPHALT_NOT_DRIVEN"
 unreal.log("SKARVIK_SAVED_REAL_ASPHALT_GAP_REPAIR_ACTORS="+str(report["actualNewPatchActors"]))
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_GAP_FIX_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
