"""One-time native final SKARVIK 48km island-and-mainland coastline landscape.
Creates a NEW World Partition level; source graded map, original D:, first island
map and CitySample never overwritten. No buildings/roads imported in this phase.
"""
import os,json,hashlib,traceback,math
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PKG="/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
FILE=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
SOURCES=(Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap"),
         ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
         ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
         ROOT/"Content/Map/Big_City_LVL.umap")
PLAN=Path(os.environ["SKARVIK_FINAL_NATIVE_PLAN"])
OUT=Path(os.environ["SKARVIK_FINAL_NATIVE_RESULT"])
report={"state":"FAILED","world":PKG,"sourceMapsModified":False,
        "levelSaved":False,"nativeLandscapeAndCollisionCount":0,
        "all125SitesRelocatedAndMigrated":False,"citySampleActorMigrated":False,
        "sourceRoadsRebuilt":False,"SM5VisualPlaytestPassed":False,
        "islandsCoastlineRenderedWithWater":False}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
   ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Not the isolated authorized staging project")
 if FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(PKG):
  raise RuntimeError("Final v1 already exists; refuse overwrite")
 if not all(f.is_file() for f in SOURCES):
  raise RuntimeError("Expected previous graded, original and island worlds missing")
 checks={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}
 plan=json.loads(PLAN.read_text(encoding="utf-8"))
 if len(plan["sites"])!=125 or len({x["id"] for x in plan["sites"]})!=125 or (
  sum(bool(s["relocated"]) for s in plan["sites"])!=67):
  raise RuntimeError("Untrusted final 125-site coastal relocation manifest")
 lib=unreal.AnomaliaZPrigimaliaWorldImportLibrary
 if not hasattr(lib,"create_skarvik_final_coastal_landscape") or not hasattr(lib,"skarvik_final_coastal_height"):
  raise RuntimeError("Native final coastal importer not compiled")
 h=lib.skarvik_final_coastal_height
 bad=[]
 for site in plan["sites"]:
  east,north=[float(a)*1000 for a in site["targetKm"]]
  center=float(h(east,north))
  if not math.isfinite(center) or center<5.0 or center>1850:
   bad.append([site["id"],"submerged-or-invalid-center",center]);continue
  pad=min(65.,float(site["siteTerrainFlatHalfM"])*.65)
  sample=[float(h(east+dx,north+dy)) for dx in (-pad,0,pad) for dy in (-pad,0,pad)]
  if max(sample)-min(sample)>0.25:
   bad.append([site["id"],"insufficient-native-terrace-grade",round(max(sample)-min(sample),3)])
 if bad:
  report["rejectedSourceSiteCount"]=len(bad)
  report["sampleSiteFailures"]=bad[:35]
  raise RuntimeError("Original coast has no safe final terraces for "+str(len(bad))+" sites")
 lv=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not lv.new_level(PKG,is_partitioned_world=True):
  raise RuntimeError("Cannot create new native final World Partition map")
 landscape=lib.create_skarvik_final_coastal_landscape()
 if not landscape:raise RuntimeError("Could not create native original-coast graded Landscape")
 proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 components=sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)
 collision=sum(len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)) for a in proxies)
 if components!=576 or collision!=576:
  raise RuntimeError("Missing 576 landscape + 576 collision components: "+str((components,collision)))
 report["nativeLandscapeAndCollisionCount"]=components
 # Exact original city location, now level center is a 4km dry flat plateau.
 city_e=2000.;city_n=-8000.;z=float(h(city_e,city_n))
 start=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(city_e*100,-city_n*100,(z+1.8)*100))
 if start:start.set_actor_label("SKARVIK_FINAL_BIG_CITY_PLAYER_START")
 if not lv.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
  raise RuntimeError("Native final World Partition landscape not saved")
 if not FILE.exists() or FILE.stat().st_size<1024:
  raise RuntimeError("Final v1 real map file missing")
 for f in SOURCES:
  if hashlib.sha256(f.read_bytes()).hexdigest()!=checks[str(f)]:
   raise RuntimeError("Source original altered during final-world construction")
 report.update(state="SKARVIK_FINAL_48KM_TRUE_SEVEN_ISLAND_COAST_AND_125_DRY_TERRACES_NATIVE_WORLD_SAVED_NOT_MIGRATED",
  levelSaved=True,sideKm=48,sitePadCount=125,provisionalDrySiteRelocations=67,
  finalCitySampleOriginalFootprintKm=[4,4],nativeLandscapeAndCollisionCount=components,
  savedNativeWorldBytes=FILE.stat().st_size,seaWaterGameplayEnabled=False)
 unreal.log("SKARVIK_FINAL_48KM_SOURCE_ISLANDS_AND_125_TERRACES_SAVED=true")
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_FINAL_TERRAIN_NATIVE_FAILURE="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
