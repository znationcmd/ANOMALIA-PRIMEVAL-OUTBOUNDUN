"""Read-only audit of every authored house/foliage/street/bunker mesh on disk.

Loads World Partition actors in batches and restores their transient loaded state.
No package is saved and no actor is replaced or deleted. This is not a render test.
"""
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = '/Game/Maps/ANOMALIA_Inhabited_v2'
OUT = Path(os.environ['ANOMALIA_DETAILED_WORLD_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), map=PACKAGE,
              rendered=False, playtested=False, packagesModified=False, meshes=[], violations=[])
try:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    wp = unreal.WorldPartitionBlueprintLibrary
    if not level.load_level(PACKAGE):
        raise RuntimeError('Detailed populated world could not reopen')
    descriptors = wp.get_actor_descs()
    if descriptors is None:
        raise RuntimeError('Saved World Partition descriptors required')
    known = {}
    for folder, tag, suffix in [('RealismValidation_v2', 'AnomaliaZPrigimaliaRealismSha256', '_r2'),
                                 ('WorldFeaturesPrepared_v1', 'AnomaliaZPrigimaliaWorldFeatureSha256', ''),
                                 ('ResidentialPhotogrammetryPrepared_v1', 'AnomaliaZPrigimaliaWorldFeatureSha256', '')]:
        manifest = json.loads((ROOT / 'SourceAssets' / folder / 'manifest.json').read_text())
        for item in manifest['models']:
            path = item['objectPath'] + suffix
            known[path.rsplit('/', 1)[0] + '/' + path.rsplit('/', 1)[1] + '.' + path.rsplit('/', 1)[1]] = (tag, item['sha256'])
    expected_classes = {'/Script/Engine.StaticMeshActor', '/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaSceneryCluster'}
    targets = []
    for desc in descriptors:
        native = desc.get_editor_property('native_class')
        if native and native.get_path_name() in expected_classes:
            targets.append(desc)
    house_labels = [str(d.get_editor_property('label')) for d in targets
                    if str(d.get_editor_property('label')).startswith('ANOMALIA_Inhabited1_')
                    and '_house_' in str(d.get_editor_property('label'))]
    report.update(savedHouseDescriptors=len(house_labels), savedMeshActorDescriptors=len(targets))
    if len(house_labels) != 4760 or len(set(house_labels)) != 4760:
        raise RuntimeError('Expected all 4,760 unique saved detailed house actors')
    initially_loaded = {a.get_actor_label() for a in actors.get_all_level_actors()}
    inspected = set(); meshes = {}; component_count = 0
    for start in range(0, len(targets), 64):
        batch = targets[start:start + 64]
        labels = {str(d.get_editor_property('label')) for d in batch}
        guids = [d.get_editor_property('guid') for d in batch]
        to_unload = [d.get_editor_property('guid') for d in batch
                     if str(d.get_editor_property('label')) not in initially_loaded]
        wp.load_actors(guids)
        try:
            loaded = {a.get_actor_label(): a for a in actors.get_all_level_actors() if a.get_actor_label() in labels}
            if set(loaded) != labels:
                raise RuntimeError('Some saved mesh actors did not load for audit')
            for label, actor in loaded.items():
                components = actor.get_components_by_class(unreal.StaticMeshComponent)
                if not components:
                    report['violations'].append(dict(actor=label, reason='NO_GEOMETRY_COMPONENT'))
                for component in components:
                    component_count += 1
                    mesh = component.get_editor_property('static_mesh')
                    if not mesh:
                        report['violations'].append(dict(actor=label, reason='MISSING_MESH')); continue
                    path = mesh.get_path_name()
                    if path.startswith('/Engine/BasicShapes/'):
                        report['violations'].append(dict(actor=label, reason='ENGINE_PRIMITIVE', mesh=path)); continue
                    if path not in meshes:
                        if path in known:
                            tag, digest = known[path]
                            verified = unreal.EditorAssetLibrary.get_metadata_tag(mesh, tag) == digest
                        else:
                            verified = (path.startswith('/Game/Anomalia/SettlementRoads_v1/')
                                        and bool(unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaZPrigimaliaStreetGeometrySha256')))
                        materials = mesh.get_editor_property('static_materials')
                        triangles = mesh.get_num_triangles(0)
                        nanite_triangles = mesh.get_num_nanite_triangles()
                        meshes[path] = dict(path=path, sourceIdentityVerified=verified,
                                            triangles=triangles, naniteTriangles=nanite_triangles,
                                            lods=mesh.get_num_lods(), materials=len(materials))
                        # A Nanite fallback or a small street fragment may have few
                        # triangles. Source identity and nonempty geometry establish
                        # this check; a polygon threshold is not a realism test.
                        if not verified or max(triangles, nanite_triangles) <= 0:
                            report['violations'].append(dict(actor=label, reason='UNVERIFIED_OR_EMPTY_GEOMETRY', mesh=path))
                        if not materials or any(not slot.material_interface or slot.material_interface.get_path_name().startswith('/Engine/EngineMaterials/DefaultMaterial') for slot in materials):
                            report['violations'].append(dict(actor=label, reason='MISSING_OR_DEFAULT_MATERIAL', mesh=path))
                    for material in component.get_materials():
                        if not material or material.get_path_name().startswith('/Engine/EngineMaterials/DefaultMaterial'):
                            report['violations'].append(dict(actor=label, reason='DEFAULT_COMPONENT_MATERIAL', mesh=path))
                inspected.add(label)
        finally:
            wp.unload_actors(to_unload)
        unreal.log('ANOMALIA detailed mesh audit: ' + str(len(inspected)) + '/' + str(len(targets)))
    report.update(inspectedActors=len(inspected), inspectedMeshComponents=component_count,
                  meshes=list(meshes.values()), enginePrimitivesFound=sum(v['reason'] == 'ENGINE_PRIMITIVE' for v in report['violations']))
    if report['violations']:
        raise RuntimeError('Detailed mesh audit found ' + str(len(report['violations'])) + ' violations')
    report['state'] = 'DETAILED_MESH_AUDIT_PASSED_NOT_RENDERED'
except Exception as error:
    report['error'] = str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
