"""Preserve full authored foliage/street geometry on the compatibility renderer."""
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = Path(os.environ['ANOMALIA_RENDER_SETTINGS_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), meshes=[], rendered=False)
try:
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not editor: raise RuntimeError('Full static mesh editor subsystem required')
    manifest = json.loads((ROOT / 'SourceAssets/RealismValidation_v2/manifest.json').read_text())
    assets = []
    for item in manifest['models']:
        if item['id'] not in {'island_tree_02', 'grass_medium_01'}: continue
        mesh = unreal.load_asset(item['objectPath'] + '_r2')
        if not isinstance(mesh, unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaRealismSha256') != item['sha256']:
            raise RuntimeError('Verified owned foliage mesh required')
        assets.append(mesh)
    for path in unreal.EditorAssetLibrary.list_assets('/Game/Anomalia/SettlementRoads_v1', recursive=True, include_folder=False):
        if not path.endswith('/SM_Streets.SM_Streets') and not path.endswith('/SM_Streets'): continue
        mesh = unreal.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh) or not unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaStreetGeometrySha256'):
            raise RuntimeError('Unknown artist street asset preserved')
        assets.append(mesh)
    if len(assets) != 29: raise RuntimeError('Expected two foliage meshes and 27 owned street meshes')
    for mesh in assets:
        settings = editor.get_nanite_settings(mesh)
        before = settings.get_editor_property('enabled')
        if before:
            if not unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaNaniteBeforeCompatibilityFix'):
                unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'AnomaliaNaniteBeforeCompatibilityFix', 'true')
            settings.set_editor_property('enabled', False)
            editor.set_nanite_settings(mesh, settings, apply_changes=True)
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
                raise RuntimeError('Detailed geometry settings did not save')
        report['meshes'].append(dict(path=mesh.get_path_name(), naniteBefore=before,
                                     naniteAfter=editor.get_nanite_settings(mesh).get_editor_property('enabled'),
                                     lods=mesh.get_num_lods(), triangles=mesh.get_num_triangles(0)))
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level.load_level('/Game/Maps/ANOMALIA_VisualValidation_v1'):
        raise RuntimeError('Detailed review scene required')
    road = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == 'ReviewRoad'), None)
    if not isinstance(road, unreal.StaticMeshActor) or unreal.Name('ANOMALIA_VisualValidation_v1_Owner') not in road.tags:
        raise RuntimeError('Owned review road required')
    # The GLB's long axis is glTF Z / Unreal Y. Rotate it onto the X lane where
    # the detailed car and truck are parked, leaving the house clear of asphalt.
    road.set_actor_rotation(unreal.Rotator(yaw=90), False)
    if not level.save_current_level(): raise RuntimeError('Review street orientation did not save')
    report.update(state='DETAILED_COMPATIBILITY_SETTINGS_SAVED_NOT_RENDERED', reviewRoadYaw=90)
except Exception as error:
    report['error'] = str(error); raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
