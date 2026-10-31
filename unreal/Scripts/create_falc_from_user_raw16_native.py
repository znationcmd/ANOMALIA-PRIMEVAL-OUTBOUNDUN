"""Safe REAL UE5.8 F.A.L.C (26.5 km) from user image-derived RAW16.

Requires the exact supplied master RAW16 SHA256; never substitute a procedural
map or regenerate unrelated coastlines. World Partition grid split and gameplay
testing deliberately deferred. Writes only a new /Game/Maps/PRIGIMALIA_FALC.
"""
import hashlib,os,json,struct,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
EXPECTED_ROOT=r"d:\anomaliaz-prigimalia\unreal"
PACKAGE="/Game/Maps/PRIGIMALIA_FALC"
UMAP=ROOT/"Content/Maps/PRIGIMALIA_FALC.umap"
RAW=ROOT/"TerrainSource/FALC/FALC_26_5KM_MASTER_2017.r16"
DIGEST="1d3ff52ed30338b59e6130a37aacc7e2a34367b7bc3b28faf4897b3bcfe6b5b7"
REPORT=Path(os.environ["ANOMALIA_FALC_NATIVE_REPORT"])
state={"status":"FAILED","source":"user-supplied-photo-derived-RAW16","masterSha256":DIGEST,
       "world":PACKAGE,"sourceElevationSurveyed":False,"gameplayTested":False,
       "finalWorldPartitionGridValidated":False,"otherMapsModified":False}
def run():
 if str(ROOT).replace("/","\\").lower().rstrip("\\")!=EXPECTED_ROOT:
  raise RuntimeError("F.A.L.C import refused outside isolated stage")
 if not RAW.is_file() or RAW.stat().st_size!=2017*2017*2:
  raise RuntimeError("F.A.L.C exact 2017x2017 raw not staged from user ZIP")
 raw=RAW.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=DIGEST:
  raise RuntimeError("F.A.L.C raw content SHA256 mismatch: refusing replacement")
 guards=[UMAP,ROOT/"Content/__ExternalActors__/Maps/PRIGIMALIA_FALC",
         ROOT/"Content/__ExternalObjects__/Maps/PRIGIMALIA_FALC"]
 if any(x.exists() for x in guards) or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
  raise RuntimeError("F.A.L.C level or external actor files already present: no overwrite")
 important=(ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap",
            ROOT/"Content/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate.umap",
            ROOT/"Content/Maps/PRIGIMALIA_KOLCHIEM_ORIGINS_FULL.umap")
 for p in important:
  if not p.is_file():raise RuntimeError("Missing protected map "+str(p))
 originals={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in important}
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(native,"create_falc_reference_landscape") or not hasattr(native,"inspect_falc_reference_components"):
  raise RuntimeError("F.A.L.C native C++ importer+inspector not compiled")
 if not level.new_level(PACKAGE,is_partitioned_world=True):
  raise RuntimeError("F.A.L.C independent World Partition creation failed")
 world=unreal.EditorLevelLibrary.get_editor_world()
 if not world or world.get_outermost().get_name()!=PACKAGE:
  raise RuntimeError("Refusing to author on a different Unreal world")
 land=native.create_falc_reference_landscape()
 if not land or native.inspect_falc_reference_components(land)!=256:
  raise RuntimeError("Native Landscape geometry/component verification failed")
 # Search a dry, fairly level spawn instead of placing a survivor underwater.
 axis=2017
 start=None
 for rad in (0,200,400,600,800):
  for yoff in (0,-rad,rad):
   for xoff in (0,-rad,rad):
    x=min(axis-2,max(1,axis//2+xoff))
    y=min(axis-2,max(1,axis//2+yoff))
    code=struct.unpack_from("<H",raw,2*(y*axis+x))[0]
    if code<=32768:continue
    around=[struct.unpack_from("<H",raw,2*((y+dy)*axis+x+dx))[0] for dx,dy in ((-2,-2),(2,-2),(-2,2),(2,2))]
    if min(around)>32768 and max(abs(z-code) for z in around)<200:
     start=(x,y,(code-32768)/16)
     break
   if start:break
  if start:break
 if start:
  x,y,z=start
  pos=unreal.Vector(-1325000+x*(2650000/2016),-1325000+y*(2650000/2016),z*100+180)
  player=actors.spawn_actor_from_class(unreal.PlayerStart,pos)
  if player:player.set_actor_label("FALC_ProvisionalPlayerStart")
 sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,50000))
 if sun:sun.set_actor_label("FALC_Sun")
 sky=actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
 if sky:sky.set_actor_label("FALC_Sky")
 if not level.save_all_dirty_levels():raise RuntimeError("F.A.L.C .umap save failed")
 if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("F.A.L.C World Partition external actor save failed")
 if not UMAP.is_file() or UMAP.stat().st_size<1024:
  raise RuntimeError("F.A.L.C real .umap missing after save")
 for p in important:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=originals[str(p)]:
   raise RuntimeError("Protected map changed during F.A.L.C native import: "+str(p))
 state.update(status="NATIVE_FALC_2017_RAW16_WORLD_SAVED_NOT_PLAYTESTED",
              nativeLandscapeComponents=256,worldPartition=True,umapBytes=UMAP.stat().st_size,
              provisionalSpawnSample=start,protectedMapsHashUnchanged=True)
try:
 run()
except Exception as e:
 state["error"]=str(e)
 state["traceback"]=traceback.format_exc()
 raise
finally:
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 if REPORT.exists():raise RuntimeError("Refuse to overwrite earlier F.A.L.C native report")
 REPORT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 unreal.log("FALC_NATIVE_IMPORT_REPORT="+str(REPORT))
