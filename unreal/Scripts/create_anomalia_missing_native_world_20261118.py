"""Create ONE missing Unreal World Partition .umap with a real native landscape.

Runs only in the original D:\ANOMALIA\unreal UE 5.8 editor, never overwrites
a .umap, never edits another world, never substitutes placeholders for houses.
Reports real landscape/collision and any error. Run for each of the 11
missing-world IDs only after the new native 11-world addon has compiled.
"""
import json,math,os,traceback
from pathlib import Path
import unreal

IDENT=os.environ.get("ANOMALIA_NEW_NATIVE_MAP_ID","").strip()
MANIFEST=Path(os.environ.get("ANOMALIA_ELEVEN_MAP_MANIFEST",""))
REPORT=Path(os.environ.get("ANOMALIA_NATIVE_MAP_REPORT",""))
ROOT=Path(unreal.Paths.project_dir()).resolve()
EXPECTED=Path(r"D:\ANOMALIA\unreal").resolve()
result={"identifier":IDENT,"state":"FAILED","originalMapsModified":False,
        "actualLandscapeSaved":False,"completeHousesBuilt":False,
        "settlementsPopulated":False,"waterBodiesInstalled":False,
        "undergroundTunnelsConstructed":False,"playtested":False,
        "newMapPackageOnly":True}
try:
 if not IDENT or not REPORT or not MANIFEST.is_file():
    raise RuntimeError("Required map ID, manifest, or report destination unavailable")
 if ROOT!=EXPECTED:raise RuntimeError("Wrong Unreal project: original D project required")
 if not (ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
    raise RuntimeError("Original SKARVIK map missing: do not touch project")
 manifest=json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
 specs=[m for m in manifest["missingMaps"] if m["nativeId"]==IDENT]
 if len(specs)!=1:raise RuntimeError("Not one exact allowlisted missing map")
 spec=specs[0]
 width,height=int(spec["widthMeters"]),int(spec["heightMeters"])
 if width<=0 or height<=0:raise RuntimeError("Unknown map geometry")
 pkg="/Game/Maps/PRIGIMALIA_"+IDENT
 if spec["packagePath"]!=pkg:raise RuntimeError("Map package not unique or valid")
 packageFile=ROOT/"Content"/"Maps"/("PRIGIMALIA_"+IDENT+".umap")
 actorDir=ROOT/"Content"/"__ExternalActors__"/"Maps"/("PRIGIMALIA_"+IDENT)
 objectDir=ROOT/"Content"/"__ExternalObjects__"/"Maps"/("PRIGIMALIA_"+IDENT)
 if any(path.exists() for path in (packageFile,actorDir,objectDir)) or unreal.EditorAssetLibrary.does_asset_exist(pkg):
    result.update(state="ALREADY_PRESENT_UNMODIFIED")
    raise RuntimeError("Package or partial World Partition external actor data already exists")
 native=(getattr(unreal,"AnomaliaPrimevalElevenWorldLibrary",None) or
         getattr(unreal,"AnomaliaZPrigimaliaElevenWorldLibrary",None))
 if not native or not hasattr(native,"create_named_world_landscape") or not hasattr(native,"named_world_height"):
    raise RuntimeError("New 11-map native UE5 module not loaded after build")
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 worldSubsystem=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
 if not level or not actors or not worldSubsystem:
    raise RuntimeError("Unreal editor subsystems not loaded")
 if not level.new_level(pkg,is_partitioned_world=True):
    raise RuntimeError("Cannot create unique new World Partition level")
 world=worldSubsystem.get_editor_world()
 if not world or world.get_path_name().split(".")[0]!=pkg:
    raise RuntimeError("Unexpected active editor map after new level creation")
 landscape=native.create_named_world_landscape(IDENT)
 if not landscape:raise RuntimeError("Native C++ landscape import returned None")
 proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
 collisions=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
 resolution=3025 if width==30000 and height==30000 else (2017 if width*height>=400000000 or IDENT in {"NASDARAS","FALC","MOKUPUNAWAI","VALHALLA_EXTINCTION"} else 1009)
 expected=((resolution-1)//126)**2
 if components!=expected or collisions!=expected:
    raise RuntimeError("Unreal landscape/component mismatch %d/%d vs %d"%(components,collisions,expected))
 def height_at(e,n):return float(native.named_world_height(IDENT,float(e),float(n)))
 # Find level, dry terrain near playable centre, never inside ocean/cliff.
 spawn=None
 for radius in [0,500,1150,1800,2700,4000,5400,7000,8500]:
  if radius>min(width,height)*.45:continue
  for deg in range(0,360,20):
   e=radius*math.cos(math.radians(deg));n=radius*math.sin(math.radians(deg))
   current=height_at(e,n)
   around=[height_at(e+dx,n+dy) for dx in (-12,12) for dy in (-12,12)]
   if 15<current<1500 and max(around)-min(around)<4:
    spawn=(e,n,current);break
  if spawn:break
 if not spawn:raise RuntimeError("No safe dry, reasonably flat player spawn in generated terrain")
 def spawn_actor(kind,label,e,n,offset):
  z=100.*height_at(e,n)+offset
  actor=actors.spawn_actor_from_class(kind,unreal.Vector(e*100.,-n*100.,z))
  if not actor:raise RuntimeError("Unable to spawn "+label)
  actor.set_actor_label("PRIGIMALIA_"+IDENT+"_"+label)
  return actor
 spawn_actor(unreal.PlayerStart,"PlayerStart",spawn[0],spawn[1],180)
 sun=spawn_actor(unreal.DirectionalLight,"DirectionalSun",0,0,50000)
 sun.set_actor_rotation(unreal.Rotator(-35.,-50.,0.),False)
 spawn_actor(unreal.SkyLight,"SkyLight",0,0,12000)
 spawn_actor(unreal.SkyAtmosphere,"SkyAtmosphere",0,0,0)
 if hasattr(unreal,"ExponentialHeightFog"):
  spawn_actor(unreal.ExponentialHeightFog,"AtmosphericHaze",0,0,1800)
 if not level.save_all_dirty_levels():raise RuntimeError("Failed to save new partitioned world level")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Failed saving new World Partition actor packages")
 if not packageFile.is_file() or packageFile.stat().st_size<=1024:
  raise RuntimeError("Real .umap not found or unexpectedly small after save")
 result.update(state="NEW_REAL_NATIVE_TERRAIN_SAVED_BUILDINGS_NOT_YET_PLACED",
   mapPackage=pkg,worldPartition=True,
   actualLandscapeSaved=True,unrealMapBytes=packageFile.stat().st_size,
   dimensionsMetres=[width,height],areaKm2=width*height/1000000,
   landscapeComponents=components,collisionComponents=collisions,playerStartMetres=spawn)
 unreal.log("ANOMALIA_MISSING_WORLD_CREATED="+IDENT+" "+str(packageFile))
except Exception as exc:
 result["error"]=str(exc)
 result["traceback"]=traceback.format_exc()
 unreal.log_error("ANOMALIA_MISSING_WORLD_ERROR="+IDENT+" "+str(exc))
finally:
 if REPORT:
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 unreal.log("ANOMALIA_NATIVE_WORLD_REPORT="+json.dumps({k:v for k,v in result.items() if k not in ("traceback",)}))
