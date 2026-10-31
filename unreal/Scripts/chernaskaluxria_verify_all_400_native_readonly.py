"""Check the CHERNASKALUXRIA 100km 400-tile persistent UE5 level after import.

This validates saved native package registration, 400 checksum-matched individual
tile receipts and 400+ real external actor packages. It is NOT a render,
World Partition streaming load, gameplay or server validation.
"""
import hashlib,json,os
from pathlib import Path
import unreal

root=Path(unreal.Paths.project_dir()).resolve()
if str(root).replace("/","\\").rstrip("\\").lower()!=r"d:\anomaliaz-prigimalia\unreal":
    raise RuntimeError("Refuse verification outside installed isolated stage")
pkg="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
receipt=Path(os.environ["CH_ALL_TILES_FINAL_REPORT"])
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
asset=unreal.load_asset(pkg)
if not asset or not isinstance(asset,unreal.World) or asset.get_outermost().get_name()!=pkg:
    raise RuntimeError("Full-grid CHERNASKALUXRIA world is not a valid UWorld package")
rootSrc=root/"TerrainSource/CHERNASKALUXRIA"
rootProof=root/"Saved/CHERNASKALUXRIA"
paths=[]
for y in range(20):
    for x in range(20):
        name=f"CHERNASKALUXRIA_x{x:02}_y{y:02}"
        inp=rootSrc/(name+".r16")
        proof=rootProof/(name+".json")
        if not inp.is_file() or inp.stat().st_size!=253*253*2 or not proof.is_file():
            raise RuntimeError("Unrepresented CHERNASKALUXRIA tile in full native World: "+name)
        p=json.loads(proof.read_text(encoding="utf-8-sig"))
        if (p.get("mapPackage")!=pkg or p.get("tile")!=name or
            p.get("state")!="NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED" or
            p.get("sourceSha256")!=hashlib.sha256(inp.read_bytes()).hexdigest()):
            raise RuntimeError("Incorrect native Landscape proof or source: "+name)
        paths.append(name)
actors=root/"Content/__ExternalActors__/Maps/PRIGIMALIA_CHERNASKALUXRIA"
packages=list(actors.rglob("*.uasset")) if actors.is_dir() else []
if len(packages)<400:
    raise RuntimeError("Missing World Partition external actor files: "+str(len(packages)))
status={"status":"400_NATIVE_TILES_SAVED_DISTINCT_WORLD_RELOADED_NOT_GAMEPLAY_TESTED",
        "package":pkg,"tileCount":len(paths),"externalActorPackages":len(packages),
        "seamVerifiedInSourcePreflight":True,
        "fullTopographicUserPhotoImported":False,"gameplayTested":False,
        "streamingTested":False,"allLandscapeActorsRendered":False}
receipt.parent.mkdir(parents=True,exist_ok=True)
if receipt.exists():
    raise RuntimeError("Refuse to replace previous full-grid inspection receipt")
receipt.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
unreal.log("CHERNASKALUXRIA_FULL_400_RELOADED_AND_SOURCE_RECEIPTS_CHECKED=true")
