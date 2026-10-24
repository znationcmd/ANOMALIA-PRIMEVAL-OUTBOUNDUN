"""Run in Blender 4.5 with the pinned MPFB extension enabled.

Creates clothed, skinned civilian source assets. This is an art preparation
tool, not a claim of Unreal integration or final visual approval.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import addon_utils
from mathutils import Vector


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset-pack', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int, default=28)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    expected_pack_sha = 'b542127a8e25547c7c29c19f2d1d2adb9a664c80396ecd694095dbc8028a0107'
    if sha256(args.asset_pack) != expected_pack_sha:
        raise RuntimeError('The source asset pack differs from the reviewed CC0 pack')
    bpy.context.preferences.filepaths.save_version = 0
    addon_utils.enable('bl_ext.user_default.mpfb', default_set=False)
    import bl_ext.user_default.mpfb as mpfb
    services = mpfb.MPFB_CONTEXTUAL_INFORMATION['SERVICES']
    human = services['HumanService']
    assets = services['AssetService']
    targets = services['TargetService']
    objects = services['ObjectService']
    export = services['ExportService']
    locations = services['LocationService']
    # Check the input before extraction; the pack contains core CC0 assets only.
    import zipfile
    with zipfile.ZipFile(args.asset_pack) as archive:
        for name in archive.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts:
                raise RuntimeError('Unsafe asset pack path')
        metadata = json.loads(archive.read('packs/makehuman_system_assets.json'))
        if not metadata or any(entry.get('license') != 'CC0' for entry in metadata.values()):
            raise RuntimeError('The asset pack contains an unapproved license')
    error = assets.fix_and_extract_asset_pack_zip(args.asset_pack, locations.get_user_data())
    if error:
        raise RuntimeError(error)
    roster = []
    for group, gender, child in [('man', 1., False), ('woman', 0., False),
                                 ('boy', 1., True), ('girl', 0., True)]:
        for index in range(7):
            if len(roster) >= args.limit:
                break
            identity = f'{group}_{index + 1:02d}'
            destination = output / identity
            destination.mkdir(exist_ok=True)
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            macro = targets.get_default_macro_info_dict()
            races = [(.1, .8, .1), (.8, .1, .1), (.1, .1, .8),
                     (.3, .4, .3), (.15, .65, .2), (.6, .15, .25), (.2, .2, .6)]
            asian, caucasian, african = races[index]
            macro.update(gender=gender,
                         age=(.19 + .012 * index) if child else (.50 + .045 * index),
                         height=.42 + .025 * index,
                         weight=.42 + .018 * index,
                         muscle=.32 if child else (.35 + .035 * index),
                         proportions=.43 + .02 * index,
                         race=dict(asian=asian, caucasian=caucasian, african=african))
            body = human.create_human(macro_detail_dict=macro)
            body.name = identity + '_body'
            # Only fully clothed source scenes are saved or rendered.
            sex = 'male' if gender else 'female'
            dominant = max(macro['race'], key=macro['race'].get)
            skin = assets.find_asset_absolute_path(f'young_{dominant}_{sex}.mhmat', asset_subdir='skins')
            if not skin:
                raise RuntimeError('Missing licensed skin')
            human.set_character_skin(skin, body, skin_type='GAMEENGINE')
            rig = human.add_builtin_rig(body, 'game_engine')
            if rig is None:
                raise RuntimeError('Missing game rig')
            rig.name = identity + '_rig'
            suit = f'male_casualsuit{(index % 6) + 1:02d}.mhclo' if gender else f'female_casualsuit{(index % 2) + 1:02d}.mhclo'
            if child:
                suit = f'{sex}_casualsuit01.mhclo'
            hair = (['short01', 'short02', 'short03', 'short04', 'afro01', 'short02', 'short03'] if gender else
                    ['ponytail01', 'bob01', 'bob02', 'braid01', 'afro01', 'long01', 'bob02'])[index] + '.mhclo'
            specification = [('clothes', suit, 'Clothes'),
                             ('clothes', f'shoes{(index % 6) + 1:02d}.mhclo', 'Clothes'),
                             ('eyes', 'low-poly.mhclo', 'Eyes'),
                             ('eyebrows', 'eyebrow001.mhclo', 'Eyebrows'),
                             ('eyelashes', 'eyelashes01.mhclo', 'Eyelashes'),
                             ('teeth', 'teeth_base.mhclo', 'Teeth'),
                             ('hair', hair, 'Hair')]
            loaded = []
            for subdir, filename, kind in specification:
                asset = assets.find_asset_absolute_path(filename, asset_subdir=subdir)
                if not asset:
                    raise RuntimeError(f'Required asset missing: {filename}')
                human.add_mhclo_asset(asset, body, asset_type=kind, material_type='GAMEENGINE')
                loaded.append(dict(file=filename, sha256=sha256(asset), kind=kind))
            root = export.create_character_copy(body, name_suffix='_export')
            export_body = objects.find_object_of_type_amongst_nearest_relatives(root, 'Basemesh')
            export.bake_modifiers_remove_helpers(export_body, bake_masks=True,
                                                 bake_subdiv=True, remove_helpers=True, also_proxy=True)
            hierarchy = [root] + objects.get_list_of_children(root)
            meshes = [obj for obj in hierarchy if obj.type == 'MESH']
            rigs = [obj for obj in hierarchy if obj.type == 'ARMATURE']
            if not rigs or not meshes:
                raise RuntimeError('Export has no mesh or skeleton')
            if not all(any(mod.type == 'ARMATURE' for mod in mesh.modifiers) for mesh in meshes):
                raise RuntimeError('Export contains an unskinned part')
            bpy.ops.object.select_all(action='DESELECT')
            for obj in hierarchy:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = root
            fbx = destination / (identity + '.fbx')
            bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True,
                                     add_leaf_bones=False, bake_anim=False,
                                     path_mode='COPY', embed_textures=True)
            glb = destination / (identity + '.glb')
            bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB',
                                      use_selection=True, export_animations=False)
            # Remove the authoring copy so the review cannot render overlapping bodies.
            keep = {obj.name for obj in hierarchy}
            for obj in list(bpy.data.objects):
                if obj.name not in keep:
                    bpy.data.objects.remove(obj, do_unlink=True)
            bpy.context.view_layer.update()
            points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
            low = min(point.z for point in points)
            high = max(point.z for point in points)
            height = high - low
            scene = bpy.context.scene
            scene.render.engine = 'CYCLES'
            scene.cycles.samples = 24
            scene.render.resolution_x = 640
            scene.render.resolution_y = 800
            scene.render.resolution_percentage = 100
            scene.world.color = (.18, .18, .18)
            bpy.ops.object.camera_add(location=(0, -height * 2.2, low + height * .55))
            camera = bpy.context.object
            camera.rotation_euler = (Vector((0, 0, low + height * .52)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            camera.data.type = 'ORTHO'
            camera.data.ortho_scale = height * 1.22
            scene.camera = camera
            for position, power, size in [((height, -height, high), 100, height),
                                          ((-height, -height * .4, high * .8), 60, height)]:
                bpy.ops.object.light_add(type='AREA', location=position)
                light = bpy.context.object
                light.data.energy = power
                light.data.shape = 'DISK'
                light.data.size = size
                light.rotation_euler = (Vector((0, 0, height * .5)) - light.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(destination / 'review.png')
            bpy.ops.wm.save_as_mainfile(filepath=str(destination / (identity + '.blend')))
            bpy.ops.render.render(write_still=True)
            record = dict(id=identity, group=group, macro=macro, assets=loaded,
                          heightMetres=height, skeletonBones=len(rigs[0].data.bones),
                          meshParts=len(meshes), fbxSha256=sha256(fbx), glbSha256=sha256(glb),
                          license='CC0-1.0', unrealImported=False, visualApproved=False)
            roster.append(record)
            (output / 'roster.json').write_text(json.dumps(dict(
                schemaVersion=1, generator='MPFB 2.0.18',
                generatorCommit='b1a2dc98776da9d1eea751b159d42cf61778fe2e',
                assetPackSha256=sha256(args.asset_pack),
                source='https://static.makehumancommunity.org/assets/assetpacks/index.html',
                requestedCount=28, generatedCount=len(roster), characters=roster,
                unrealIntegrated=False, clothingLootImplemented=False), indent=2))
            print('ANOMALIA_CLOTHED_CHARACTER_EXPORTED', identity, flush=True)


if __name__ == '__main__':
    main()
