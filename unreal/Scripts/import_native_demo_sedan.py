"""Import pinned licensed sedan parts; do not alter a map or installation."""
import hashlib
import json
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
E39=os.environ.get("ANOMALIA_SEDAN_USE_E39")=="1"
NAMESPACE="BMWE39Review_v3" if E39 else "NativeDemoSedan_v3"
BASE=ROOT/"SourceAssets"/NAMESPACE
OUT=Path(os.environ['ANOMALIA_SEDAN_OUTPUT'])
OUT.mkdir(parents=True,exist_ok=True)
TAG='AnomaliaNativeSedanSha256'
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),models=[],
    mapModified=False,installed=False,rigged=False,interactiveDoors=False,gameplayTested=False)
try:
    manifest=json.loads((BASE/'manifest.json').read_text())
    source=manifest['source']
    expected_license='CC-BY-4.0' if E39 else 'CC0-1.0'
    expected_hash='984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d' if E39 else 'feb0be31d153ddb42dc15ae52a651e214e85ab67e31bec4282b00f9d47c9b597'
    if source['license']!=expected_license or source['sha256']!=expected_hash:
        raise RuntimeError('Reviewed licensed source identity required')
    models=manifest['models']
    expected={'body','door_driver','wheel_fl','wheel_fr','wheel_rl','wheel_rr'}
    if E39:expected.update({'door_front_right','door_rear_left','door_rear_right','hood','trunk'})
    if len(models)!=len(expected) or {m['id'] for m in models}!=expected:raise RuntimeError('Complete expected part set required')
    partition=None
    if E39:
        partition=manifest['surfacePartition']
        previous=json.loads((ROOT/'SourceAssets/BMWE39Review_v2/manifest.json').read_text())
        if (manifest['schemaVersion']!=3 or abs(partition['sourceArea']-sum(partition['areas'].values()))>1e-6 or
            manifest['parentBodySha256']!=next(m['sha256'] for m in previous['models'] if m['id']=='body') or
            {p['id'] for p in manifest['panels']}!={'door_driver','door_front_right','door_rear_left','door_rear_right','hood','trunk'}):
            raise RuntimeError('Same E39 complete panel partition required')
        for old in previous['models']:
            if old['id']=='door_driver' or old['id'].startswith('wheel_'):
                if next(m['sha256'] for m in models if m['id']==old['id'])!=old['sha256']:
                    raise RuntimeError('Validated E39 driver leaf and wheels must remain unchanged')
    else:
        coverage=manifest['sourceCoverage'];partition=coverage['partition']
        if (manifest['schemaVersion']!=3 or coverage['nodes']!=304 or partition['doorSurfaceArea']<.5 or
            abs(partition['originalSurfaceArea']-partition['doorSurfaceArea']-partition['remainingSurfaceArea'])>1e-6):
            raise RuntimeError('Original surface partition and separate driver door required')
    editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for model in models:
        name=model['id'];path=BASE/(name+'.glb')
        if model['file']!=name+'.glb' or path.stat().st_size!=model['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=model['sha256']:
            raise RuntimeError('Prepared part integrity mismatch: '+name)
        destination='/Game/Anomalia/'+NAMESPACE+'/'+name+'/SM_'+name
        if model['objectPath']!=destination:raise RuntimeError('Unexpected canonical sedan namespace')
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            mesh=unreal.load_asset(destination)
            if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,TAG)!=model['sha256']:
                raise RuntimeError('Existing artist asset preserved: '+destination)
        else:
            # The import namespace is separate from the canonical assets. Never
            # replace an asset, including leftovers from an interrupted import.
            task=unreal.AssetImportTask();task.filename=str(path)
            task.destination_path='/Game/Anomalia/'+NAMESPACE+'/Imports/'+name
            task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            objects=task.get_objects()
            candidates=[m for m in objects if isinstance(m,unreal.StaticMesh)]
            if len(candidates)!=1:raise RuntimeError('Expected one imported static part: '+name)
            mesh=unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(),destination)
            if not mesh:raise RuntimeError('Canonical part creation failed: '+name)
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,TAG,model['sha256'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaSourceLicense',source['license'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaAttribution',source['author']+' / '+source['source']+' / '+source['license'])
        bounds=mesh.get_bounds()
        actual=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]
        # glTF uses metres/Y up; Unreal uses centimetres/Z up.
        dims=model['dimensionsMetresYUp'];expected_cm=[dims[0]*100,dims[2]*100,dims[1]*100]
        if any(abs(a-b)>max(2,b*.025) for a,b in zip(actual,expected_cm)):
            raise RuntimeError('Imported axes or scale are incorrect: '+name+' '+str(actual))
        if 'originMetresYUp' in model:
            origin=model['originMetresYUp'];expected_origin=[origin[0]*100,origin[2]*100,origin[1]*100]
            actual_origin=[bounds.origin.x,bounds.origin.y,bounds.origin.z]
            if any(abs(a-b)>1 for a,b in zip(actual_origin,expected_origin)):
                raise RuntimeError('Imported handedness/pivot differs: '+name+' '+str(actual_origin)+' expected '+str(expected_origin))
        if mesh.get_num_triangles(0)<100 or len(mesh.static_materials)<1:
            raise RuntimeError('Detailed geometry and imported materials required: '+name)
        if name in {p['id'] for p in manifest.get('panels',[{'id':'door_driver'}])} and editor.get_simple_collision_count(mesh)==0:
            if editor.add_simple_collisions(mesh,unreal.ScriptCollisionShapeType.NDOP26)<0:
                raise RuntimeError('Driver door needs moving convex collision')
        # Keep D3D11 compatibility for the current validation host. This does not
        # claim Nanite/Lumen acceptance or final presentation quality.
        settings=editor.get_nanite_settings(mesh)
        if settings.get_editor_property('enabled'):
            settings.set_editor_property('enabled',False);editor.set_nanite_settings(mesh,settings,apply_changes=True)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):
            raise RuntimeError('Part save failed: '+name)
        report['models'].append(dict(id=name,path=mesh.get_path_name(),triangles=mesh.get_num_triangles(0),
            dimensionsCm=actual,originCm=[bounds.origin.x,bounds.origin.y,bounds.origin.z],
            materials=len(mesh.static_materials),sha256=model['sha256']))
    report.update(state='E39_STATIC_PARTS_IMPORTED_NOT_DRIVEN' if E39 else 'CC0_SEDAN_STATIC_PARTS_IMPORTED_NOT_DRIVEN',source=source,
        wheelHubsCm=manifest['wheelHubsCm'],panels=manifest.get('panels',[]),surfacePartition=partition)
except Exception as error:
    report['error']=str(error);unreal.log_error(traceback.format_exc())
finally:
    (OUT/'sedan-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
