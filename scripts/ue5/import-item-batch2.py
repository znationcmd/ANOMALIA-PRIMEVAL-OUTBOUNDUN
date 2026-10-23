"""Execute inside UE5 Editor after extracting the complete batch archive."""
import hashlib,json
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'conversion-receipt.json').read_text(encoding='utf-8'))
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
reports=[]
for model in manifest['models']:
    row={'id':model['id'],'gameplayVerified':False,'visualApproved':False}
    try:
        if model.get('licenseReviewRequired'):
            row['status']='HELD_LICENSE_HEADER_REVIEW'
        elif any('Missing texture:' in w for w in model.get('warnings',[])):
            row['status']='HELD_MISSING_TEXTURE'
        elif model['status']!='CONVERTED_STATIC_REVIEW_REQUIRED':
            row['status']='SKIPPED_UNCONVERTED'
        else:
            source=(ROOT/model['file']).resolve()
            if not source.is_relative_to(ROOT.resolve()):raise ValueError('Unsafe source path')
            if source.stat().st_size!=model['bytes'] or hashlib.sha256(source.read_bytes()).hexdigest()!=model['sha256']:
                raise ValueError('Source checksum differs')
            dest='/Game/ExternalSources/ItemBatch2/'+model['id']
            row['destination']=dest
            if assets.does_directory_exist(dest):row['status']='SKIPPED_EXISTING_DIRECTORY'
            else:
                task=unreal.AssetImportTask()
                task.filename=str(source)
                task.destination_path=dest
                task.automated=True
                task.async_=False
                task.replace_existing=False
                task.replace_existing_settings=False
                task.save=True
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                objects=list(task.get_objects())
                row['objects']=[obj.get_path_name() for obj in objects]
                row['staticMeshes']=[obj.get_path_name() for obj in objects if isinstance(obj,unreal.StaticMesh)]
                row['status']='MESH_IMPORTED_REVIEW_REQUIRED' if row['staticMeshes'] else 'NO_STATIC_MESH_REVIEW_REQUIRED'
    except Exception as error:row.update(status='FAILED',error=str(error))
    reports.append(row)
    (ROOT/'unreal-import-batch2-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
unreal.log('Batch 2 complete; inspect unreal-import-batch2-report.json before accepting any asset.')
