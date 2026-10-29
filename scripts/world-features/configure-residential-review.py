"""Add eight cameras and source-faithful rendering to the four imported candidates."""
import json
import math
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = '/Game/Maps/ANOMALIA_ResidentialPhotogrammetryReview_v1'
OWNER = unreal.Name('ANOMALIA_ResidentialPhotogrammetryReview_v1')
OUT = Path(os.environ['ANOMALIA_RESIDENTIAL_SETUP_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), map=PACKAGE, cameras=[], models=[])
try:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if not editor:
        raise RuntimeError('Full static mesh editor subsystem required')
    if not level.load_level(PACKAGE):
        raise RuntimeError('Imported residential review map required')
    present = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    if str(OWNER) not in present or OWNER not in present[str(OWNER)].tags:
        raise RuntimeError('Owned residential map required')
    def spawn(cls, label, location):
        actor = present.get(label)
        if actor:
            if actor.get_class() != cls.static_class() or OWNER not in actor.tags:
                raise RuntimeError('Existing artist actor preserved: ' + label)
        else:
            actor = actors.spawn_actor_from_class(cls, location)
            if not actor: raise RuntimeError('Review actor creation failed')
            actor.set_actor_label(label); actor.tags = [OWNER]
        return actor
    manifest = json.loads((ROOT / 'SourceAssets/ResidentialPhotogrammetryPrepared_v1/manifest.json').read_text())
    for number, item in enumerate(manifest['models']):
        actor = present.get('Review_' + item['id'])
        if not actor or OWNER not in actor.tags:
            raise RuntimeError('Imported review actor missing')
        mesh = actor.static_mesh_component.get_editor_property('static_mesh')
        if not mesh or unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaZPrigimaliaWorldFeatureSha256') != item['sha256']:
            raise RuntimeError('Native candidate source identity mismatch')
        settings = editor.get_nanite_settings(mesh)
        settings.set_editor_property('enabled', False)
        editor.set_nanite_settings(mesh, settings, apply_changes=True)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
            raise RuntimeError('Candidate rendering settings did not save')
        location = actor.get_actor_location(); bounds = mesh.get_bounds(); scale = actor.get_actor_scale3d().x
        centre = location + bounds.origin * scale
        radius = max(bounds.box_extent.x, bounds.box_extent.y) * scale
        for side, angle in enumerate((-55., 125.)):
            radians = math.radians(angle)
            position = centre + unreal.Vector(math.cos(radians)*radius*2.5, math.sin(radians)*radius*2.5, max(250., bounds.box_extent.z*scale*.7))
            label = 'ResidentialCamera_%02d_%d' % (number, side)
            camera = spawn(unreal.CameraActor, label, position)
            camera.set_actor_location(position, False, False)
            camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, centre), False)
            camera.camera_component.set_editor_property('field_of_view',55.)
            report['cameras'].append(label)
        report['models'].append(dict(id=item['id'], lods=mesh.get_num_lods(), naniteEnabled=False))
    for label, tag in [('FeatureReviewSun', 'ReviewSun'), ('FeatureReviewSky', 'ReviewSky')]:
        actor = present.get(label)
        if not actor or OWNER not in actor.tags:
            raise RuntimeError('Owned review lighting required')
        actor.tags = list(set(list(actor.tags) + [unreal.Name(tag)]))
        if label == 'FeatureReviewSun':
            actor.set_actor_rotation(unreal.Rotator(pitch=-40, yaw=-30), False)
            actor.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(3.)
    spawn(unreal.SkyAtmosphere, 'ResidentialReviewAtmosphere', unreal.Vector(0,0,0))
    if not level.save_current_level() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Residential camera setup did not save')
    report['state'] = 'RESIDENTIAL_CAMERAS_SAVED_NOT_RENDERED'
except Exception as error:
    report['error'] = str(error); raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
