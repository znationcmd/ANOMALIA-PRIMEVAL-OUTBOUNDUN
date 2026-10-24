"""Read back three actual model assets in the installed editor project, without saving."""
import json
import os
from pathlib import Path
import unreal

PACKAGE = '/Game/Maps/ANOMALIA_InteractiveRealismReview_v1'
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):
    raise RuntimeError('Installed review map is unavailable')
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
models = []
for identifier in ['wood_house_enterable', 'modular_shed_interior', 'sports_car_930_review']:
    found = [a for a in actors.get_all_level_actors() if a.get_actor_label() == 'Review_' + identifier]
    if len(found) != 1:
        raise RuntimeError('Missing unique installed model: ' + identifier)
    mesh = found[0].get_component_by_class(unreal.StaticMeshComponent).get_editor_property('static_mesh')
    if not mesh or not mesh.get_path_name().startswith('/Game/Anomalia/InteractiveRealismReview_v1/'):
        raise RuntimeError('Installed mesh does not belong to this review')
    if not unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaInteractiveRealismSha256'):
        raise RuntimeError('Missing source identity on installed asset')
    materials = mesh.get_editor_property('static_materials')
    if not materials or any(not m.material_interface for m in materials):
        raise RuntimeError('Installed material missing')
    models.append(dict(id=identifier, mesh=mesh.get_path_name(), materials=len(materials)))
Path(os.environ['ANOMALIA_REVIEW_INSTALL_PROBE']).write_text(json.dumps(dict(
    state='INSTALLED_REAL_MODEL_REVIEW_REOPENED', sourceCommit=os.environ.get('GITHUB_SHA'),
    mapPackage=PACKAGE, models=models, playableIntegrated=False), indent=2), encoding='utf-8')
