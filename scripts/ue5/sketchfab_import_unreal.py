"""Run INSIDE Unreal Editor with Python Editor Script Plugin enabled.

Example (Windows, adapt path to your UE install):
  UnrealEditor-Cmd.exe unreal/AnomaliaPrimeval.uproject -ExecutePythonScript=scripts/ue5/sketchfab_import_unreal.py

Imports the glTF files previously retrieved through Sketchfab's authenticated official API.
This is not a Chaos vehicle conversion and does not attach assets to drivable Blueprints.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re

STAGING = Path(os.environ.get('ANOMALIA_SKETCHFAB_STAGING',
    str(Path.home() / 'Downloads' / 'ANOMALIA_Sketchfab_Staging')))
MOUNT = '/Game/Imported/Sketchfab'


def safe_asset_name(text: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', '_', text).strip('_')[:96]


def discovered(staging: Path):
    """Return only extracted assets with a separate authorized-download receipt."""
    if not staging.exists():
        return []
    result = []
    for folder in sorted(staging.iterdir()):
        if not folder.is_dir():
            continue
        provenance_path = folder / 'provenance.json'
        if not provenance_path.is_file():
            continue
        try:
            provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            continue
        if not re.fullmatch(r'[a-f0-9]{32}', str(provenance.get('uid', ''))):
            continue
        extracted = folder / 'extrait'
        # Prefer one main scene over auxiliary geometry and avoid duplicate imports.
        candidates = sorted(extracted.rglob('scene.gltf'))
        if not candidates:
            candidates = sorted(extracted.rglob('*.gltf'))
        if not candidates:
            candidates = sorted(extracted.rglob('*.glb'))
        if not candidates:
            continue
        # Avoid traversing out of the extraction folder through malicious links.
        geometry = candidates[0].resolve()
        if not geometry.is_relative_to(extracted.resolve()):
            continue
        asset_path = MOUNT + '/' + safe_asset_name(folder.name)
        result.append((geometry, asset_path, provenance))
    return result


def run() -> int:
    try:
        import unreal  # type: ignore
    except ImportError:
        print('ERROR: Must run in Unreal Editor with Python Editor Script Plugin enabled.')
        return 2
    rows = discovered(STAGING)
    print('ANOMALIA Sketchfab — authorized local receipts:', len(rows))
    if not rows:
        print('No authorized glTF staging assets; no changes made.')
        return 1
    imported = 0
    report = []
    for source_file, dest, meta in rows:
        result = {'source': str(source_file), 'uid': meta['uid'], 'unreal_package': dest}
        try:
            if unreal.EditorAssetLibrary.does_directory_exist(dest) and unreal.EditorAssetLibrary.list_assets(dest, recursive=True):
                result['etat'] = 'existing_skipped_no_overwrite'
                report.append(result)
                continue
            task = unreal.AssetImportTask()
            task.filename = str(source_file)
            task.destination_path = dest
            task.automated = True
            task.save = True
            task.replace_existing = False
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            obj_paths = [str(obj) for obj in task.imported_object_paths]
            if not obj_paths:
                result['etat'] = 'import_failed_no_assets'
                result['detail'] = 'Verify glTF Interchange importer plugin for Unreal 5.8 and editor log.'
            else:
                result['etat'] = 'imported_static_assets_not_drivable'
                result['objects'] = obj_paths
                imported += 1
        except Exception as exc:
            result['etat'] = 'import_error'
            result['detail'] = str(exc)[:350]
        report.append(result)
    output = STAGING / 'unreal_import_report.json'
    output.write_text(json.dumps({'createdUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'imported':imported, 'drivable_vehicle_blueprints_created':0, 'results':report},
        indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print('ANOMALIA: Unreal asset packages imported:', imported, '/', len(rows))
    print('Blueprints / Chaos physics: NOT created. Report:', output)
    return 0 if imported else 1


if __name__ == '__main__':
    raise SystemExit(run())
