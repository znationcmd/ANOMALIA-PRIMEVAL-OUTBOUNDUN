"""Import the user-selected ANOMALIA Workshop crest, isolated from the main-menu artwork."""
import hashlib
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
source = root / "SourceAssets/Branding/prigimalia-workshop-logo.jpg"
destination = "/Game/AnomaliaZPrigimalia/Branding/T_WorkshopLogo"
if not source.is_file():
    raise RuntimeError("Workshop logo is missing: " + str(source))
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
texture = unreal.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else None
if texture and unreal.EditorAssetLibrary.get_metadata_tag(texture, "AnomaliaZPrigimaliaWorkshopLogoSha256") != source_sha:
    raise RuntimeError("Existing workshop artwork differs: preserving current file")
if not texture:
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = "/Game/AnomaliaZPrigimalia/Branding"
    task.destination_name = "T_WorkshopLogo"
    task.automated = True
    task.save = True
    task.replace_existing = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(destination)
if not isinstance(texture, unreal.Texture2D):
    raise RuntimeError("Could not import the selected ANOMALIA Workshop logo")
texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property("never_stream", True)
texture.set_editor_property("srgb", True)
unreal.EditorAssetLibrary.set_metadata_tag(texture, "AnomaliaZPrigimaliaWorkshopLogoSha256", source_sha)
if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
    raise RuntimeError("Could not save native Workshop UTexture2D")
unreal.log("ANOMALIA Workshop logo imported: " + source_sha)
