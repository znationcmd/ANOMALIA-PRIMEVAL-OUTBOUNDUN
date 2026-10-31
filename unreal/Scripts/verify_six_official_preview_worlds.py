"""Read-only verify the six stable official packages are actual distinct Unreal Worlds.

The six worlds still use procedural TerrainPreview relief, NOT the final
user-approved source topographies. No gameplay, World Partition streaming,
landscape material, or assets are certified by this check.
"""
import json, os
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
if str(root).replace("/","\\").rstrip("\\").lower()!=r"d:\anomaliaz-prigimalia\unreal":
    raise RuntimeError("Refusing to audit original or unexpected Unreal project")
out=Path(os.environ["ANOMALIA_SIX_MAP_RELOAD_RECEIPT"])
ids=("KARSKOV","VORGRAD","NEMORIS","DRAKHEIM","SOLYNACALYRA","NEXAVARKHOS")
data={"status":"FAILED_OR_PARTIAL","worlds":[],"gameplayTested":False,
      "finalPhotoTerrainImported":False,"streamingVerified":False}
for name in ids:
    row={"id":name}
    target="/Game/Maps/PRIGIMALIA_"+name
    source=target+"_TerrainPreview"
    for label,path in (("originalPreview",source),("officialWorld",target)):
        asset=unreal.load_asset(path)
        row[label+"Loaded"]=(bool(asset) and isinstance(asset,unreal.World) and
                            asset.get_outermost().get_name()==path)
        if asset:
            row[label+"Package"]=asset.get_outermost().get_name()
    srcActors=root/"Content/__ExternalActors__/Maps"/("PRIGIMALIA_"+name+"_TerrainPreview")
    dstActors=root/"Content/__ExternalActors__/Maps"/("PRIGIMALIA_"+name)
    row["sourceActorFiles"]=sum(1 for _ in srcActors.rglob("*.uasset")) if srcActors.is_dir() else 0
    row["newActorFiles"]=sum(1 for _ in dstActors.rglob("*.uasset")) if dstActors.is_dir() else 0
    row["separatePackageIdentity"]=target!=source
    row["status"]="NATIVE_DUPLICATE_LOADS_NOT_FINAL_TERRAIN" if all((
        row["originalPreviewLoaded"],row["officialWorldLoaded"],
        row["newActorFiles"]>=row["sourceActorFiles"])) else "FAIL"
    data["worlds"].append(row)
    unreal.log("ANOMALIA_OFFICIAL_PROVISIONAL_WORLD "+name+" "+row["status"])
data["verifiedCount"]=sum(row["status"].startswith("NATIVE_DUPLICATE") for row in data["worlds"])
if data["verifiedCount"]==len(ids):
    data["status"]="SIX_DISTINCT_OFFICIAL_PROVISIONAL_WORLDS_NATIVE_LOADED"
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():
    raise RuntimeError("Refusing to overwrite a previous map validation receipt")
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if data["verifiedCount"]!=len(ids):
    raise RuntimeError("Some official provisional worlds could not be native loaded")
unreal.log("SIX_OFFICIAL_PROVISIONAL_WORLDS_NATIVE_LOADED=true")
