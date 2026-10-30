"""Apply depth-based PBR seabed shading to the owned populated world only.

Retains the original land material and every actor/height sample. No ocean renderer,
underwater gameplay or completed-map claim is implied by material assignment.
"""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = '/Game/Maps/ANOMALIA_Inhabited_v2'
ORIGINAL = '/Game/Anomalia/Inhabited_v2/M_PBRGround'
ART = '/Game/Anomalia/MarineTerrain_v1'
DEST = ART + '/M_LandShoreSeabed_v2'
OUT = Path(os.environ['ANOMALIA_MARINE_TERRAIN_REPORT'])
report = dict(state='FAILED', sourceCommit=os.environ.get('GITHUB_SHA'), map=PACKAGE,
              rendered=False, playtested=False, oceanRenderingImplemented=False)
try:
    # A successful receipt must exist before reopening a world that may be incomplete.
    receipts = []
    for p in (ROOT / 'Saved/TransportCity').glob('run-*/populated-world.json'):
        try:
            data = json.loads(p.read_text())
            if data.get('state') == 'POPULATED_WORLD_CREATED_NOT_PLAYTESTED' and data.get('mapPackage') == PACKAGE and data.get('houses', 0) >= 4500:
                receipts.append((p.stat().st_mtime, p, data))
        except (ValueError, OSError):
            continue
    if not receipts:
        raise RuntimeError('Completed owned populated-world save receipt required; incomplete map preserved')
    _, receipt, population = max(receipts, key=lambda row: row[0])
    report['populationReceipt'] = str(receipt)
    registry_path = ROOT.parent / 'docs/art/marine-terrain-sources.json'
    identity = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    registry = json.loads(registry_path.read_text())
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level.load_level(PACKAGE):
        raise RuntimeError('Owned populated world unavailable')
    # World Partition reopens only loaded editor regions. Load terrain proxies
    # explicitly before counting or assigning their material; leave towns streamed.
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    if descriptors is None:
        raise RuntimeError('World Partition actor descriptors unavailable')
    terrain_guids = []
    for descriptor in descriptors:
        native_class = descriptor.get_editor_property('native_class')
        if native_class and native_class.get_path_name() in {
                '/Script/Landscape.Landscape', '/Script/Landscape.LandscapeStreamingProxy'}:
            terrain_guids.append(descriptor.get_editor_property('guid'))
    report['terrainActorDescriptors'] = len(terrain_guids)
    unreal.WorldPartitionBlueprintLibrary.load_actors(terrain_guids)
    landscapes = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.LandscapeProxy)]
    count = sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in landscapes)
    report['loadedTerrainComponents'] = count
    if count != 576 or not any(a.get_actor_label() == 'ANOMALIA_InhabitedArchipelago_48km' for a in landscapes):
        raise RuntimeError('Expected owned complete 576-component terrain; loaded ' + str(count))
    allowed = {ORIGINAL + '.M_PBRGround', DEST + '.' + DEST.rsplit('/', 1)[1]}
    for a in landscapes:
        material = a.get_editor_property('landscape_material')
        if not material or material.get_path_name() not in allowed:
            raise RuntimeError('Artist terrain material preserved: ' + a.get_actor_label())
    for model in registry['models']:
        if model['license'] != 'CC0-1.0':
            raise RuntimeError('Unreviewed texture license')
        for entry in model['files']:
            source = ROOT / 'SourceAssets/MarineTerrain_v1' / entry['path']
            if source.parent != ROOT / 'SourceAssets/MarineTerrain_v1' or hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
                raise RuntimeError('Marine source integrity failed')
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        mat = unreal.load_asset(DEST)
        if not isinstance(mat, unreal.Material) or unreal.EditorAssetLibrary.get_metadata_tag(mat, 'AnomaliaZPrigimaliaMarineRegistrySha256') != identity:
            raise RuntimeError('Existing material preserved; source identity differs')
    else:
        # Reconstruct the existing forest layer from its verified source textures.
        original = unreal.load_asset(ORIGINAL)
        if not isinstance(original, unreal.Material):
            raise RuntimeError('Original owned land material required')
        textures = {}
        land = json.loads((ROOT.parent / 'docs/art/realism-validation-sources.json').read_text())
        forest = next(m for m in land['models'] if m['id'] == 'forest_ground_04')
        for channel, suffix in [('diff', 'diff_2k.jpg'), ('nor_gl', 'nor_gl_2k.jpg'), ('rough', 'rough_2k.jpg')]:
            entry = next(f for f in forest['files'] if f['path'].endswith(suffix))
            source = ROOT / 'Saved/RealismSourceCache/forest_ground_04' / entry['path']
            if hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
                raise RuntimeError('Original ground source integrity failed')
            texture = unreal.load_asset('/Game/Anomalia/Inhabited_v2/Ground/' + source.stem)
            if not isinstance(texture, unreal.Texture2D):
                raise RuntimeError('Original ground texture unavailable')
            textures[('land', channel)] = texture
        for model in registry['models']:
            for entry in model['files']:
                source = ROOT / 'SourceAssets/MarineTerrain_v1' / entry['path']
                destination = ART + '/Textures/' + source.stem
                if unreal.EditorAssetLibrary.does_asset_exist(destination):
                    texture = unreal.load_asset(destination)
                    if not isinstance(texture, unreal.Texture2D) or unreal.EditorAssetLibrary.get_metadata_tag(texture, 'AnomaliaZPrigimaliaSourceSha256') != entry['sha256']:
                        raise RuntimeError('Existing texture preserved: ' + destination)
                else:
                    task = unreal.AssetImportTask()
                    task.filename = str(source)
                    task.destination_path = ART + '/Textures'
                    task.automated = True
                    task.replace_existing = False
                    task.save = True
                    tools.import_asset_tasks([task])
                    texture = next((o for o in task.get_objects() if isinstance(o, unreal.Texture2D)), None)
                    if not texture:
                        raise RuntimeError('Marine texture import failed')
                    if entry['channel'] != 'diff':
                        texture.set_editor_property('srgb', False)
                    if entry['channel'] == 'nor_gl':
                        texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
                        texture.set_editor_property('flip_green_channel', True)
                    unreal.EditorAssetLibrary.set_metadata_tag(texture, 'AnomaliaZPrigimaliaSourceSha256', entry['sha256'])
                    if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
                        raise RuntimeError('Texture save failed')
                textures[(model['id'], entry['channel'])] = texture
        mat = tools.create_asset(DEST.rsplit('/', 1)[1], ART, unreal.Material, unreal.MaterialFactoryNew())
        if not mat:
            raise RuntimeError('Marine material creation failed')
        def node(name):
            return lib.create_material_expression(mat, getattr(unreal, 'MaterialExpression' + name))
        def wire(source, target, pin, output=''):
            if not lib.connect_material_expressions(source, output, target, pin):
                raise RuntimeError('Material connection failed: ' + pin)
        def constant(value):
            result = node('Constant'); result.set_editor_property('r', value); return result
        def op(name, a, b):
            result = node(name); wire(a, result, 'A'); wire(b, result, 'B'); return result
        position = node('WorldPosition')
        xy = node('ComponentMask')
        for key, value in [('r', True), ('g', True), ('b', False), ('a', False)]:
            xy.set_editor_property(key, value)
        wire(position, xy, '')
        z = node('ComponentMask')
        for key, value in [('r', False), ('g', False), ('b', True), ('a', False)]:
            z.set_editor_property(key, value)
        wire(position, z, '')
        def mask(top, span):
            result = node('Clamp')
            wire(op('Divide', op('Subtract', constant(top), z), constant(span)), result, '')
            return result
        # Sea level is Z=0. Shore: +5m to -5m; deeper rock: -25m to -75m.
        shore = mask(500., 1000.)
        deep = mask(-2500., 5000.)
        uv = {'land': op('Divide', xy, constant(300.))}
        for model in registry['models']:
            uv[model['id']] = op('Divide', xy, constant(model['physicalTileMetres'] * 100.))
        def sample(layer, channel):
            result = node('TextureSample')
            result.set_editor_property('texture', textures[(layer, channel)])
            if channel == 'nor_gl':
                result.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            elif channel == 'rough':
                result.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            wire(uv[layer], result, 'UVs')
            return result
        def blend(a, b, alpha, output):
            result = node('LinearInterpolate')
            wire(a, result, 'A', output); wire(b, result, 'B', output); wire(alpha, result, 'Alpha')
            return result
        for channel, prop in [('diff', unreal.MaterialProperty.MP_BASE_COLOR), ('nor_gl', unreal.MaterialProperty.MP_NORMAL), ('rough', unreal.MaterialProperty.MP_ROUGHNESS)]:
            output = 'R' if channel == 'rough' else 'RGB'
            seabed = blend(sample('coast_sand_02', channel), sample('coast_sand_rocks_02', channel), deep, output)
            result = node('LinearInterpolate')
            wire(sample('land', channel), result, 'A', output)
            wire(seabed, result, 'B'); wire(shore, result, 'Alpha')
            if channel == 'nor_gl':
                normal = node('Normalize'); wire(result, normal, ''); result = normal
            if not lib.connect_material_property(result, '', prop):
                raise RuntimeError('Material property connection failed')
        lib.layout_material_expressions(mat)
        lib.recompile_material(mat)
        unreal.EditorAssetLibrary.set_metadata_tag(mat, 'AnomaliaZPrigimaliaMarineRegistrySha256', identity)
        unreal.EditorAssetLibrary.set_metadata_tag(mat, 'AnomaliaZPrigimaliaOriginalLandMaterial', ORIGINAL)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False):
            raise RuntimeError('Marine material did not save')
    for a in landscapes:
        a.set_editor_property('landscape_material', mat)
    if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Marine terrain assignments did not save')
    report.update(state='MARINE_TERRAIN_MATERIAL_SAVED_NOT_RENDERED', terrainComponents=count,
                  material=mat.get_path_name(), sourceResolution=4096, shoreBlendMetres=[5, -5],
                  deepRockBlendMetres=[-25, -75], originalMaterialRetained=ORIGINAL,
                  decorativeSeabedCoverageComplete=False)
except Exception as error:
    report['error'] = str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
