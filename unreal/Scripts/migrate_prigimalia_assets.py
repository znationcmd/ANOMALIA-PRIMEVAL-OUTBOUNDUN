"""Safe asset + map rename for ANOMALIA’Z PRIGIMALIA, exclusively inside Unreal Editor 5.8.

Dry-run by default. APPLY is deliberately impossible on the original D:\\ANOMALIA
project: use an independent, fully backed up project copy. The script never
moves or edits a .uasset or .umap file using ordinary filesystem operations.
Run UnrealEditor-Cmd.exe -ExecutePythonScript=... on the staged copy.
"""
import json
import os
from pathlib import Path
import unreal

OLD_DIR = "/Game/Anomalia"
NEW_DIR = "/Game/AnomaliaZPrigimalia"
APPLY = os.environ.get("PRIGIMALIA_APPLY_RENAME") == "YES"
STAGED = os.environ.get("PRIGIMALIA_STAGED_COPY") == "YES"
project_root = Path(unreal.Paths.project_dir()).resolve()
project_file = Path(unreal.Paths.get_project_file_path()).resolve()
content_dir = project_root / "Content"
report_file = project_root / "Saved" / "BrandMigration" / "asset-rename-report.json"
report_file.parent.mkdir(parents=True, exist_ok=True)
api = unreal.EditorAssetLibrary

# Source and target paths are object/package paths, not filenames. AssetTools
# handles loaded references, redirectors and serialized package identifiers.
def old_asset_inventory():
    if not api.does_directory_exist(OLD_DIR):
        return []
    return sorted(set(api.list_assets(OLD_DIR, recursive=True, include_folder=False)))

def eligible_maps():
    """Discover actual .umap packages, including maps outside /Game/Maps."""
    if not content_dir.is_dir():
        return []
    items = []
    for filepath in content_dir.rglob("*.umap"):
        rel = filepath.relative_to(content_dir).with_suffix("")
        path = "/Game/" + rel.as_posix()
        name = rel.name
        if path.startswith(OLD_DIR + "/"):
            continue  # renamed with the directory and its external packages
        if name.startswith("ANOMALIA_"):
            target_name = "PRIGIMALIA_" + name[len("ANOMALIA_"):]
        elif name == "AnomaliaWorld":
            target_name = "PrigimaliaWorld"
        else:
            continue
        target = path.rsplit("/", 1)[0] + "/" + target_name
        items.append((path, target))
    return sorted(items)

def report_on_disk(report):
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("PRIGIMALIA_MIGRATION_REPORT=" + str(report_file))
    return report

def migrate():
    checkpoint = {}
    if report_file.exists():
        checkpoint = json.loads(report_file.read_text(encoding="utf-8"))
    previous = old_asset_inventory()
    resumed = bool(checkpoint.get("directoryRenamed"))
    if resumed:
        migrated = api.list_assets(NEW_DIR, recursive=True, include_folder=False)
        if len(migrated) < checkpoint.get("legacyAssetsFound", 0):
            raise RuntimeError("Previously migrated folder is incomplete; refusing resume")
        previous = []
    maps = eligible_maps()
    report = {
        "title": "ANOMALIA’Z PRIGIMALIA",
        "project": project_file.name,
        "applyRequested": APPLY,
        "stagedCopyConfirmed": STAGED,
        "legacyFolder": OLD_DIR,
        "newFolder": NEW_DIR,
        "legacyAssetsFound": checkpoint.get("legacyAssetsFound", 0) if resumed else len(previous),
        "legacyMapsFound": len(maps),
        "mapRenamePlan": [{"old": a, "new": b} for a, b in maps],
        "directoryRenamed": resumed,
        "mapsRenamed": checkpoint.get("mapsRenamed", []) if resumed else [],
        "verified": False,
        "errors": [],
        "originalProjectPreserved": True,
    }
    if not APPLY:
        unreal.log_warning("DRY RUN ONLY: no assets or map packages will be modified.")
        dry_report = report_file.with_name("asset-rename-dry-run-report.json")
        dry_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        unreal.log("PRIGIMALIA_DRY_RUN_REPORT=" + str(dry_report))
        return report

    # There is no safe way to resolve binary reference dependencies via git mv.
    # The original local project remains intact. Only a staged project copy
    # with a renamed .uproject may be modified by this migration.
    if not STAGED or project_file.stem != "AnomaliaZPrigimalia":
        raise RuntimeError("Refusing apply: must be an independently staged renamed project")
    if str(project_root).lower().startswith("d:\\anomalia\\"):
        raise RuntimeError("Refusing apply inside original D:\\ANOMALIA project")
    if not (project_root / "Saved" / "BrandMigration" / "verified-source-backup.marker").is_file():
        raise RuntimeError("Refusing apply without verified backup marker on staged project")
    if previous and api.does_directory_exist(NEW_DIR):
        existing = api.list_assets(NEW_DIR, recursive=True, include_folder=False)
        if existing:
            raise RuntimeError("Destination contains assets; refusing overwrite")
    for old, new in maps:
        if api.does_asset_exist(new):
            raise RuntimeError("Map destination collision: " + new)

    try:
        unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()
        if previous:
            if not api.rename_directory(OLD_DIR, NEW_DIR):
                raise RuntimeError("Unreal could not rename the legacy asset directory")
            report["directoryRenamed"] = True
            report_on_disk(report)
            updated = [name.replace(OLD_DIR + "/", NEW_DIR + "/", 1) for name in previous]
            if not all(api.does_asset_exist(name) for name in updated):
                raise RuntimeError("Missing target assets after folder rename")
            if not api.save_directory(NEW_DIR, only_if_is_dirty=False, recursive=True):
                raise RuntimeError("Failed to save one or more migrated assets")
        # A World Partition map rename can be rejected by Unreal while the
        # world is loaded. This is a hard failure, never a filesystem fallback.
        for old, new in maps:
            world = unreal.load_asset(old)
            if not isinstance(world, unreal.World):
                raise RuntimeError("Map could not be loaded as a World: " + old)
            folder, name = new.rsplit("/", 1)
            rename = unreal.AssetRenameData(asset=world, new_package_path=folder, new_name=name)
            if not unreal.AssetToolsHelpers.get_asset_tools().rename_assets([rename]):
                raise RuntimeError("AssetTools refused map rename; World Partition builder may be required: " + old)
            if not api.does_asset_exist(new):
                raise RuntimeError("Renamed map could not be resolved: " + new)
            if not unreal.EditorLoadingAndSavingUtils.save_map(world, new):
                raise RuntimeError("Could not save renamed map: " + new)
            report["mapsRenamed"].append({"old": old, "new": new})
            report_on_disk(report)
        # Unreal may intentionally leave redirector assets under the old path.
        # They preserve legacy Blueprint references and are NOT lost source assets.
        # Verify every new target instead of incorrectly rejecting redirectors.
        expected_new = [name.replace(OLD_DIR + "/", NEW_DIR + "/", 1) for name in previous]
        report["remainingLegacyPathsIncludingRedirectors"] = len(old_asset_inventory())
        report["verified"] = (
            all(api.does_asset_exist(name) for name in expected_new)
            and all(api.does_asset_exist(m["new"]) for m in report["mapsRenamed"])
        )
        if not report["verified"]:
            raise RuntimeError("Final asset and map validation failed")
        unreal.log("PRIGIMALIA_MIGRATION_STAGED_ASSETS_VERIFIED=true")
    except Exception as exc:
        report["errors"].append(str(exc))
        report_on_disk(report)
        raise
    return report_on_disk(report)

migrate()
