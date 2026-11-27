"""Populate the existing VERIFIED SKARVIK GRADED v2 48km terrain with real UE StaticMeshes.
This is an isolated C: staging change; never edits D: originals or the v1 map.
Only initial settlement architecture is authored. Does not certify CitySample or gameplay.
"""
import hashlib,json,math,os,shutil,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
TARGET="/Game/Maps/PRIGIMALIA_SKARVIK_GRADED_v2"
MAIN=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
ORIG=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
BACKUP=ROOT/"Saved/SkarvikCity/BeforePopulatingGradedV2/graded-v2-clean.umap"
PLAN=Path(os.environ["SKARVIK_GRADED_V2_POPULATE_PLAN"])
OUT=Path(os.environ["SKARVIK_GRADED_V2_POPULATE_REPORT"])
ASSETS={
 "wood":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
 "coastal":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
 "garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
 "apartment":"/Game/Anomalia/Buildings/Lot1/SM_hlm_8floors_v1",
 "residence":"/Game/Anomalia/Buildings/Expansion1/SM_residence_4floors",
 "townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
 "hospital":"/Game/Anomalia/Buildings/Expansion1/SM_hospital",
 "police":"/Game/Anomalia/Buildings/Expansion1/SM_police_station",
 "barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn",
 "fire":"/Game/Anomalia/Buildings/Expansion1/SM_fire_station",
}
REPORT={"state":"FAILED","mapPackage":TARGET,"buildingsPlaced":0,"settlementsBuilt":0,
 "landscapeRebuilt":False,"roadNetworkBuilt":False,"bigCityInstanced":False,
 "interiorsPlaytested":False,"NPCVehiclesPlaytested":False,"SM5GameTested":False,
 "DOriginalModified":False,"V1StageModified":False,"nativeWorldSaved":False,"sites":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Not C: isolated SKARVIK stage")
 if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted staged native project")
 if BACKUP.exists():raise RuntimeError("Prior population attempt found; do not duplicate 3D towns")
 for f in (MAIN,V1,ORIG):
  if not f.is_file():raise RuntimeError("Missing protected world "+str(f))
 for banned in ("Crowd","Vehicle"):
  if (ROOT/"Content"/banned).exists():raise RuntimeError("Unapproved City Sample simulation source exists")
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(data["settlements"])!=125 or len(data["roads"])!=382:
  raise RuntimeError("Unexpected 125-site / 382-road masterplan")
 originals={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (ORIG,V1)}
 clean_v2_hash=hashlib.sha256(MAIN.read_bytes()).hexdigest()
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(lib,"skarvik_graded_height"):raise RuntimeError("Compiled graded native terrain sampler missing")
 mesh={}
 for name,path in ASSETS.items():
  obj=unreal.EditorAssetLibrary.load_asset(path)
  if not isinstance(obj,unreal.StaticMesh):raise RuntimeError("Missing genuine StaticMesh "+name+" : "+path)
  bb=obj.get_bounds()
  sizes=(bb.box_extent.x*2/100,bb.box_extent.y*2/100,bb.box_extent.z*2/100)
  if min(sizes[:2])<2 or max(sizes[:2])>70:raise RuntimeError("Unreal building mesh dimensions invalid: "+str((name,sizes)))
  mesh[name]=(obj,bb)
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(TARGET):raise RuntimeError("Could not open native graded 48km World Partition map")
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if world.get_path_name().split(".")[0]!=TARGET:raise RuntimeError("Unexpected active editor map")
 descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
 if not any("Landscape" in str(d.class_) or "Landscape" in str(d.label) for d in descs):
  raise RuntimeError("Missing persisted graded LandscapeProxy descriptors")
 if any("SKARVIK_GRADED_SITE_" in str(d.label) for d in descs):
  raise RuntimeError("Settlement actors already exist in this map; refuse overlapping duplicate")
 BACKUP.parent.mkdir(parents=True,exist_ok=False)
 shutil.copy2(MAIN,BACKUP)
 if hashlib.sha256(BACKUP.read_bytes()).hexdigest()!=clean_v2_hash:
  raise RuntimeError("Graded map backup failed SHA256 verification")
 def height(e,n):return float(lib.skarvik_graded_height(e,n))
 # Candidate buildings by size and settlement class; never placeholder cuboids.
 choices={
   "major-city":("apartment","residence","townhouse","hospital","police","fire","coastal","wood"),
   "small-town":("townhouse","coastal","wood","residence","garage","police","barn"),
   "town":("wood","townhouse","coastal","garage","barn","police"),
   "village":("wood","coastal","barn","garage","townhouse"),
 }
 targets={"major-city":24,"small-town":16,"town":12,"village":5}
 for s in data["settlements"]:
  if s["id"]=="citysample":
   REPORT["sites"].append({"id":s["id"],"buildingsPlaced":0,"reservedForCitySample":True})
   continue
  typ=s["settlementClass"];n=targets[typ]
  cols=int(math.ceil(math.sqrt(n)));rows=int(math.ceil(n/cols))
  spacing={"major-city":74,"small-town":66,"town":57,"village":52}[typ]
  e0=float(s["eastKm"])*1000.;n0=float(s["northKm"])*1000.
  placed=[];declined=0;maxGrade=0.
  for i in range(n):
   ix=i%cols;iy=i//cols
   dx=(ix-(cols-1)/2)*spacing;dy=(iy-(rows-1)/2)*spacing
   e,north=e0+dx,n0+dy
   candidate=None
   for order in range(len(choices[typ])):
    name=choices[typ][(i+order)%len(choices[typ])]
    obj,bounds=mesh[name];hw=float(bounds.box_extent.x)/100.;hh=float(bounds.box_extent.y)/100.
    if (abs(dx)+hw+2 > s["footprintKm"][0]*500 or
        abs(dy)+hh+2 > s["footprintKm"][1]*500):continue
    if any(abs(dx-other[0])<(hw+other[2]+4) and abs(dy-other[1])<(hh+other[3]+4) for other in placed):continue
    h=[height(e+ox,north+oy) for ox in (-hw,hw) for oy in (-hh,hh)]
    grade=max(h)-min(h);maxGrade=max(maxGrade,grade)
    if grade>1.2:continue
    candidate=(name,obj,bounds,hw,hh,max(h))
    break
   if candidate is None:
    declined+=1;continue
   name,obj,bounds,hw,hh,ground=candidate
   bottom=(float(bounds.origin.z)-float(bounds.box_extent.z))/100.
   actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(e*100.,-north*100.,(ground-bottom+.03)*100.))
   if not actor:raise RuntimeError("Unreal actor spawn failed for "+s["id"])
   actor.set_actor_label("SKARVIK_GRADED_SITE_{}_{}_{}".format(s["id"],i,name))
   actor.tags=[unreal.Name("SKARVIK_GRADED_SITE"),unreal.Name("SKARVIK_"+s["id"])]
   comp=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not comp or not comp.set_static_mesh(obj):raise RuntimeError("Real mesh assignment failed "+name)
   comp.set_collision_profile_name("BlockAll")
   actor.set_actor_rotation(unreal.Rotator(0.,180. if iy%2 else 0.,0.),False)
   placed.append((dx,dy,hw,hh))
   REPORT["buildingsPlaced"]+=1
  REPORT["sites"].append({"id":s["id"],"name":s["name"],"class":typ,
   "sourceModelBuildingsPlaced":len(placed),"declinedDueToGradeOrOverlap":declined,
   "maxSampledGradeM":round(maxGrade,3)})
  if not placed:raise RuntimeError("Terrain or building overlap prevented all buildings in "+s["id"])
  REPORT["settlementsBuilt"]+=1
  unreal.log("SKARVIK_GRADED_SITE_GEOMETRY_BUILT={} actual={}".format(s["id"],len(placed)))
 if REPORT["settlementsBuilt"]!=124:raise RuntimeError("Some settlement empty")
 if REPORT["buildingsPlaced"]<620:raise RuntimeError("Insufficient actual 3D building content")
 if not levels.save_all_dirty_levels():raise RuntimeError("Could not save graded World Partition with 3D settlements")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Unable to save external actor packages")
 for f in (ORIG,V1):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=originals[str(f)]:
   raise RuntimeError("Protected original changed; audit stage")
 REPORT["state"]="124_SITES_HAVE_REAL_UE5_MESHES_ON_GRADED_WORLD_NOT_GAMEPLAY_TESTED"
 REPORT["nativeWorldSaved"]=True
 REPORT["backupOfCleanGradedV2"]=str(BACKUP)
 unreal.log("SKARVIK_GRADED_124_SETTLEMENT_REAL_MESHES_SAVED=true")
except Exception as exc:
 REPORT["error"]=str(exc);REPORT["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_GRADED_124_SETTLEMENT_SAVE_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(REPORT,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
