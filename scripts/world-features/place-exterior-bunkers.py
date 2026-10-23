"""Place the verified exterior bunker scan in reserved settlement corner corridors.
Does not bury the interior scan or claim functional underground entrances.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = '/Game/Maps/ANOMALIA_Inhabited_v2'
OWNER = unreal.Name('ANOMALIA_WorldFeatures_v1')
OUT = Path(os.environ['ANOMALIA_BUNKER_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), map=PACKAGE,
              playtested=False, undergroundEntrancesBuilt=False, placements=[], rejected=[])
try:
    receipts = []
    for p in (ROOT / 'Saved/TransportCity').glob('run-*/populated-world.json'):
        try:
            data = json.loads(p.read_text())
            if data.get('state') == 'POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and data.get('mapPackage') == PACKAGE:
                receipts.append((p.stat().st_mtime, p, data))
        except (ValueError, OSError):
            continue
    if not receipts:
        raise RuntimeError('Saved populated world receipt required')
    _, receipt, data = max(receipts, key=lambda row: row[0])
    plan = json.loads((receipt.parent / 'population-plan.json').read_text())
    if len(plan['buildings']) != data['houses'] or data['houses'] < 4500 or plan['mapPackage'] != PACKAGE:
        raise RuntimeError('Complete matching population plan required')
    manifest = json.loads((ROOT / 'SourceAssets/WorldFeaturesPrepared_v1/manifest.json').read_text())
    model = next(m for m in manifest['models'] if m['id'] == 'bunker_o323')
    source = ROOT / 'SourceAssets/WorldFeaturesPrepared_v1' / model['file']
    if hashlib.sha256(source.read_bytes()).hexdigest() != model['sha256']:
        raise RuntimeError('Bunker source identity mismatch')
    mesh = unreal.load_asset(model['objectPath'])
    if not isinstance(mesh, unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh, 'AnomaliaWorldFeatureSha256') != model['sha256']:
        raise RuntimeError('Verified native exterior bunker import required')
    bounds = mesh.get_bounds()
    width, depth, height = bounds.box_extent.x * .02, bounds.box_extent.y * .02, bounds.box_extent.z * .02
    if not (8 < width < 20 and 8 < depth < 20 and 2 < height < 6):
        raise RuntimeError('Bunker dimensions outside expected full-scale exterior envelope')
    spec = importlib.util.spec_from_file_location('bunker_ground', ROOT / 'Scripts/archipelago_population.py')
    ground = importlib.util.module_from_spec(spec); spec.loader.exec_module(ground)
    surface = ground.sampled_surface(unreal.AnomaliaWorldImportLibrary.inhabited_archipelago_height)
    proposals = []
    for site in plan['settlements']:
        e, n = site['east'] + 365., site['north'] + 365.
        low, high = ground.ground_envelope(surface, e, n, width, depth)
        if low < 5 or high - low > .12:
            report['rejected'].append(dict(site=site['id'], reason='WET_OR_UNEVEN')); continue
        if any(abs(e - b['east']) < (width + b['width']) / 2 + 5 and
               abs(n - b['north']) < (depth + b['depth']) / 2 + 5 for b in plan['buildings']):
            report['rejected'].append(dict(site=site['id'], reason='BUILDING_CLEARANCE')); continue
        z = high - (bounds.origin.z - bounds.box_extent.z) / 100. - .05
        proposals.append(dict(id=site['id'] + '_ExteriorBunker', east=e, north=n, z=z))
    if not proposals:
        raise RuntimeError('No dry clear bunker locations')
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level.load_level(PACKAGE):
        raise RuntimeError('Saved populated world could not reopen')
    # Exterior features stay loaded during authoring/re-runs so idempotence does not
    # depend on editor World Partition regions. Limit is at most one per 27 settlements.
    existing = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
    for item in proposals:
        name = 'ANOMALIA_Features_' + item['id']
        actor = existing.get(name)
        if actor:
            if not isinstance(actor, unreal.StaticMeshActor) or OWNER not in actor.tags or actor.static_mesh_component.get_editor_property('static_mesh') != mesh:
                raise RuntimeError('Existing artist actor preserved: ' + name)
            actor.set_actor_location(unreal.Vector(item['east'] * 100, -item['north'] * 100, item['z'] * 100), False, False)
            report['placements'].append(dict(**item, existing=True)); continue
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(item['east'] * 100, -item['north'] * 100, item['z'] * 100))
        if not actor:
            raise RuntimeError('Bunker placement failed')
        actor.set_actor_label(name); actor.tags = [OWNER]
        actor.set_editor_property('is_spatially_loaded', False)
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        report['placements'].append(dict(**item, existing=False))
    if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Exterior bunker placements did not save')
    report.update(state='EXTERIOR_BUNKERS_SAVED_NOT_PLAYTESTED', count=len(proposals),
                  model=model['id'], dimensionsMetres=[width, depth, height],
                  sourceGeometryPlacementReview='NATIVE_ENVELOPE_AND_TERRAIN_CLEARANCE_ONLY')
except Exception as error:
    report['error'] = str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
