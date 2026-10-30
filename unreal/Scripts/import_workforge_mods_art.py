"""Import existing repository-owned scenery/branding into the actual UE5 Mods UI.

These are real images, not flattened interface screenshots. All clickable
elements remain independent UMG widgets. Imports use unique /WorkForge/Artwork
names and NEVER replace an existing artwork asset or modify other maps.
"""
import hashlib
import json
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir()).resolve()
allowed = Path(r"D:\ANOMALIAZ-PRIGIMALIA\unreal")
if str(project).lower().replace("/", "\\") != str(allowed).lower():
    raise RuntimeError("WorkForge visual import is isolated to the staged D project")

source_dir = project / "SourceAssets" / "WorkForge" / "ReferenceArtwork"
destination = "/Game/AnomaliaZPrigimalia/WorkForge/Artwork"
manifest_path = project / "Saved" / "BrandMigration" / "workforge-mods-visual-art-report.json"
assets = {
    "T_WFHero": "hero-archipelago.jpg",
    "T_WFCategory0": "category-all.jpg",
    "T_WFCategory1": "category-vehicles.jpg",
    "T_WFCategory2": "category-creatures.jpg",
    "T_WFCategory3": "category-buildings.jpg",
    "T_WFCategory4": "category-maps.jpg",
    "T_WFCategory5": "category-weapons.jpg",
    "T_WFCategory6": "category-survival.jpg",
    "T_WFCategory7": "category-gameplay.jpg",
    "T_WFCategory8": "category-tools.jpg",
    "T_WFModCardFallback": "card-fallback.jpg",
}
report = {"destination": destination, "created": [], "alreadyIdentical": [], "errors": []}
tag = "AnomaliaZPrigimaliaWorkForgeVisualSourceSHA256"
for name, filename in assets.items():
    source = source_dir / filename
    if not source.is_file():
        report["errors"].append("Missing approved repository artwork: " + filename)
        continue
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    package = destination + "/" + name
    texture = unreal.load_asset(package) if unreal.EditorAssetLibrary.does_asset_exist(package) else None
    if texture:
        if not isinstance(texture, unreal.Texture2D):
            report["errors"].append("Target is not a Texture2D: " + package)
            continue
        existing = unreal.EditorAssetLibrary.get_metadata_tag(texture, tag)
        if existing != sha:
            report["errors"].append("Existing art differs; preserved: " + package)
            continue
        report["alreadyIdentical"].append(name)
        continue
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(package)
    if not isinstance(texture, unreal.Texture2D):
        report["errors"].append("Unreal could not import " + name)
        continue
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("never_stream", True)
    texture.set_editor_property("srgb", True)
    unreal.EditorAssetLibrary.set_metadata_tag(texture, tag, sha)
    if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
        report["errors"].append("Failed to save " + name)
    else:
        report["created"].append(name)

manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
unreal.log("PRIGIMALIA_WORKFORGE_VISUAL_ASSETS=" + str(len(report["created"]) + len(report["alreadyIdentical"])))
if report["errors"]:
    raise RuntimeError("WorkForge artwork verification failed: " + "; ".join(report["errors"]))
