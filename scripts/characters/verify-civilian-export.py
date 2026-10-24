"""Blender round-trip review: export geometry, skinning, and texture presence."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    root = Path(args.root).resolve()
    roster = json.loads((root / 'roster.json').read_text())
    assert roster['generatedCount'] == 28
    assert len({item['glbSha256'] for item in roster['characters']}) == 28
    assert all(sum(item['group'] == group for item in roster['characters']) == 7
               for group in ('man', 'woman', 'boy', 'girl'))
    results = []
    # Check each actual GLB, then a representative FBX of each age/gender group.
    cases = [(item, 'glb') for item in roster['characters']]
    cases += [(next(item for item in roster['characters'] if item['group'] == group), 'fbx')
              for group in ('man', 'woman', 'boy', 'girl')]
    for item, extension in cases:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        source = root / item['id'] / (item['id'] + '.' + extension)
        if extension == 'glb':
            bpy.ops.import_scene.gltf(filepath=str(source))
        else:
            bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
        # glTF's Blender importer can create an unskinned Icosphere bone display
        # object. It is not part of the exported character geometry.
        rigs = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE'
                and obj.name.startswith(item['id'])]
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH'
                  and obj.name.startswith(item['id'])]
        assert len(rigs) == 1 and len(meshes) >= 8, (item['id'], extension)
        rig = rigs[0]
        assert len(rig.data.bones) >= 53
        assert 'upperarm_l' in rig.pose.bones
        images = {node.image for mesh in meshes for slot in mesh.material_slots
                  if slot.material and slot.material.use_nodes
                  for node in slot.material.node_tree.nodes
                  if node.type == 'TEX_IMAGE' and node.image}
        assert len(images) >= 7
        assert all(image.size[0] > 0 for image in images)
        assert all(any(mod.type == 'ARMATURE' and mod.object == rig
                       for mod in mesh.modifiers) for mesh in meshes)
        bpy.context.view_layer.update()
        points = [mesh.matrix_world @ Vector(corner) for mesh in meshes for corner in mesh.bound_box]
        height = max(point.z for point in points) - min(point.z for point in points)
        assert abs(height - item['heightMetres']) < .025, (item['id'], height)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        def positions():
            return [[vertex.co.copy() for vertex in mesh.evaluated_get(depsgraph).data.vertices]
                    for mesh in meshes]
        before = positions()
        bone = rig.pose.bones['upperarm_l']
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler.x = .4
        bpy.context.view_layer.update()
        after = positions()
        maximum_motion = max((a - b).length for left, right in zip(before, after)
                             for a, b in zip(left, right))
        assert maximum_motion > .01, (item['id'], 'Skin does not deform')
        results.append(dict(id=item['id'], format=extension,
                            heightMetres=height, bones=len(rig.data.bones),
                            meshParts=len(meshes), textures=len(images),
                            maximumJointDeformation=maximum_motion, passed=True))
        print('ANOMALIA_CIVILIAN_ROUNDTRIP_PASSED', item['id'], extension, flush=True)
    (root / 'roundtrip-validation.json').write_text(json.dumps(dict(
        allPassed=True, checks=results, unrealTested=False,
        visualQualityApproved=False, animationsIncluded=False), indent=2))


if __name__ == '__main__':
    main()
