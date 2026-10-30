"""Author local 3D streets in the already saved populated map. Preserve every house."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = '/Game/Maps/ANOMALIA_Inhabited_v2'
ART = '/Game/Anomalia/SettlementRoads_v1'
OWNER = unreal.Name('ANOMALIA_Streets_v1')
OUT = Path(os.environ['ANOMALIA_STREETS_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), map=PACKAGE,
              playtested=False, housesRemoved=0, terrainModified=False,
              intercityConnected=False, towns=[])
try:
    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
    ground = module('street_ground', ROOT / 'Scripts/archipelago_population.py')
    streets = module('street_authoring', Path(__file__).with_name('settlement_roads.py'))
    receipts = []
    for p in (ROOT / 'Saved/TransportCity').glob('run-*/populated-world.json'):
        try:
            data = json.loads(p.read_text())
            if data.get('state') == 'POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and data.get('mapPackage') == PACKAGE:
                receipts.append((p.stat().st_mtime, p, data))
        except (ValueError, OSError):
            continue
    if not receipts: raise RuntimeError('Saved owned populated world required')
    _, receipt, data = max(receipts, key=lambda row: row[0])
    plan = json.loads((receipt.parent / 'population-plan.json').read_text())
    if plan['mapPackage'] != PACKAGE or len(plan['buildings']) != data['houses'] or data['houses'] < 4500:
        raise RuntimeError('Matching complete population plan required')
    manifest = json.loads((ROOT / 'SourceAssets/RealismValidation_v2/manifest.json').read_text())
    asphalt = next(m for m in manifest['models'] if m['id'] == 'asphalt_02')
    source = ROOT / 'SourceAssets/RealismValidation_v2' / asphalt['file']
    if hashlib.sha256(source.read_bytes()).hexdigest() != asphalt['sha256']:
        raise RuntimeError('Asphalt source identity mismatch')
    original = unreal.load_asset(asphalt['objectPath'] + '_r2')
    if not isinstance(original, unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(original, 'AnomaliaZPrigimaliaRealismSha256') != asphalt['sha256']:
        raise RuntimeError('Verified native asphalt material required')
    materials = original.get_editor_property('static_materials')
    if len(materials) != 2 or any(not slot.material_interface for slot in materials):
        raise RuntimeError('Expected original asphalt and road paint materials')
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    if not level.load_level(PACKAGE): raise RuntimeError('Populated map did not reopen')
    if not any(a.get_actor_label() == 'ANOMALIA_InhabitedArchipelago_48km' for a in actors.get_all_level_actors()):
        raise RuntimeError('Owned inhabited landscape required')
    present = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    obstacles = list(plan['buildings'])
    for a in present.values():
        if isinstance(a, unreal.StaticMeshActor) and unreal.Name('ANOMALIA_WorldFeatures_v1') in a.tags:
            feature_mesh = a.static_mesh_component.get_editor_property('static_mesh')
            if feature_mesh:
                position = a.get_actor_location(); bounds = feature_mesh.get_bounds()
                obstacles.append(dict(east=position.x / 100, north=-position.y / 100,
                                      width=bounds.box_extent.x * .02, depth=bounds.box_extent.y * .02))
    surface = ground.sampled_surface(unreal.AnomaliaZPrigimaliaWorldImportLibrary.inhabited_archipelago_height)
    cache = ROOT / 'SourceAssets/SettlementRoads_v1'; cache.mkdir(parents=True, exist_ok=True)
    for site in plan['settlements']:
        result = streets.build_streets(site, obstacles, surface, ground.ground_envelope)
        if not result['segments']:
            report['towns'].append(dict(id=site['id'], segments=0)); continue
        content = result['geometry'].glb(site['id']); digest = hashlib.sha256(content).hexdigest()
        file = cache / (site['id'] + '.glb')
        if file.exists() and file.read_bytes() != content:
            raise RuntimeError('Existing authored street geometry preserved: ' + site['id'])
        if not file.exists(): file.write_bytes(content)
        destination = ART + '/' + site['id'] + '/SM_Streets'
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            mesh = unreal.load_asset(destination)
            if not isinstance(mesh, unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaZPrigimaliaStreetGeometrySha256') != digest:
                raise RuntimeError('Existing artist street mesh preserved')
        else:
            task = unreal.AssetImportTask(); task.filename = str(file)
            task.destination_path = ART + '/' + site['id'] + '/Imported'
            task.automated = True; task.replace_existing = False; task.save = True
            tools.import_asset_tasks([task]); task.get_objects()
            imported = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(task.destination_path, recursive=True, include_folder=False)]
            candidates = [a for a in imported if isinstance(a, unreal.StaticMesh)]
            if len(candidates) != 1: raise RuntimeError('One authored street mesh expected')
            mesh = unreal.EditorAssetLibrary.duplicate_asset(candidates[0].get_path_name(), destination)
            if not mesh or len(mesh.get_editor_property('static_materials')) != 3:
                raise RuntimeError('Three street material slots expected')
            mesh.set_material(0, materials[0].material_interface)
            mesh.set_material(1, materials[1].material_interface)
            body = mesh.get_editor_property('body_setup')
            if not body: raise RuntimeError('Street collision body required')
            body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'AnomaliaZPrigimaliaStreetGeometrySha256', digest)
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, 'AnomaliaZPrigimaliaAttribution', 'Original ANOMALIA geometry; asphalt texture: ' + asphalt['author'] + ' / ' + asphalt['license'] + ' / ' + asphalt['source'])
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
                raise RuntimeError('Street mesh save failed')
        label = 'ANOMALIA_Streets_' + site['id']; actor = present.get(label)
        if actor:
            if not isinstance(actor, unreal.StaticMeshActor) or OWNER not in actor.tags or actor.static_mesh_component.get_editor_property('static_mesh') != mesh:
                raise RuntimeError('Existing artist road actor preserved')
        else:
            actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(site['east'] * 100, -site['north'] * 100, result['originHeight'] * 100))
            if not actor: raise RuntimeError('Street actor creation failed')
            actor.set_actor_label(label); actor.tags = [OWNER]
            actor.set_editor_property('is_spatially_loaded', False)
            actor.static_mesh_component.set_static_mesh(mesh)
            actor.static_mesh_component.set_collision_profile_name('BlockAll')
        report['towns'].append(dict(id=site['id'], segments=result['segments'], junctions=result['junctions'], centrelineMetres=result['centrelineMetres'], objectPath=mesh.get_path_name()))
    if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Town streets did not save')
    report.update(state='TOWN_STREETS_SAVED_NOT_PLAYTESTED',
                  centrelineMetres=sum(t.get('centrelineMetres', 0) for t in report['towns']),
                  townsWithStreets=sum(t['segments'] > 0 for t in report['towns']))
except Exception as error:
    report['error'] = str(error); raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
