"""Install all 49 pinned CC0 props into an owned Unreal asset namespace."""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
CACHE = ROOT / 'Saved/ItemSourceCache'
OUT = Path(os.environ['ANOMALIA_PROPS_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), models=[], gameplayBound=False, rendered=False)
try:
    manifest = json.loads((CACHE / 'download-receipt.json').read_text())
    if len(manifest['models']) != 49: raise RuntimeError('Complete 49-source receipt required')
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for item in manifest['models']:
        row = dict(id=item['id'], source=item['source'], license=item['license'], state='FAILED')
        try:
            if item['license'] != 'CC0-1.0' or item['status'] != 'DOWNLOADED_DEPENDENCIES_CHECKED':
                raise RuntimeError('Source license and dependency review required')
            for record in item['files']:
                path = (CACHE / 'ANOMALIA_SOURCE_ASSETS' / record['path']).resolve()
                if not path.is_relative_to(CACHE) or path.stat().st_size != record['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                    raise RuntimeError('Source bytes changed')
            identity = hashlib.sha256(json.dumps(item['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            destination = '/Game/Anomalia/VerifiedProps_v1/' + item['modelId']
            exists = unreal.EditorAssetLibrary.does_directory_exist(destination)
            if not exists:
                task = unreal.AssetImportTask()
                task.filename = str(CACHE / 'ANOMALIA_SOURCE_ASSETS' / item['entryPoint'])
                task.destination_path = destination; task.automated=True; task.replace_existing=False; task.save=True
                tools.import_asset_tasks([task]); task.get_objects()
            assets = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(destination,recursive=True,include_folder=False)]
            meshes = [a for a in assets if isinstance(a,unreal.StaticMesh)]
            if not meshes: raise RuntimeError('No native static mesh imported')
            row['meshes'] = []
            for mesh in meshes:
                if exists and unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaPropsSourceSha256') != identity:
                    raise RuntimeError('Existing unverified artist asset preserved')
                materials = mesh.get_editor_property('static_materials')
                if not materials or any(not slot.material_interface or slot.material_interface.get_path_name().startswith('/Engine/EngineMaterials/DefaultMaterial') for slot in materials):
                    raise RuntimeError('Missing native materials')
                if max(mesh.get_num_triangles(0),mesh.get_num_nanite_triangles()) <= 0:
                    raise RuntimeError('Empty native geometry')
                if not exists:
                    unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaPropsSourceSha256',identity)
                    unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaAttribution',item['source']+' / CC0-1.0 / '+item['licenseUrl'])
                    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):
                        raise RuntimeError('Native prop save failed')
                bounds=mesh.get_bounds()
                row['meshes'].append(dict(path=mesh.get_path_name(),materials=len(materials),
                    triangles=mesh.get_num_triangles(0),naniteTriangles=mesh.get_num_nanite_triangles(),
                    dimensionsCm=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]))
            row.update(state='NATIVE_MESHES_AND_MATERIALS_SAVED_NOT_GAMEPLAY_BOUND',sourceIdentity=identity)
        except Exception as error:
            row['error']=str(error)
        report['models'].append(row)
        OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
        unreal.log('ANOMALIA prop '+item['id']+': '+row['state'])
    failed=[m for m in report['models'] if m['state']=='FAILED']
    report.update(importedSources=49-len(failed),meshCount=sum(len(m.get('meshes',[])) for m in report['models']))
    if failed: raise RuntimeError(str(len(failed))+' prop sources require native review')
    report['state']='ALL_49_REGISTERED_CC0_PROP_SOURCES_INSTALLED_NOT_GAMEPLAY_BOUND'
except Exception as error:
    report['error']=str(error);raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
