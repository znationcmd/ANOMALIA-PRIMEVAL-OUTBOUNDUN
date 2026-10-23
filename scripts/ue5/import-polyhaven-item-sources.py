"""Run in Unreal Editor after extracting this archive. Not executed in UE here."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parent
def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()

def main():
    manifest = json.loads((ROOT / 'download-receipt.json').read_text())
    assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    reports = []
    report_path = ROOT / 'unreal-import-report.json'
    for model in manifest['models']:
        if model['status'] != 'DOWNLOADED_DEPENDENCIES_CHECKED':
            continue
        destination = '/Game/ExternalSources/PolyHaven/' + model['modelId']
        row = {'id': model['id'], 'destination': destination, 'gameplayVerified': False}
        try:
            for record in model['files']:
                path = ROOT / 'ANOMALIA_SOURCE_ASSETS' / record['path']
                if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
                    raise ValueError('Source integrity mismatch: ' + record['path'])
            if assets.does_directory_exist(destination):
                row['status'] = 'SKIPPED_EXISTING_DIRECTORY_REVIEW_REQUIRED'
            else:
                task = unreal.AssetImportTask()
                task.filename = str(ROOT / 'ANOMALIA_SOURCE_ASSETS' / model['entryPoint'])
                task.destination_path = destination
                task.automated = True
                task.async_ = False
                task.replace_existing = False
                task.replace_existing_settings = False
                task.save = True
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                objects = list(task.get_objects())
                row['objects'] = [obj.get_path_name() for obj in objects]
                row['staticMeshes'] = [obj.get_path_name() for obj in objects if isinstance(obj, unreal.StaticMesh)]
                row['status'] = 'MESH_IMPORTED_REVIEW_REQUIRED' if row['staticMeshes'] else 'NO_STATIC_MESH_REVIEW_REQUIRED'
        except Exception as error:
            row.update(status='FAILED', error=str(error))
            unreal.log_error(str(row))
        reports.append(row)
        report_path.write_text(json.dumps(reports, indent=2), encoding='utf-8')
    unreal.log('Source import report: ' + str(report_path))

if __name__ == '__main__':
    main()
