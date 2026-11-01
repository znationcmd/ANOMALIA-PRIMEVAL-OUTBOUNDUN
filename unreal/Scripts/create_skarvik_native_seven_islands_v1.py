"""Build a VERSIONED full 48km SKARVIK island landscape plus 15 island locality cores.
Uses original native archipelago ocean/island height, not graded-v2 predominant land.
This never edits the populated graded world, its 14,798+ original road actors,
Big City, existing original Archipelago D:, or original World Partition packages.
This is the FIRST island-core native map, NOT a migrated or SM5-playtested game.
"""
import os,json,hashlib,traceback,math
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1"
NEW=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap"
D=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
STAGE_V1=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_CITY_v1.umap"
GRADED=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
CITY=ROOT/"Content/Map/Big_City_LVL.umap"
PLAN=Path(os.environ["SKARVIK_ISLANDS_NATIVE_PLAN"])
OUT=Path(os.environ["SKARVIK_ISLANDS_NATIVE_REPORT"])
ASSET_PATHS={
 "wood":"/Game/Anomalia/InteractiveRealismReview_v1/wood_house_enterable/SM_wood_house_enterable",
 "coastal":"/Game/Anomalia/Buildings/Lot1/SM_coastal_house_v1",
 "garage":"/Game/Anomalia/Buildings/Lot1/SM_garage_v1",
 "townhouse":"/Game/Anomalia/Buildings/Expansion1/SM_townhouse",
 "residence":"/Game/Anomalia/Buildings/Expansion1/SM_residence_4floors",
 "barn":"/Game/Anomalia/Buildings/Expansion1/SM_farm_barn",
}
LABEL="SKARVIK_ISLAND_V1_"
report={"state":"FAILED","newWorldPackage":PKG,"newIsolatedNativeWorld":True,
        "sevenDetachedIslandsOnSourceTopography":True,"landscapeComponentCount":0,
        "collisionComponentCount":0,"settlementsWithReal3DBuildingCores":0,
        "realNativeBuildingActorsSaved":0,"skippedBuildingPositions":0,
        "seaWaterSimulationEnabled":False,"coastlineMeshRenderedInSM5":False,
        "mainland125LocationsMigrated":False,"originalGradedWorldModified":False,
        "BigCity4KmImported":False,"boatsDocksTrafficTested":False,
        "fullGameSM5Playtested":False,"sites":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
   ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Not verified isolated C stage")
 if NEW.exists() or unreal.EditorAssetLibrary.does_asset_exist(PKG):
  raise RuntimeError("Island native world already exists: never overwrite or duplicate")
 for f in (D,STAGE_V1,GRADED,CITY):
  if not f.is_file():raise RuntimeError("Missing protected original world "+str(f))
 hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (D,STAGE_V1,GRADED,CITY)}
 data=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(data["islands"])!=7 or data["targetTotalLocalities"]!=15:
  raise RuntimeError("Unapproved seven island / 15 locality layout")
 sites=[dict(s,islandId=isl["id"]) for isl in data["islands"] for s in isl["settlements"]]
 if len(sites)!=15 or len({s["id"] for s in sites})!=15:
  raise RuntimeError("Duplicate or missing island towns")
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(lib,"create_skarvik_islands_v1_landscape") or not hasattr(lib,"archipelago_height"):
  raise RuntimeError("Islands v1 native landscape C++ function unavailable: compile editor first")
 assets={}
 for name,pkg in ASSET_PATHS.items():
  asset=unreal.EditorAssetLibrary.load_asset(pkg)
  if not isinstance(asset,unreal.StaticMesh):
   raise RuntimeError("Genuine native house mesh absent: "+pkg)
  bb=asset.get_bounds()
  hw=float(bb.box_extent.x)/100.
  hd=float(bb.box_extent.y)/100.
  if min(hw,hd)<1.5 or max(hw,hd)>35:
   raise RuntimeError("Unreal actor mesh model outside safe native house dimensions "+pkg)
  assets[name]=(asset,bb,hw,hd)
 def h(e,n):
  value=float(lib.archipelago_height(float(e),float(n)))
  if not math.isfinite(value) or value< -500 or value>2000:
   raise RuntimeError("Unreasonable original island height")
  return value
 # Perform complete dry-site planning BEFORE creating the Unreal level.
 # No coast or sea floor footprints; no place-on-water shortcuts.
 plans=[]
 for site in sites:
  e0=float(site["eastKm"])*1000.
  n0=float(site["northKm"])*1000.
  target=int(site["targetBuildingCoreCount"])
  approved=[]
  for radius in range(0,551,30):
   offsets=[(0,0)] if radius==0 else [
      (dx,dy) for dx in range(-radius,radius+1,30) for dy in range(-radius,radius+1,30)
      if max(abs(dx),abs(dy))==radius]
   for dx,dy in offsets:
    if len(approved)>=target:break
    e=e0+dx;n=n0+dy
    if abs(e)>23600 or abs(n)>23600:continue
    name=list(ASSET_PATHS)[(len(approved)+len(site["id"])+radius//30)%len(ASSET_PATHS)]
    mesh,bb,hw,hd=assets[name]
    ground=[h(e+sx*hw,n+sy*hd) for sx in (-1,0,1) for sy in (-1,0,1)]
    grade=max(ground)-min(ground)
    if min(ground)<=6.5 or grade>1.4:continue
    if any(abs(e-a["east"]) < hw+a["halfW"]+8 and
           abs(n-a["north"]) < hd+a["halfD"]+8 for a in approved):continue
    bottom=(float(bb.origin.z)-float(bb.box_extent.z))/100.
    approved.append({"assetKey":name,"east":e,"north":n,
       "height":max(ground)-bottom+.03,"groundTop":max(ground),
       "sourceGroundMin":min(ground),"sampledBuildingGradeM":grade,
       "halfW":hw,"halfD":hd,"siteId":site["id"],"islandId":site["islandId"]})
   if len(approved)>=target:break
  if len(approved)<4:
   raise RuntimeError("No safe dry 3D building core on actual offshore island: "+
     site["name"]+" candidates="+str(len(approved)))
  plans.append((site,approved))
  report["sites"].append({"id":site["id"],"name":site["name"],
     "islandId":site["islandId"],"intendedBuildings":target,
     "dryGradeApprovedBuildings":len(approved),
     "nativeCoreOnlyNotFullTown":True})
  report["skippedBuildingPositions"]+=max(0,target-len(approved))
 if len(plans)!=15 or not all(pts for _,pts in plans):
  raise RuntimeError("Islands dry-safe settlement plan failed preflight")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.new_level(PKG,is_partitioned_world=True):
  raise RuntimeError("Cannot create isolated islands 48km World Partition level")
 landscape=lib.create_skarvik_islands_v1_landscape()
 if not landscape:raise RuntimeError("Native original-coast archipelago Landscape import failed")
 proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
 collisions=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
 if components!=576 or collisions!=576:
  raise RuntimeError("Native islands terrain/collision components missing: "+str((components,collisions)))
 report["landscapeComponentCount"]=components
 report["collisionComponentCount"]=collisions
 for site,approved in plans:
  for index,p in enumerate(approved):
   mesh=assets[p["assetKey"]][0]
   # North-to-UE negative Y is identical to every existing SKARVIK map.
   actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,
     unreal.Vector(p["east"]*100.,-p["north"]*100.,p["height"]*100.))
   if not actor:raise RuntimeError("Native island building actor spawning failed")
   actor.set_actor_label("{}{}_{}_{:03d}_{}".format(LABEL,site["islandId"],site["id"],index,p["assetKey"]))
   actor.tags=[unreal.Name("SKARVIK_ISLANDS_SOURCE_V1"),unreal.Name("SKARVIK_ISLAND_"+site["islandId"]),
               unreal.Name("SKARVIK_SITE_"+site["id"])]
   comp=actor.get_component_by_class(unreal.StaticMeshComponent)
   if not comp or not comp.set_static_mesh(mesh):
    raise RuntimeError("Genuine island building static mesh assignment failed")
   comp.set_collision_profile_name("BlockAll")
   actor.set_actor_rotation(unreal.Rotator(0.,180. if index%2 else 0.,0.),False)
   report["realNativeBuildingActorsSaved"]+=1
  report["settlementsWithReal3DBuildingCores"]+=1
 # This is not a full water gameplay simulation; preview geometry only.
 if report["realNativeBuildingActorsSaved"]<95:
  raise RuntimeError("Insufficient dry native island architecture to certify first 15 cores")
 if not levels.save_all_dirty_levels():
  raise RuntimeError("Could not save new native island map")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Could not save native island World Partition external actor packages")
 if not NEW.is_file() or NEW.stat().st_size<1024:
  raise RuntimeError("New native islands .umap missing")
 for file in (D,STAGE_V1,GRADED,CITY):
  if hashlib.sha256(file.read_bytes()).hexdigest()!=hashes[str(file)]:
   raise RuntimeError("Protected production/graded world hash changed")
 report["state"]="NEW_NATIVE_48KM_SEVEN_ISLAND_WORLD_WITH_FIFTEEN_DRY_REAL_BUILDING_CORES_SAVED_NOT_PLAYTESTED"
 report["nativeMapSaved"]=True
 report["newWorldBytes"]=NEW.stat().st_size
 unreal.log("SKARVIK_NEW_SEVEN_NATIVE_ISLANDS_DRY_SETTLEMENT_BUILDINGS="+str(report["realNativeBuildingActorsSaved"]))
except Exception as exc:
 report["error"]=str(exc);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_ISLAND_NATIVE_WORLD_AUTHOR_FAILED="+str(exc))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
