r"""Author real ANOMALIA static-mesh buildings for SKARVIK settlement parcels.
ONLY an isolated, marked C: Unreal staging project. Never touch original D:.
Creates an independent new World Partition settlement overlay aligned to SKARVIK XY.
No fake cube buildings, no CitySample crowds/vehicles, no false claim of interiors.
"""
import json,math,os,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
MARKER=ROOT/".skarvik-ci-stage-marker"
PLAN=Path(os.environ["SKARVIK_SETTLEMENT_LAYOUT"])
REPORT=Path(os.environ["SKARVIK_SETTLEMENT_AUTHOR_REPORT"])
LIMIT=int(os.environ.get("SKARVIK_SETTLEMENT_SITE_LIMIT","6"))
PACKAGE="/Game/Maps/SKARVIK_SETTLEMENTS_PILOT_v1" if LIMIT<125 else "/Game/Maps/SKARVIK_SETTLEMENTS_125_v2"
MODEL_PATHS={
 "wood":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
 "coastal":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
 "garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
 "apartment":"/Game/Anomalia/Buildings/Lot1/SM_hlm_8floors_v1",
 "residence":"/Game/Anomalia/Buildings/Expansion1/SM_residence_4floors",
 "townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
 "hospital":"/Game/Anomalia/Buildings/Expansion1/SM_hospital",
 "police":"/Game/Anomalia/Buildings/Expansion1/SM_police_station",
 "barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn",
 "fire":"/Game/Anomalia/Buildings/Expansion1/SM_fire_station"
}
report={"state":"FAILED","mapPackage":PACKAGE,"requestedSiteLimit":LIMIT,"adaptiveNucleusVersion":2,
 "buildingsPhysicallyPlaced":0,"settlementsWithRealBuildings":0,"settlements":[],
 "roadsBuilt":False,"enterableBuildingsPlaytested":False,"npcGameplayTested":False,
 "workingVehiclesTested":False,"originalDModified":False,"productionSkarvikModified":False}
try:
 if not (ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap").exists():
  raise RuntimeError("Source SKARVIK staged terrain map missing")
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or MARKER.read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Untrusted native stage project")
 if LIMIT not in (6,125):
  raise RuntimeError("Only validated 6-site pilot or full 125-site run is permitted")
 if not PLAN.is_file():
  raise RuntimeError("Missing committed SKARVIK settlement masterplan")
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 sites=data["settlements"][:LIMIT]
 if len(data["settlements"])!=125 or data["settlementTargets"]["total"]!=125:
  raise RuntimeError("Masterplan not precisely 125 original localities")
 counts={}
 for site in data["settlements"]:
  cls=site["settlementClass"];counts[cls]=counts.get(cls,0)+1
 if counts!={"major-city":10,"small-town":6,"town":26,"village":83}:
  raise RuntimeError("Unexpected 125-settlement class counts")
 if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE) or (ROOT/"Content/Maps"/(PACKAGE.split("/")[-1]+".umap")).exists():
  raise RuntimeError("This settlement world already exists; never overwrite an edited map")
 for d in ("Crowd","Vehicle"):
  if (ROOT/"Content"/d).exists():
   raise RuntimeError("Forbidden CitySample crowds or vehicles present")
 if not (Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")).is_file():
  raise RuntimeError("Protected original ANOMALIA map missing")
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(lib,"skarvik_city_height"):
  raise RuntimeError("Compiled 48km native height sampler missing")
 meshes={}
 for name,path in MODEL_PATHS.items():
  asset=unreal.EditorAssetLibrary.load_asset(path)
  if not isinstance(asset,unreal.StaticMesh):
   raise RuntimeError("Real building mesh missing, no placeholder substitution: "+path)
  bounds=asset.get_bounds()
  sizes=[bounds.box_extent.x*2/100,bounds.box_extent.y*2/100,bounds.box_extent.z*2/100]
  if not (2<min(sizes[:2]) and max(sizes[:2])<70):
   raise RuntimeError("Unexpected building mesh scale: "+name+" "+str(sizes))
  meshes[name]=(asset,bounds)
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels or not actors or not levels.new_level(PACKAGE,is_partitioned_world=True):
  raise RuntimeError("Could not create fresh, isolated World Partition settlement overlay")
 def height(east_m,north_m):
  v=float(lib.skarvik_city_height(east_m,north_m))
  if not -60<v<2000:raise RuntimeError("Invalid SKARVIK height: "+str(v))
  return v
 def model_for(cls,biome,k):
  if cls=="major-city":return ("apartment","residence","townhouse","hospital","police","fire","coastal")[k%7]
  if cls=="small-town":return ("townhouse","wood","coastal","residence","police","garage")[k%6]
  if cls=="town":return ("wood","townhouse","coastal","barn","garage","police")[k%6]
  return ("wood","coastal","barn","garage","townhouse")[k%5] if biome!="snow" else ("wood","barn","wood","garage","coastal")[k%5]
 building_targets={"major-city":24,"small-town":16,"town":12,"village":5}
 def count_buildable(site,requested,origin_e,origin_n):
  # Score local nuclei inside each reserved settlement footprint, not a relocated town.
  cols=int(math.ceil(math.sqrt(requested)))
  rows=int(math.ceil(requested/cols))
  spacing=52 if requested>=12 else 38
  valid=0
  grading=0.0
  for i in range(requested):
   column=i%cols;row=i//cols
   de=(column-(cols-1)/2)*spacing
   dn=(row-(rows-1)/2)*spacing
   name=model_for(site["settlementClass"],site["biome"],i)
   _mesh,bounds=meshes[name]
   hw=bounds.box_extent.x/100.0;hd=bounds.box_extent.y/100.0
   if (abs(de)+hw>site["footprintKm"][0]*500-10 or abs(dn)+hd>site["footprintKm"][1]*500-10):
    grading+=1000.0
    continue
   e,n=origin_e+de,origin_n+dn
   grades=[height(e+ox,n+oy) for ox in (-hw,hw) for oy in (-hd,hd)]
   delta=max(grades)-min(grades)
   grading+=min(100.0,delta)
   if delta<=5.0:valid+=1
  return valid,grading
 def choose_nucleus(site,requested,east_center,north_center):
  cols=int(math.ceil(math.sqrt(requested)))
  rows=int(math.ceil(requested/cols))
  spacing=52 if requested>=12 else 38
  max_dx=max(0,int(site["footprintKm"][0]*500-(cols-1)*spacing/2-45))
  max_dy=max(0,int(site["footprintKm"][1]*500-(rows-1)*spacing/2-45))
  first=count_buildable(site,requested,east_center,north_center)
  if first[0]==requested:return east_center,north_center,0,0,first[0]
  # Bounded deterministic search, 20 to 80 metres in villages, larger in cities.
  offsets=[0,40,-40,80,-80,120,-120,160,-160,240,-240,320,-320,480,-480,640,-640]
  options=[]
  for dx in offsets:
   if abs(dx)>max_dx:continue
   for dy in offsets:
    if abs(dy)>max_dy:continue
    options.append((dx,dy))
  options.sort(key=lambda z:(abs(z[0])+abs(z[1]),abs(z[0]),abs(z[1])))
  best=(-1,float("inf"),float("inf"),0,0)
  for dx,dy in options:
   good,grade=count_buildable(site,requested,east_center+dx,north_center+dy)
   candidate=(good,-grade,-(abs(dx)+abs(dy)),dx,dy)
   if (candidate[:3]>best[:3]):
    best=candidate
   if good==requested:
    break
  return east_center+best[3],north_center+best[4],best[3],best[4],best[0]
 for site in sites:
  ident=site["id"]
  if ident=="citysample":
   report["settlements"].append({"id":ident,"state":"CITY_SAMPLE_NATIVE_CORE_RESERVED","actualBuildingActors":0})
   continue
  requested=building_targets[site["settlementClass"]]
  cols=int(math.ceil(math.sqrt(requested)));spacing=52 if requested>=12 else 38
  east0=float(site["eastKm"])*1000;north0=float(site["northKm"])*1000
  east0,north0,shift_e,shift_n,expected_buildable=choose_nucleus(site,requested,east0,north0)
  unreal.log("SKARVIK_ADAPTIVE_SITE={} viable={} requested={} shiftEastM={} shiftNorthM={}".format(
   ident,expected_buildable,requested,shift_e,shift_n))
  placed=0;skipped=0;maxgrade=0.
  for i in range(requested):
   column=i%cols;row=i//cols
   dx=(column-(cols-1)/2)*spacing
   dy=(row-(math.ceil(requested/cols)-1)/2)*spacing
   east=east0+dx;north=north0+dy
   name=model_for(site["settlementClass"],site["biome"],i)
   mesh,bounds=meshes[name]
   wx=bounds.box_extent.x/100;wy=bounds.box_extent.y/100
   relief=[]
   for ox in (-wx,wx):
    for oy in (-wy,wy):
     relief.append(height(east+ox,north+oy))
   grade=max(relief)-min(relief)
   maxgrade=max(maxgrade,grade)
   if grade>5.0:
    skipped+=1;continue
   floor=max(relief)+0.05
   # Actual building bottom (not mesh pivot) stays at/just above real landscape.
   min_mesh_z=(bounds.origin.z-bounds.box_extent.z)/100
   pos=unreal.Vector(east*100,-north*100,(floor-min_mesh_z)*100)
   actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,pos)
   if not actor:raise RuntimeError("Could not spawn real building at "+ident)
   actor.set_actor_label("SKARVIK125_{}_{}_{}".format(ident,i,name))
   actor.tags=[unreal.Name("SKARVIK_SETTLEMENTS_125"),unreal.Name("SKARVIK_"+ident)]
   component=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not component or not component.set_static_mesh(mesh):
    raise RuntimeError("Native building mesh assignment failed: "+name)
   component.set_collision_profile_name("BlockAll")
   actor.set_actor_rotation(unreal.Rotator(0,180 if (row%2) else 0,0),False)
   placed+=1
  report["settlements"].append({
    "id":ident,"name":site["name"],"kind":site["settlementClass"],
    "expectedBuildingParcels":requested,"actualBuildingActors":placed,
    "skippedSteepParcels":skipped,"maxSampledReliefMeters":round(maxgrade,2),
    "constructionNucleusShiftEastM":shift_e,"constructionNucleusShiftNorthM":shift_n,
    "state":"REAL_UE_STATIC_MESHES_STAGED_UNPLAYTESTED" if placed else "NO_BUILDABLE_PARCEL_NEEDS_TERRAIN_REWORK"
   })
  report["buildingsPhysicallyPlaced"]+=placed
  if placed:report["settlementsWithRealBuildings"]+=1
  unreal.log("SKARVIK_NATIVE_SETTLEMENT_BUILT={} buildings={} skipped={}".format(ident,placed,skipped))
 if report["settlementsWithRealBuildings"]<len(sites)-1:
  raise RuntimeError("Some sites have no real building geometry; refuse declaring a complete overlay")
 if not levels.save_all_dirty_levels():
  raise RuntimeError("Could not save native settlement overlay world")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Could not save owned World Partition actor packages")
 report["state"]="PILOT_REAL_BUILDINGS_SAVED_NOT_PLAYTESTED" if LIMIT==6 else "125_SITE_REAL_BUILDINGS_SAVED_NOT_PLAYTESTED"
 report["worldPartition"]=True
 report["fullyPlayable"]=False
 unreal.log("SKARVIK_NATIVE_SETTLEMENT_OVERLAY_SAVED=true")
except Exception as exc:
 report["error"]=str(exc);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_NATIVE_SETTLEMENT_OVERLAY_ERROR="+str(exc))
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
