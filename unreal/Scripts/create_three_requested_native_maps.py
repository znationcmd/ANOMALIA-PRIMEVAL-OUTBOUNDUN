"""Create ONLY the three requested draft landscapes in the actual D project.
Original procedural geography; no claim of surveyed geography, populated cities or playability.
Existing map packages and partial destinations are never overwritten.
"""
import json
import math
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
EXPECTED_ROOT=Path("D:/ANOMALIA/unreal").resolve()
IDENT=os.environ.get("PRIGIMALIA_THREE_MAP","")
SPECS={
 "YUDINAVIA":{"size":12500,"resolution":1009,"components":64,"display":"YUDINAVIA"},
 "MOSCOVIE":{"size":10000,"resolution":1009,"components":64,"display":"MOSCOVIE"},
 "CORSIVIA":{"size":15000,"resolution":1009,"components":64,"display":"CORSIVIA"}
}
REPORT=Path(os.environ.get("PRIGIMALIA_THREE_REPORT",str(ROOT/"Saved/NewFourMaps"/(IDENT+".json"))))
result={"state":"BLOCKED","name":IDENT,"actualLandscapeSaved":False,
 "waterRendered":False,"vegetationPopulated":False,"fullDeathmatchImplemented":False,
 "walkableIceValidated":False,"SM5Playtested":False,"existingMapsModified":False,"geographicSurveyValidated":False,"settlementsPopulated":False}
try:
 if IDENT not in SPECS:raise RuntimeError("Unknown new world, refuse editing")
 if ROOT != EXPECTED_ROOT:
  raise RuntimeError("Refuse another project: actual D project required")
 if not Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
  raise RuntimeError("Existing original SKARVIK source unexpectedly absent")
 spec=SPECS[IDENT]
 pkg="/Game/Maps/PRIGIMALIA_"+IDENT
 file=ROOT/"Content/Maps"/("PRIGIMALIA_"+IDENT+".umap")
 external=ROOT/"Content/__ExternalActors__/Maps"/("PRIGIMALIA_"+IDENT)
 external2=ROOT/"Content/__ExternalObjects__/Maps"/("PRIGIMALIA_"+IDENT)
 if file.exists() or external.exists() or external2.exists() or unreal.EditorAssetLibrary.does_asset_exist(pkg):
  raise RuntimeError("Map or partial World Partition data already exists, refuse overwrite")
 native=getattr(unreal,"AnomaliaWorldImportLibrary",None) or getattr(unreal,"AnomaliaPrimevalWorldImportLibrary",None) or getattr(unreal,"AnomaliaZPrigimaliaWorldImportLibrary",None)
 if not native or not hasattr(native,"create_named_world_landscape") or not hasattr(native,"named_world_height"):
  raise RuntimeError("Native C++ 4-map terrain module is not compiled and loaded")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels or not actors or not levels.new_level(pkg,is_partitioned_world=True):
  raise RuntimeError("Cannot create unique World Partition world")
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 if not world or world.get_path_name().split(".")[0]!=pkg:
  raise RuntimeError("Wrong map active, refuse terrain generation")
 terrain=native.create_named_world_landscape(IDENT)
 if not terrain:raise RuntimeError("Native C++ landscape creation failed")
 landscapes=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in landscapes)
 collisions=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in landscapes)
 if components!=spec["components"] or collisions!=spec["components"]:
  raise RuntimeError("World Partition landscape components/collision mismatch: {} / {}".format(components,collisions))
 def height(e,n):return float(native.named_world_height(IDENT,e,n))
 # Find a dry spawn, never place a player inside an ocean or traversable ice.
 spawn=None
 for radius in [0,300,650,1100,1750,2700,3800,4600,6200]:
  if radius>spec["size"]*.48:continue
  for deg in range(0,360,20):
   e=radius*math.cos(math.radians(deg));n=radius*math.sin(math.radians(deg))
   h=height(e,n)
   footprint=[height(e+dx,n+dy) for dx in (-8,8) for dy in (-8,8)]
   if 8<h<450 and max(footprint)-min(footprint)<3.0:
    spawn=(e,n,h);break
  if spawn:break
 if not spawn:raise RuntimeError("No verified dry/level PlayerStart")
 def place(actor_type,label,x,y,z):
  actor=actors.spawn_actor_from_class(actor_type,unreal.Vector(x,y,z))
  if not actor:raise RuntimeError("Failed to create native "+label)
  actor.set_actor_label("PRIGIMALIA_"+IDENT+"_"+label)
  return actor
 place(unreal.PlayerStart,"PlayerStart",spawn[0]*100,-spawn[1]*100,spawn[2]*100+180)
 sun=place(unreal.DirectionalLight,"Sun",0,0,55000)
 sun.set_actor_rotation(unreal.Rotator(-43,-30,0),False)
 place(unreal.SkyLight,"SkyLight",0,0,13000)
 place(unreal.SkyAtmosphere,"SkyAtmosphere",0,0,0)
 if not levels.save_all_dirty_levels():raise RuntimeError("Failed saving native world map")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Failed saving native World Partition actor data")
 if not file.is_file() or file.stat().st_size<1024:
  raise RuntimeError("New world .umap missing or empty after Unreal save")
 result.update(state="NEW_NATIVE_TERRAIN_SAVED_NOT_PLAYTESTED",mapPackage=pkg,
   widthMetres=spec["size"],heightMetres=spec["size"],
   landscapeComponents=components,collisionComponents=collisions,
   playerStartMetres=spawn,actualLandscapeSaved=True,worldPartition=True,
   unrealMapFileBytes=file.stat().st_size)
 unreal.log("PRIGIMALIA_NEW_FOUR_NATIVE_TERRAIN_SAVED="+IDENT)
except Exception as exc:
 result["error"]=str(exc)
 result["traceback"]=traceback.format_exc()
 unreal.log_error("PRIGIMALIA_NEW_FOUR_NATIVE_ERROR="+str(exc))
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 unreal.log("PRIGIMALIA_THREE_REPORT="+str(REPORT))

