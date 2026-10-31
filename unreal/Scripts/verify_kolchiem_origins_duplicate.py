"""Read-only UE5.8 proof that both old DRAZOVIA and KOLCHIEM are separate World assets.

The builder must have produced the independent destination before this script.
This verifies package loading only, not streaming, terrain identity, gameplay,
or a finished level. No asset is saved, renamed, deleted or modified.
"""
import json
import os
from pathlib import Path
from datetime import datetime,timezone
import unreal

SOURCE="/Game/Maps/PRIGIMALIA_Inhabited_v2"
LEGACY_ALIAS="/Game/Maps/ANOMALIA_Inhabited_v2"
TARGET="/Game/Maps/PRIGIMALIA_KOLCHIEM_ORIGINS"
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUTPUT=Path(os.environ["ANOMALIA_KOLCHIEM_RELOAD_REPORT"])
if str(ROOT).replace("/","\\").rstrip("\\").lower()!=r"d:\anomaliaz-prigimalia\unreal":
    raise RuntimeError("Refusing native validation in original or unexpected project: "+str(ROOT))
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
api=unreal.EditorAssetLibrary
state={"sourcePackage":SOURCE,"targetPackage":TARGET,"nativeWorldReloaded":False,
       "separateWorldPackages":False,"streamingVerified":False,
       "gameplayTested":False,"generatedUtc":datetime.now(timezone.utc).isoformat()}
try:
    if SOURCE==TARGET:
        raise RuntimeError("Source and destination unexpectedly identical")
    for package in (SOURCE,TARGET):
        if not api.does_asset_exist(package):
            raise RuntimeError("Expected native World is not registered: "+package)
        obj=unreal.load_asset(package)
        if not obj or not isinstance(obj,unreal.World):
            raise RuntimeError("Expected package does not load as an Unreal World: "+package)
        if str(obj.get_outermost().get_name())!=package:
            raise RuntimeError("World loaded with unexpected package identity: "+package)
        state[("source" if package==SOURCE else "target")+"Class"]=str(obj.get_class().get_name())
    legacy=unreal.load_asset(LEGACY_ALIAS)
    if not legacy or legacy.get_outermost().get_name()!=SOURCE:
        raise RuntimeError("Legacy DRAZOVIA alias no longer resolves to protected original")
    state["legacyAliasResolvesTo"]=legacy.get_outermost().get_name()
    state["nativeWorldReloaded"]=True
    state["separateWorldPackages"]=True
    state["status"]="BOTH_DISTINCT_WORLD_PACKAGES_NATIVE_RELOADED_NOT_PLAYTESTED"
    unreal.log("KOLCHIEM_ORIGINS_DISTINCT_NATIVE_WORLDS_RELOADED=true")
finally:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    if OUTPUT.exists():
        raise RuntimeError("Refusing to replace earlier KOLCHIEM native verification")
    OUTPUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
