"""Import authored V8 and genuine, attributed M5 recording excerpts; preserve existing assets."""
import unreal,os,json,hashlib,traceback
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();out=Path(os.environ['SCENE_REPAIR_OUT']);report={'state':'FAILED','assets':[]}
try:
 if root!=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal').resolve():raise RuntimeError('Unexpected project')
 unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()
 tools=unreal.AssetToolsHelpers.get_asset_tools()
except Exception:
 report['error']=traceback.format_exc()
 (out/'m5-import.json').write_text(json.dumps(report,indent=2));unreal.SystemLibrary.quit_editor();raise
try:
 records=[]
 engine=json.loads((root/'SourceAssets/E39M5S62_v1/manifest.json').read_text())
 records.append((root/'SourceAssets/E39M5S62_v1/engine_bay.glb','/Game/Anomalia/E39M5S62_v1/SM_engine_bay',engine['sha256'],'mesh'))
 audio=json.loads((root/'SourceAssets/E39M5S62Audio_v1/manifest.json').read_text())
 for p in audio['sounds']:records.append((root/'SourceAssets/E39M5S62Audio_v1'/p['file'],'/Game/Anomalia/E39M5S62Audio_v1/S_m5_'+p['id'],p['sha256'],'sound'))
 for source,destination,expected,kind in records:
  if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise RuntimeError('Source integrity mismatch')
  if unreal.EditorAssetLibrary.does_asset_exist(destination):
   asset=unreal.load_asset(destination)
   if unreal.EditorAssetLibrary.get_metadata_tag(asset,'AnomaliaM5SourceSha')!=expected:raise RuntimeError('Existing asset preserved: '+destination)
  else:
   task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=destination.rsplit('/',1)[0]+'/Imports';task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
   if kind=='sound':task.factory=unreal.SoundFactory()
   tools.import_asset_tasks([task]);candidates=[a for a in task.get_objects() if isinstance(a,unreal.StaticMesh if kind=='mesh' else unreal.SoundWave)]
   if len(candidates)!=1:raise RuntimeError('Expected one imported '+kind+': '+str(source))
   asset=unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(),destination)
   if not asset:raise RuntimeError('Canonical asset copy failed')
   unreal.EditorAssetLibrary.set_metadata_tag(asset,'AnomaliaM5SourceSha',expected)
  if kind=='mesh':
   editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);settings=editor.get_nanite_settings(asset);settings.enabled=False;editor.set_nanite_settings(asset,settings,apply_changes=True)
   if asset.get_num_triangles(0)<=0:raise RuntimeError('Empty V8 geometry')
   report['assets'].append({'path':destination,'triangles':asset.get_num_triangles(0)})
  else:
   asset.set_editor_property('looping',True);asset.set_editor_property('virtualization_mode',unreal.VirtualizationMode.PLAY_WHEN_SILENT)
   unreal.EditorAssetLibrary.set_metadata_tag(asset,'Attribution','AfricaAuddyTech — CC BY 3.0 — '+audio['originalVideo'])
   if asset.get_editor_property('duration')<.5:raise RuntimeError('Audio duration invalid')
   report['assets'].append({'path':destination,'duration':asset.get_editor_property('duration'),'looping':asset.get_editor_property('looping')})
  if not unreal.EditorAssetLibrary.save_loaded_asset(asset,False):raise RuntimeError('Asset save failed')
 report['state']='M5_V8_AND_RECORDED_AUDIO_IMPORTED_NOT_YET_PACKAGED'
except Exception:report['error']=traceback.format_exc()
finally:
 (out/'m5-import.json').write_text(json.dumps(report,indent=2));unreal.SystemLibrary.quit_editor()
