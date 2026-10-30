"""Import the user-approved startup poster as a boot-only Unreal UI texture.

This intentionally never touches T_MenuBackdrop, WorkForge backgrounds, or the
original D:\\ANOMALIA project. Run inside UnrealEditor-Cmd on the verified clone.
"""
import hashlib
from pathlib import Path

import unreal

root = Path(unreal.Paths.project_dir()).resolve()
stage = Path(r"D:\ANOMALIAZ-PRIGIMALIA\unreal")
source = root / "SourceAssets" / "Branding" / "prigimalia-startup-poster.jpg"
marker = root / "Saved" / "BrandMigration" / "verified-source-backup.marker"
destination = "/Game/AnomaliaZPrigimalia/Branding/T_StartupPoster"
metadata_key = "PrigimaliaApprovedStartupPosterSHA256"

if str(root).rstrip("\\/").lower() != str(stage).rstrip("\\/").lower():
    raise RuntimeError("Refusing to import startup artwork outside staged PRIGIMALIA clone")
if not marker.is_file():
    raise RuntimeError("Independent clone has not been verified")
if not source.is_file() or source.stat().st_size < 100_000:
    raise RuntimeError("The approved full-resolution startup poster JPG is missing")

checksum = hashlib.sha256(source.read_bytes()).hexdigest()
texture = unreal.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else None
if texture is not None:
    existing_checksum = unreal.EditorAssetLibrary.get_metadata_tag(texture, metadata_key)
    if existing_checksum != checksum:
        raise RuntimeError("Existing startup texture has different artwork: refusing overwrite")
else:
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = "/Game/AnomaliaZPrigimalia/Branding"
    task.destination_name = "T_StartupPoster"
    task.automated = True
    task.save = True
    task.replace_existing = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(destination)

if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("Startup poster was not imported as a Texture2D")

texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property("never_stream", True)
texture.set_editor_property("srgb", True)
unreal.EditorAssetLibrary.set_metadata_tag(texture, metadata_key, checksum)
if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
    raise RuntimeError("Could not save the transient startup texture")
unreal.log("PRIGIMALIA_STARTUP_TEXTURE_IMPORTED=" + checksum)
