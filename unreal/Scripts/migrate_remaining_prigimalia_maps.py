"""Resume only the missing STAGED native map renames in a single UE Editor pass.

Uses AssetTools for ordinary maps; reports still-pending World Partition maps
for the separate builder commandlet. Idempotent: verified targets are skipped.
No filesystem .umap/.uasset renames, no project-root modifications or force.
"""
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
project = Path(unreal.Paths.get_project_file_path()).resolve()
stage = str(root).replace("/", "\\").rstrip("\\").lower()
original = Path(r"D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject")
folder = root / "Saved" / "BrandMigration"
checkpoint_path = folder / "asset-rename-report.json"
output = folder / "remaining-map-migration-status.json"

if (stage != r"d:\anomaliaz-prigimalia\unreal"
        or project.stem != "AnomaliaZPrigimalia"
        or not original.is_file()
        or not (folder / "verified-source-backup.marker").is_file()):
    raise RuntimeError("Refusing staged map migration without isolated verified clone")
if not checkpoint_path.is_file():
    raise RuntimeError("Missing original native migration checkpoint")

proof = json.loads(checkpoint_path.read_text(encoding="utf-8-sig"))
if proof.get("stagedCopyConfirmed") is not True or proof.get("directoryRenamed") is not True:
    raise RuntimeError("Source asset folder was not confirmed migrated")
plan = proof.get("mapRenamePlan") or []
if not plan:
    raise RuntimeError("No original native map migration plan to resume")

api = unreal.EditorAssetLibrary
unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()
assets = unreal.AssetToolsHelpers.get_asset_tools()
result = {
    "stage": str(root), "planned": len(plan),
    "alreadyMigrated": [], "renamedWithAssetTools": [],
    "pendingWorldPartition": [], "errors": [],
    "originalProjectPreserved": original.is_file(),
}
for entry in plan:
    old = entry.get("old", "")
    new = entry.get("new", "")
    if (not old.startswith("/Game/") or not new.startswith("/Game/")
            or old == new or "." in old.rsplit("/", 1)[-1]):
        result["errors"].append("Invalid map mapping: " + repr(entry))
        continue
    if api.does_asset_exist(new):
        world = unreal.load_asset(new)
        if not isinstance(world, unreal.World):
            result["errors"].append("Already renamed target cannot load: " + new)
        else:
            result["alreadyMigrated"].append({"old": old, "new": new})
        continue
    if not api.does_asset_exist(old):
        result["errors"].append("Both map source and destination missing: " + old)
        continue
    world = unreal.load_asset(old)
    if not isinstance(world, unreal.World):
        result["errors"].append("Unreal could not load source World: " + old)
        continue
    target_dir, target_name = new.rsplit("/", 1)
    renamed = False
    try:
        rename = unreal.AssetRenameData(
            asset=world, new_package_path=target_dir, new_name=target_name
        )
        renamed = bool(assets.rename_assets([rename]))
    except Exception as exc:
        unreal.log_warning("Map requires native builder: " + old + " " + str(exc))
    if renamed and api.does_asset_exist(new):
        if not api.save_asset(new, only_if_is_dirty=False):
            result["errors"].append("Could not save renamed map: " + new)
        else:
            result["renamedWithAssetTools"].append({"old": old, "new": new})
    elif api.does_asset_exist(new):
        result["errors"].append(
            "Uncertain partially renamed target; manual review required: " + new
        )
    else:
        result["pendingWorldPartition"].append({"old": old, "new": new})

output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
unreal.log("PRIGIMALIA_MAP_RESUME_REPORT=" + str(output))
unreal.log("PRIGIMALIA_NATIVE_SIMPLE_MAPS_RENAMED=" +
           str(len(result["renamedWithAssetTools"])))
unreal.log("PRIGIMALIA_NATIVE_WORLD_PARTITION_PENDING=" +
           str(len(result["pendingWorldPartition"])))
if result["errors"]:
    raise RuntimeError("Map resume errors (do not package): " + "; ".join(result["errors"]))
