"""Create one real CHERNASKALUXRIA World Partition .umap and import approved terrain tiles.

Execute with UnrealEditor-Cmd and the installed compiled editor. Uses only the
new /Game/Maps/PRIGIMALIA_CHERNASKALUXRIA world. Fails closed on duplicate tiles.
Never touches SKARVIK/DRAZOVIA/other maps, their saves or user project directories.
A one-tile test is NOT a completed 100km native world.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
MAPFILE=ROOT/"Content/Maps/PRIGIMALIA_CHERNASKALUXRIA.umap"
SRC=ROOT/"TerrainSource/CHERNASKALUXRIA"
MODE=os.environ.get("PRIGIMALIA_CH_MODE","initialize")
COL=int(os.environ.get("PRIGIMALIA_CH_COL","10"))
ROW=int(os.environ.get("PRIGIMALIA_CH_ROW","10"))
REPORT=Path(os.environ.get("PRIGIMALIA_CH_REPORT",
                          str(ROOT/"Saved/CHERNASKALUXRIA"/f"{MODE}-{COL:02}-{ROW:02}.json")))
TILE_NAME=f"CHERNASKALUXRIA_x{COL:02}_y{ROW:02}"
DATA=SRC/(TILE_NAME+".r16")
OWNER="PRIGIMALIA_CHERNASKALUXRIA"
STATUS=dict(state="FAILED",mode=MODE,mapPackage=PACKAGE,
            tile=[COL,ROW],nativeSaved=False,completedNativeTiles=0,
            plannedTiles=400,photorealismValidated=False,gameplayTested=False,
            multiplayerTested=False,otherWorldsModified=False)

def author():
 if MODE not in ("initialize","tile"):
  raise RuntimeError("Invalid authoring mode")
 if not 0<=COL<20 or not 0<=ROW<20:
  raise RuntimeError("Invalid tile indices")
 if not DATA.is_file() or DATA.stat().st_size!=253*253*2:
  raise RuntimeError("Exact raw heightfield missing or invalid")
 raw=DATA.read_bytes()
 digest=hashlib.sha256(raw).hexdigest()
 native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(native,"create_chernaskaluxria_landscape_tile"):
  raise RuntimeError("Native editor C++ 100km landscape importer not compiled")
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not level or not actors:
  raise RuntimeError("This script must run from Unreal Editor")
 if MODE=="initialize":
  if MAPFILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
   raise RuntimeError("Existing world preserved; never recreate or overwrite")
  ext=ROOT/"Content/__ExternalActors__/Maps/PRIGIMALIA_CHERNASKALUXRIA"
  if ext.exists():
   raise RuntimeError("Orphan or partial external actors must be investigated first")
  if not level.new_level(PACKAGE,is_partitioned_world=True):
   raise RuntimeError("New World Partition .umap creation failed")
 else:
  if not MAPFILE.is_file():
   raise RuntimeError("Existing native world required before importing another tile")
  proof=ROOT/"Saved/CHERNASKALUXRIA/created-owner.json"
  if not proof.is_file():
   raise RuntimeError("Ownership manifest missing")
  info=json.loads(proof.read_text(encoding="utf-8"))
  if info.get("mapPackage")!=PACKAGE or info.get("owner")!=OWNER:
   raise RuntimeError("World ownership changed; refusing edit")
  existing=ROOT/"Saved/CHERNASKALUXRIA"/(TILE_NAME+".json")
  if existing.exists():
   raise RuntimeError("Existing imported tile receipt preserved; no overwriting")
  if not level.load_level(PACKAGE):
   raise RuntimeError("Existing native world cannot be loaded")
 # Strong map identity check: no tile creation in any other loaded world.
 world=unreal.EditorLevelLibrary.get_editor_world()
 if not world or str(world.get_outermost().get_name())!=PACKAGE:
  raise RuntimeError("The editor is not inside the CHERNASKALUXRIA package")
 labels={a.get_actor_label() for a in actors.get_all_level_actors()}
 if TILE_NAME in labels:
  raise RuntimeError("Existing landscape tile actor would be overwritten")
 tile=native.create_chernaskaluxria_landscape_tile(COL,ROW)
 if not tile:
  raise RuntimeError("Native C++ landscape import failed")
 if len(tile.get_components_by_class(unreal.LandscapeComponent))!=4:
  raise RuntimeError("Imported landscape must have four real components")
 if MODE=="initialize":
  def spawn(cls,label,xyz):
   a=actors.spawn_actor_from_class(cls,unreal.Vector(*xyz))
   if not a:raise RuntimeError("Could not spawn "+label)
   a.set_actor_label(OWNER+"_"+label)
   a.tags=[unreal.Name(OWNER)]
   return a
  sun=spawn(unreal.DirectionalLight,"Sun",(0,0,100000))
  sun.set_actor_rotation(unreal.Rotator(-48,-20,0),False)
  spawn(unreal.SkyLight,"SkyLight",(0,0,5000))
  spawn(unreal.SkyAtmosphere,"SkyAtmosphere",(0,0,0))
  # The central tile bounds are 0..5km east and 0..5km south.
  # Place spawn near its centre on the *imported* height (not at sea level).
  middle_code=struct.unpack_from("<H",raw,(126*253+126)*2)[0]
  height_metres=(middle_code-32768)/16.
  spawn(unreal.PlayerStart,"FirstTestSpawn",(250000,250000,height_metres*100+180))
 if not level.save_all_dirty_levels():
  raise RuntimeError("Unable to save World Partition world")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Unable to save external landscape actor packages")
 if not MAPFILE.is_file() or MAPFILE.stat().st_size<1024:
  raise RuntimeError("Real Unreal binary world file was not saved")
 # Owner/tile manifest only emitted AFTER native assets were persisted.
 receipt=ROOT/"Saved/CHERNASKALUXRIA"/(TILE_NAME+".json")
 receipt.parent.mkdir(parents=True,exist_ok=True)
 with receipt.open("x",encoding="utf-8") as writer:
  json.dump(dict(mapPackage=PACKAGE,tile=TILE_NAME,col=COL,row=ROW,
                 sourceSha256=digest,worldFileBytes=MAPFILE.stat().st_size,
                 state="NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED"),writer,indent=2)
 if MODE=="initialize":
  owner=ROOT/"Saved/CHERNASKALUXRIA/created-owner.json"
  with owner.open("x",encoding="utf-8") as writer:
   json.dump(dict(owner=OWNER,mapPackage=PACKAGE,tilesExpected=400,
                  firstTile=TILE_NAME,sourceSha256=digest,
                  state="NATIVE_WORLD_PARTIAL_ONLY"),writer,indent=2)
 STATUS.update(state="NATIVE_PARTIAL_WORLD_SAVED_NOT_PLAYTESTED",
               nativeSaved=True,completedNativeTiles=1,
               sourceSha256=digest,umapBytes=MAPFILE.stat().st_size,
               receipt=str(receipt),worldPartition=True)

try:
 author()
except Exception as e:
 STATUS["error"]=str(e)
 STATUS["traceback"]=traceback.format_exc()
 raise
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 with REPORT.open("x",encoding="utf-8") as stream:
  json.dump(STATUS,stream,indent=2,ensure_ascii=False)
 unreal.log("PRIGIMALIA_CHERNASKALUXRIA_REPORT="+str(REPORT))
