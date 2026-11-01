"""Independent real Unreal 5.8 map asset-load smoke for the ONE staged ANOMALIAZ editor.

Do not create, rename, save, cook, load all World Partition cells or delete
anything; check 14 real .umap assets can be resolved and loaded as UWorld.
The 15th F.A.L.C (26.5 km) genuinely has no source .umap/heightmap on PC.
"""
import json
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
OUTPUT=Path(os.environ["ANOMALIAZ_FOURTEEN_UE_WORLD_VERIFY_OUT"])
WORLD_NAMES=[
 "PRIGIMALIA_SKARVIK_FINAL_v1",
 "ANOMALIA_Inhabited_v2",
 "PRIGIMALIA_KARSKOV",
 "PRIGIMALIA_VORGRAD",
 "PRIGIMALIA_NEMORIS",
 "PRIGIMALIA_DRAKHEIM",
 "PRIGIMALIA_SOLYNACALYRA",
 "PRIGIMALIA_NEXAVARKHOS",
 "PRIGIMALIA_CHERNASKALUXRIA",
 "PRIGIMALIA_KOLCHIEM_ORIGINS",
 "PRIGIMALIA_ROSKATVIA_B1",
 "PRIGIMALIA_NOGOKV_51",
 "PRIGIMALIA_PARADISIOMANIA",
 "PRIGIMALIA_DEADROOT"
]
report={
 "state":"FAILED",
 "project":str(ROOT),
 "targetWorldCount":15,
 "actualWorldsToVerify":14,
 "falcOriginalTerrainSourceFound":False,
 "falcNativeWorldCreated":False,
 "allFifteenGenuineReady":False,
 "SM5Rendered":False,
 "allWorldsPlayable":False,
 "networkServerReady":False,
 "originalCAndDMapsModified":False,
 "levelsSavedOrModified":False,
 "worlds":[]
}
try:
 if ROOT.name.lower()!="unreal" or "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper():
  raise RuntimeError("Unexpected UE5 stage")
 marker=ROOT/".skarvik-ci-stage-marker"
 if not marker.is_file() or marker.read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("No original-coast stage marker")
 if len(WORLD_NAMES)!=14 or len(set(WORLD_NAMES))!=14:
  raise RuntimeError("Duplicate or missing real original world packages")
 for name in WORLD_NAMES:
  relative="Maps/"+name+".umap"
  disk=ROOT/"Content"/relative
  package="/Game/Maps/"+name
  item={"name":name,"package":package,"umapFileFound":disk.is_file(),
        "UnrealAssetRegistryFindsWorld":False,"actualUWorldLoaded":False,
        "actualClass":None,"worldPartitionActorsStreamed":False}
  report["worlds"].append(item)
  if not disk.is_file():
   raise RuntimeError("Missing independent native world: "+package)
  present=bool(unreal.EditorAssetLibrary.does_asset_exist(package))
  item["UnrealAssetRegistryFindsWorld"]=present
  if not present:raise RuntimeError("UE5 AssetRegistry cannot find existing .umap: "+package)
  world=unreal.load_asset(package)
  item["actualUWorldLoaded"]=bool(world)
  if not world:raise RuntimeError("Native UWorld asset failed to load: "+package)
  item["actualClass"]=world.get_class().get_name()
  if item["actualClass"]!="World":
   raise RuntimeError("This isn't a real native UWorld: "+package+" -> "+str(item["actualClass"]))
  unreal.log("ANOMALIAZ_REAL_NATIVE_WORLD_LOADED="+package)
 # F.A.L.C is not falsely represented by another landscape.
 missing=ROOT/"Content/Maps/PRIGIMALIA_FALC.umap"
 if missing.is_file():
  # Another agent may have created FALC while this read-only test was running:
  # stop rather than claim that it is absent without a fresh terrain audit.
  raise RuntimeError("FALC .umap appeared during audit; verify original topo before claiming 15th world")
 report["state"]="FOURTEEN_REAL_UE5_WORLD_ASSETS_LOADED_FALC_SOURCE_MISSING"
except Exception as exc:
 report["error"]=str(exc)
 report["traceback"]=traceback.format_exc(limit=9)
 unreal.log_error("ANOMALIAZ_REAL_MAP_LOAD_AUDIT_FAILED="+str(exc))
finally:
 OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 unreal.log("ANOMALIAZ_FOURTEEN_UE5_MAP_LOAD_STATUS="+report["state"])
