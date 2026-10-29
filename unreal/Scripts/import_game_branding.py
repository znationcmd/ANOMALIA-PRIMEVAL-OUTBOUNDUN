"""Import the user's unchanged menu artwork as a cooked UI texture."""
import hashlib,json,os
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
source=root/'SourceAssets/Branding/menu-backdrop.jpg'
destination='/Game/Anomalia/Branding/T_MenuBackdrop'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
texture=unreal.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else None
if texture and unreal.EditorAssetLibrary.get_metadata_tag(texture,'AnomaliaZPrigimaliaBrandingSourceSha256')!=sha:
    raise RuntimeError('Existing artist branding preserved; use a new namespace')
if not texture:
    task=unreal.AssetImportTask();task.filename=str(source);task.destination_path='/Game/Anomalia/Branding';task.destination_name='T_MenuBackdrop';task.automated=True;task.save=True;task.replace_existing=False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);task.get_objects()
    texture=unreal.load_asset(destination)
if not isinstance(texture,unreal.Texture2D):raise RuntimeError('Menu artwork texture import failed')
texture.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property('never_stream',True)
texture.set_editor_property('srgb',True)
unreal.EditorAssetLibrary.set_metadata_tag(texture,'AnomaliaZPrigimaliaBrandingSourceSha256',sha)
if not unreal.EditorAssetLibrary.save_loaded_asset(texture,only_if_is_dirty=False):raise RuntimeError('Menu artwork did not save')
unreal.log('ANOMALIA user menu artwork imported: '+sha)
