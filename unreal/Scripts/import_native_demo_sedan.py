"""Import the pinned original CC0 sedan parts; do not alter a map or installation."""
import hashlib
import json
import os
import traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
BASE=ROOT/'SourceAssets/NativeDemoSedan_v3'
OUT=Path(os.environ['ANOMALIA_SEDAN_OUTPUT'])
OUT.mkdir(parents=True,exist_ok=True)
TAG='AnomaliaNativeSedanSha256'
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),models=[],
    mapModified=False,installed=False,rigged=False,interactiveDoors=False,gameplayTested=False)
try:
    manifest=json.loads((BASE/'manifest.json').read_text())
    source=manifest['source']
    if source['license']!='CC0-1.0' or source['sha256']!='feb0be31d153ddb42dc15ae52a651e214e85ab67e31bec4282b00f9d47c9b597':
        raise RuntimeError('Reviewed original CC0 source identity required')
    models=manifest['models']
    expected={'body','door_driver','wheel_fl','wheel_fr','wheel_rl','wheel_rr'}
    coverage=manifest['sourceCoverage'];partition=coverage['partition']
    if (manifest['schemaVersion']!=3 or len(models)!=6 or {m['id'] for m in models}!=expected or
        coverage['nodes']!=304 or partition['doorSurfaceArea']<.5 or
        abs(partition['originalSurfaceArea']-partition['doorSurfaceArea']-partition['remainingSurfaceArea'])>1e-6):
        raise RuntimeError('Original surface partition and separate driver door required')
    editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for model in models:
        name=model['id'];path=BASE/(name+'.glb')
        if model['file']!=name+'.glb' or path.stat().st_size!=model['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=model['sha256']:
            raise RuntimeError('Prepared part integrity mismatch: '+name)
        destination='/Game/Anomalia/NativeDemoSedan_v3/'+name+'/SM_'+name
        if model['objectPath']!=destination:raise RuntimeError('Unexpected canonical sedan namespace')
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            mesh=unreal.load_asset(destination)
            if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,TAG)!=model['sha256']:
                raise RuntimeError('Existing artist asset preserved: '+destination)
        else:
            # The import namespace is separate from the canonical assets. Never
            # replace an asset, including leftovers from an interrupted import.
            task=unreal.AssetImportTask();task.filename=str(path)
            task.destination_path='/Game/Anomalia/NativeDemoSedan_v3/Imports/'+name
            task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            objects=task.get_objects()
            candidates=[m for m in objects if isinstance(m,unreal.StaticMesh)]
            if len(candidates)!=1:raise RuntimeError('Expected one imported static part: '+name)
            mesh=unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(),destination)
            if not mesh:raise RuntimeError('Canonical part creation failed: '+name)
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,TAG,model['sha256'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaSourceLicense','CC0-1.0')
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
        if name=='door_driver' and editor.get_simple_collision_count(mesh)==0:
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
    report.update(state='CC0_SEDAN_STATIC_PARTS_IMPORTED_NOT_DRIVEN',source=source,
        wheelHubsCm=manifest['wheelHubsCm'],panels=manifest['panels'],surfacePartition=partition)
except Exception as error:
    report['error']=str(error);unreal.log_error(traceback.format_exc())
finally:
    (OUT/'sedan-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
