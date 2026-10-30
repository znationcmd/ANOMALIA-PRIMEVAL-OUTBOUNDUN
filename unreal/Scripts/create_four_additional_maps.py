"""Author ONE real, independent Unreal World Partition landscape at a time.

Run only from UnrealEditor-Cmd on the isolated Windows UE5.8 project, after
the C++ WorldImportLibrary is compiled. Never replace an existing map.
Creates a real .umap, landscape height/collision, daytime and a PlayerStart.
This does not claim photorealism, finished content or a playable server.
"""
import json
import math
import os
import traceback
from pathlib import Path
import unreal

CONFIG={
 "KARSKOV": dict(side=30000,samples=3025,components=576,biome="cold fjords and taiga",
                  low=(.115,.15,.13),high=(.82,.86,.88),snow=520.),
 "VORGRAD": dict(side=30000,samples=3025,components=576,biome="continental river plains",
                  low=(.19,.24,.09),high=(.33,.30,.21),snow=300.),
 "NEMORIS": dict(side=20000,samples=2017,components=256,biome="ancient woodland and marshes",
                  low=(.055,.18,.09),high=(.21,.27,.16),snow=210.),
 "DRAKHEIM": dict(side=20000,samples=2017,components=256,biome="volcanic basalt highlands",
                  low=(.12,.11,.10),high=(.24,.16,.13),snow=660.),
 "SOLYNACALYRA": dict(side=15000,samples=1513,components=576,biome="paradise tropical islands and lagoons",
                  low=(.18,.38,.16),high=(.68,.78,.39),snow=500.),
 "NEXAVARKHOS": dict(side=10000,samples=1009,components=256,biome="devastated colony original impact wasteland",
                  low=(.13,.11,.10),high=(.39,.23,.14),snow=680.),
}
ROOT=Path(unreal.Paths.project_dir()).resolve()
NAME=os.environ.get("PRIGIMALIA_NEW_MAP","")
OUT=Path(os.environ.get("PRIGIMALIA_NEW_MAP_REPORT",str(ROOT/"Saved/FourWorlds"/((NAME or "invalid")+".json"))))
REPORT=dict(state="FAILED",name=NAME,generatedInUnreal=False,gameplayTested=False,
            photorealismValidated=False,networkTested=False,originalMapsModified=False)
try:
 if NAME not in CONFIG:raise RuntimeError("Refusing unknown map identifier")
 spec=CONFIG[NAME]
 package="/Game/Maps/PRIGIMALIA_"+NAME
 mapfile=ROOT/"Content/Maps"/("PRIGIMALIA_"+NAME+".umap")
 materials="/Game/Anomalia/World/NewMaps_"+NAME
 # World Partition's external objects must be preserved even if .umap is missing.
 guards=[mapfile,ROOT/"Content/__ExternalActors__/Maps"/("PRIGIMALIA_"+NAME),
         ROOT/"Content/__ExternalObjects__/Maps"/("PRIGIMALIA_"+NAME),
         ROOT/"Content/Anomalia/World"/("NewMaps_"+NAME)]
 if any(p.exists() for p in guards) or unreal.EditorAssetLibrary.does_asset_exist(package):
  raise RuntimeError("Existing or partly authored world preserved; never overwrite or resume blindly")
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not level or not actors:raise RuntimeError("UE editor subsystems not available")
 native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(native,"create_named_world_landscape") or not hasattr(native,"named_world_height"):
  raise RuntimeError("Compiled UE5.8 native named terrain methods required")

 # Material is explicitly a biome PREVIEW, not PBR photorealism certification.
 tools=unreal.AssetToolsHelpers.get_asset_tools()
 mat=tools.create_asset("M_BiomePreview",materials,unreal.Material,unreal.MaterialFactoryNew())
 if not mat:raise RuntimeError("Unable to create owned biome preview material")
 lib=unreal.MaterialEditingLibrary
 def node(cls,**props):
  obj=lib.create_material_expression(mat,cls)
  for key,value in props.items():obj.set_editor_property(key,value)
  return obj
 def connect(a,b,pin):
  if not lib.connect_material_expressions(a,"",b,pin):
   raise RuntimeError("Material input connection failed: "+pin)
 def color(rgb):
  return node(unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(*rgb,1))
 lower=color(spec["low"]);upper=color(spec["high"])
 pos=node(unreal.MaterialExpressionWorldPosition)
 mask=node(unreal.MaterialExpressionComponentMask,r=False,g=False,b=True,a=False)
 connect(pos,mask,"")
 start=node(unreal.MaterialExpressionSubtract,const_b=(spec["snow"]-90)*100.)
 connect(mask,start,"A")
 divide=node(unreal.MaterialExpressionDivide,const_b=18000.)
 connect(start,divide,"A")
 clamp=node(unreal.MaterialExpressionClamp)
 connect(divide,clamp,"")
 lerp=node(unreal.MaterialExpressionLinearInterpolate)
 connect(lower,lerp,"A");connect(upper,lerp,"B");connect(clamp,lerp,"Alpha")
 if not lib.connect_material_property(lerp,"",unreal.MaterialProperty.MP_BASE_COLOR):
  raise RuntimeError("Biome material base color failed")
 rough=node(unreal.MaterialExpressionConstant,r=.87)
 if not lib.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS):
  raise RuntimeError("Biome roughness failed")
 lib.recompile_material(mat)
 if not unreal.EditorAssetLibrary.save_loaded_asset(mat):raise RuntimeError("Preview material save failed")
 if not level.new_level(package,is_partitioned_world=True):
  raise RuntimeError("Native World Partition map creation failed")
 land=native.create_named_world_landscape(NAME)
 if not land:raise RuntimeError("Native terrain import failed; do not mark world as created")
 proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
 collision=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
 if components!=spec["components"] or collision!=spec["components"]:
  raise RuntimeError("Landscape heightfield/collision count mismatch")
 for a in proxies:a.set_editor_property("landscape_material",mat)
 def place(cls,label,xyz):
  obj=actors.spawn_actor_from_class(cls,unreal.Vector(*xyz))
  if not obj:raise RuntimeError("Failed to spawn actor "+label)
  obj.set_actor_label("PRIGIMALIA_"+NAME+"_"+label)
  obj.tags=[unreal.Name("PRIGIMALIA_"+NAME+"_Owner")]
  return obj
 sunlight=place(unreal.DirectionalLight,"Sun",(0,0,40000))
 sunlight.set_actor_rotation(unreal.Rotator(-48,-22,0),False)
 place(unreal.SkyLight,"SkyLight",(0,0,10000))
 place(unreal.SkyAtmosphere,"SkyAtmosphere",(0,0,0))
 # Search for a known dry, locally traversable spawn, not an arbitrary water coordinate.
 spawn=None
 for radius in (0,600,1200,2100,3500,5200):
  for angle in range(0,360,30):
   e=radius*math.cos(math.radians(angle));n=radius*math.sin(math.radians(angle))
   h=native.named_world_height(NAME,e,n)
   corners=[native.named_world_height(NAME,e+dx,n+dy) for dx,dy in
            ((-8,-8),(-8,8),(8,-8),(8,8))]
   if 8<h<400 and max(abs(v-h) for v in corners)<3.5:
    spawn=(e,n,h);break
  if spawn:break
 if not spawn:raise RuntimeError("No safe dry player start; do not save an unusable map")
 player=place(unreal.PlayerStart,"PlayerStart",(spawn[0]*100,-spawn[1]*100,spawn[2]*100+180))
 if not level.save_all_dirty_levels():raise RuntimeError("Native level save failed")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("World Partition external actor save failed")
 if not mapfile.is_file() or mapfile.stat().st_size<1024:
  raise RuntimeError("Expected native binary .umap not found")
 REPORT.update(state="NATIVE_WORLD_SAVED_NOT_PLAYTESTED",name=NAME,mapPackage=package,
               generatedInUnreal=True,sideMeters=spec["side"],areaKm2=(spec["side"]/1000)**2,
               heightSamplesPerSide=spec["samples"],landscapeComponents=components,
               collisionComponents=collision,landscapeProxies=len(proxies),
               playerStartMetres=spawn,visualMaterial="BIOME_PREVIEW_NOT_PHOTOREALISTIC",
               worldPartitionRequested=True,worldFileBytes=mapfile.stat().st_size)
except Exception as exc:
 REPORT["error"]=str(exc)
 REPORT["traceback"]=traceback.format_exc()
 raise
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 unreal.log("PRIGIMALIA_NEW_MAP_REPORT="+str(OUT))
