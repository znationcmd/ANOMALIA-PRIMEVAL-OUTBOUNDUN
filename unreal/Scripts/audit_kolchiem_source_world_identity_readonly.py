"""Diagnose whether legacy ANOMALIA_Inhabited_v2 is a redirect, actual UWorld,
or an unsuitable package for the native WorldPartition rename/duplicate builder.
Outputs only a JSON receipt to RUNNER_TEMP. No level save/mutation.
"""
import os, json
from pathlib import Path
import traceback
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
expected=r"d:\anomaliaz-prigimalia\unreal"
if str(root).replace("/","\\").rstrip("\\").lower()!=expected:
    raise RuntimeError("wrong UE project; refuse identity audit")
out=Path(os.environ["ANOMALIA_KOLCHIEM_SOURCE_INSPECTION"])
packages=[
 "/Game/Maps/ANOMALIA_Inhabited_v2",
 "/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate",
 "/Game/Maps/ANOMALIA_Archipelago_v2",
 "/Game/Maps/ANOMALIA_Playable_v1",
]
r={"mode":"readonly-world-package-identity","data":[]}
for package in packages:
    row={"requested":package}
    try:
        row["doesAssetExist"]=unreal.EditorAssetLibrary.does_asset_exist(package)
        asset=unreal.EditorAssetLibrary.find_asset_data(package)
        row["registryValid"]=bool(asset and asset.is_valid())
        if row["registryValid"]:
            row["assetDataPackage"]=str(asset.package_name)
            row["assetDataName"]=str(asset.asset_name)
            row["assetDataObjectPath"]=str(asset.get_full_name())
        world=unreal.load_asset(package)
        row["assetLoaded"]=bool(world)
        if world:
            row["class"]=world.get_class().get_name()
            row["objectName"]=world.get_name()
            row["objectPath"]=world.get_path_name()
            row["outermostPackage"]=world.get_outermost().get_name()
            row["isWorld"]=isinstance(world,unreal.World)
            try:
                wp=world.get_editor_property("world_partition")
                row["hasWorldPartitionProperty"]=bool(wp)
            except Exception as exc:
                row["worldPartitionPropertyError"]=str(exc)
    except Exception as exc:
        row["error"]=repr(exc)
        row["traceback"]=traceback.format_exc()
    r["data"].append(row)
    unreal.log("KOLCHIEM_SOURCE_IDENTITY="+json.dumps(row,ensure_ascii=False))
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
unreal.log("KOLCHIEM_SOURCE_READONLY_INSPECTION_COMPLETED=true")
