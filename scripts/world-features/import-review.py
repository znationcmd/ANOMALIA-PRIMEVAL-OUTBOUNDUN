"""Import credited bunkers, stations and marine scans in a separate review level.

No large-world placement is approved by this import. Source units are uncalibrated;
the review report records dimensions for subsequent scale/access validation.
"""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_SET = os.environ.get('ANOMALIA_WORLD_FEATURE_SET', 'world-features')
if SOURCE_SET not in ('world-features', 'residential-photogrammetry'):
    raise RuntimeError('Unknown review source set')
RESIDENTIAL = SOURCE_SET == 'residential-photogrammetry'
BASE = ROOT / ('SourceAssets/ResidentialPhotogrammetryPrepared_v1' if RESIDENTIAL else 'SourceAssets/WorldFeaturesPrepared_v1')
PACKAGE = '/Game/Maps/ANOMALIA_ResidentialPhotogrammetryReview_v1' if RESIDENTIAL else '/Game/Maps/ANOMALIA_WorldFeaturesReview_v1'
OWNER = unreal.Name('ANOMALIA_ResidentialPhotogrammetryReview_v1' if RESIDENTIAL else 'ANOMALIA_WorldFeaturesReview_v1')
OUT = Path(os.environ['ANOMALIA_WORLD_FEATURES_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), map=PACKAGE,
              placedInArchipelago=False, scaleValidated=False, playtested=False, models=[])
try:
    manifest = json.loads((BASE / 'manifest.json').read_text())
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not editor:
        raise RuntimeError('Full editor mesh subsystem required')
    meshes = {}
    for item in manifest['models']:
        source = (BASE / item['file']).resolve()
        if source.parent != BASE.resolve() or hashlib.sha256(source.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('Prepared source checksum failed: ' + item['id'])
        destination = item['objectPath']
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            mesh = unreal.load_asset(destination)
            if not isinstance(mesh, unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaWorldFeatureSha256') != item['sha256']:
                raise RuntimeError('Existing artist asset preserved: ' + destination)
        else:
            task = unreal.AssetImportTask()
            task.filename = str(source)
            task.destination_path = destination.rsplit('/', 1)[0] + '/Imported'
            task.automated = True
            task.replace_existing = False
            task.save = True
            tools.import_asset_tasks([task])
            task.get_objects()
            imported = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(task.destination_path, recursive=True, include_folder=False)]
            candidates = [a for a in imported if isinstance(a, unreal.StaticMesh)]
            if len(candidates) != 1:
                raise RuntimeError('Expected one baked mesh for ' + item['id'])
            mesh = unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(), destination)
            if not mesh:
                raise RuntimeError('Canonical review mesh creation failed')
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'AnomaliaWorldFeatureSha256', item['sha256'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'AnomaliaAttribution', item['author'] + ' / ' + item['license'] + ' / ' + item['source'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'AnomaliaScaleReview', 'REQUIRED_SOURCE_UNITS_UNCALIBRATED')
            options = unreal.StaticMeshReductionOptions()
            options.auto_compute_lod_screen_size = False
            options.reduction_settings = [unreal.StaticMeshReductionSettings(percent_triangles=p, screen_size=s)
                                          for p, s in [(1., 1.), (.35, .5), (.12, .25), (.04, .1)]]
            editor.set_lods(mesh, options)
            if editor.get_lod_count(mesh) < 4:
                raise RuntimeError('LOD generation failed')
            body = mesh.get_editor_property('body_setup')
            if body:
                body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
                raise RuntimeError('Mesh save failed')
        materials = mesh.get_editor_property('static_materials')
        if not materials or any(not slot.material_interface for slot in materials):
            raise RuntimeError('Missing model materials')
        bounds = mesh.get_bounds()
        dimensions = [bounds.box_extent.x * 2, bounds.box_extent.y * 2, bounds.box_extent.z * 2]
        meshes[item['id']] = mesh
        report['models'].append(dict(id=item['id'], objectPath=mesh.get_path_name(), dimensionsCm=dimensions,
                                     previewScale=min(1., 3000. / max(dimensions)),
                                     productionPlacementAllowed=False, visualReview=item.get('visualReview'),
                                     materials=len(materials), lods=editor.get_lod_count(mesh),
                                     scaleReview='REQUIRED', accessReview='REQUIRED', license=item['license']))
    if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        if not level.load_level(PACKAGE):
            raise RuntimeError('Cannot load feature review')
        if not any(a.get_actor_label() == str(OWNER) and OWNER in a.tags for a in actors.get_all_level_actors()):
            raise RuntimeError('Unowned review map preserved')
    elif not level.new_level(PACKAGE):
        raise RuntimeError('Cannot create feature review')
    def spawn(cls, label, location):
        existing = [a for a in actors.get_all_level_actors() if a.get_actor_label() == label]
        if existing:
            if len(existing) != 1 or OWNER not in existing[0].tags or existing[0].get_class() != cls.static_class():
                raise RuntimeError('Unowned or mismatched actor preserved: ' + label)
            return existing[0]
        actor = actors.spawn_actor_from_class(cls, unreal.Vector(*location))
        if not actor:
            raise RuntimeError('Spawn failed')
        actor.set_actor_label(label)
        actor.tags = [OWNER]
        return actor
    spawn(unreal.Actor, str(OWNER), (0, 0, 0))
    if not level.save_current_level():
        raise RuntimeError('Cannot persist ownership')
    x = 0.
    for item in report['models']:
        width = item['dimensionsCm'][0] * item['previewScale']
        x += width / 2 + 1000
        actor = spawn(unreal.StaticMeshActor, 'Review_' + item['id'], (x, 0, 0))
        actor.static_mesh_component.set_static_mesh(meshes[item['id']])
        actor.set_actor_scale3d(unreal.Vector(item['previewScale'], item['previewScale'], item['previewScale']))
        actor.static_mesh_component.set_collision_profile_name('NoCollision' if item['id'] == 'underwater_environment' else 'BlockAll')
        x += width / 2 + 1000
    sun = spawn(unreal.DirectionalLight, 'FeatureReviewSun', (0, 0, 10000))
    sun.set_actor_rotation(unreal.Rotator(pitch=-40, yaw=-30), False)
    spawn(unreal.SkyLight, 'FeatureReviewSky', (0, 0, 1000))
    spawn(unreal.PlayerStart, 'FeatureReviewStart', (0, -1500, 150))
    if not level.save_current_level() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Feature review did not save')
    report['state'] = 'IMPORTED_REVIEW_SAVED_SCALE_AND_ACCESS_UNVALIDATED'
except Exception as error:
    report['error'] = str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
