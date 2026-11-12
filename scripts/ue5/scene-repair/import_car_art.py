"""Import corrected, source-verified E39 parts; no map changes in this step."""
import unreal,json,os,traceback,hashlib
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();out=Path(os.environ['SCENE_REPAIR_OUT']);r={'state':'FAILED','parts':[]}
try:
 reg=unreal.AssetRegistryHelpers.get_asset_registry();reg.wait_for_completion();ed=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
 manifest=json.loads((root/'SourceAssets/BMWE39RoadPresentation_v8/manifest.json').read_text())
 models=[(root/'SourceAssets/BMWE39RoadPresentation_v8'/p['file'],p['objectPath'],p['sha256'],p['id'] in {x['id'] for x in manifest['panels']}) for p in manifest['models']]
 engine=json.loads((root/'SourceAssets/E39EngineBay_v1/manifest.json').read_text());models.append((root/'SourceAssets/E39EngineBay_v1/engine_bay.glb','/Game/Anomalia/E39EngineBay_v1/SM_engine_bay',engine['sha256'],False))
 for source,destination,sha,panel in models:
  if hashlib.sha256(source.read_bytes()).hexdigest()!=sha:raise RuntimeError('Art integrity mismatch '+str(source))
  if unreal.EditorAssetLibrary.does_asset_exist(destination):
   mesh=unreal.load_asset(destination)
   if unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaSceneRepairSourceSha')!=sha:raise RuntimeError('Existing artist asset preserved '+destination)
  else:
   task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=destination.rsplit('/',1)[0]+'/Imports';task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
   unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);candidates=[a for a in task.get_objects() if isinstance(a,unreal.StaticMesh)]
   if len(candidates)!=1:raise RuntimeError('Expected one imported mesh '+str(source))
   mesh=unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(),destination)
   if not mesh:raise RuntimeError('Canonical mesh copy failed')
   unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaSceneRepairSourceSha',sha)
  ns=ed.get_nanite_settings(mesh);ns.enabled=False;ed.set_nanite_settings(mesh,ns,apply_changes=True)
  bs=ed.get_lod_build_settings(mesh,0);bs.recompute_normals=False;bs.recompute_tangents=True;bs.use_high_precision_tangent_basis=True;ed.set_lod_build_settings(mesh,0,bs)
  if panel and ed.get_simple_collision_count(mesh)==0:
   if ed.add_simple_collisions(mesh,unreal.ScriptCollisionShapeType.NDOP26)<0:raise RuntimeError('Panel collision missing')
  if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False):raise RuntimeError('Imported mesh did not save')
  b=mesh.get_bounds();r['parts'].append({'path':destination,'triangles':mesh.get_num_triangles(0),'min':[getattr(b.origin,a)-getattr(b.box_extent,a) for a in ['x','y','z']],'max':[getattr(b.origin,a)+getattr(b.box_extent,a) for a in ['x','y','z']]})
 r['state']='CORRECTED_E39_AND_ENGINE_IMPORTED_NOT_YET_INSTALLED'
except Exception:r['error']=traceback.format_exc()
finally:(out/'car-art-import.json').write_text(json.dumps(r,indent=2));unreal.SystemLibrary.quit_editor()
