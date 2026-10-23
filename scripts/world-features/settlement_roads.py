"""Original town street meshes in metres, with terrain and house clearance checks."""
import json
import math
import struct

class Geometry:
    def __init__(self):
        self.groups = [dict(positions=[], normals=[], uv=[], indices=[]) for _ in range(3)]

    def quad(self, points, material, normal=(0, 1, 0)):
        group = self.groups[material]; start = len(group['positions']) // 3
        for x, y, z in points:
            group['positions'].extend((x, y, z)); group['normals'].extend(normal)
            group['uv'].extend((x / 3, z / 3))
        group['indices'].extend((start, start + 2, start + 1, start + 1, start + 2, start + 3))

    def glb(self, name):
        binary = bytearray(); views = []; accessors = []; primitives = []
        def accessor(values, kind, components, type_name, target):
            while len(binary) % 4: binary.append(0)
            offset = len(binary)
            binary.extend(struct.pack('<' + ('I' if kind == 5125 else 'f') * len(values), *values))
            views.append(dict(buffer=0, byteOffset=offset, byteLength=len(binary) - offset, target=target))
            entry = dict(bufferView=len(views) - 1, componentType=kind, count=len(values) // components, type=type_name)
            if type_name == 'VEC3' and target == 34962:
                entry['min'] = [min(values[i::3]) for i in range(3)]
                entry['max'] = [max(values[i::3]) for i in range(3)]
            accessors.append(entry); return len(accessors) - 1
        for material, group in enumerate(self.groups):
            if not group['indices']: continue
            primitives.append(dict(attributes=dict(
                POSITION=accessor(group['positions'], 5126, 3, 'VEC3', 34962),
                NORMAL=accessor(group['normals'], 5126, 3, 'VEC3', 34962),
                TEXCOORD_0=accessor(group['uv'], 5126, 2, 'VEC2', 34962)),
                indices=accessor(group['indices'], 5125, 1, 'SCALAR', 34963), material=material))
        doc = dict(asset=dict(version='2.0', generator='ANOMALIA original settlement road authoring'),
                   scene=0, scenes=[dict(nodes=[0])], nodes=[dict(name=name, mesh=0)],
                   meshes=[dict(name=name, primitives=primitives)],
                   materials=[dict(name=n, pbrMetallicRoughness=dict(baseColorFactor=c, metallicFactor=0, roughnessFactor=.85))
                              for n, c in [('Asphalt', [.08, .08, .08, 1]), ('Paint', [.8, .78, .7, 1]), ('Curb', [.43, .43, .4, 1])]],
                   buffers=[dict(byteLength=len(binary))], bufferViews=views, accessors=accessors)
        header = json.dumps(doc, separators=(',', ':')).encode()
        header += b' ' * (-len(header) % 4); binary += b'\0' * (-len(binary) % 4)
        return (struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(header) + 8 + len(binary))
                + struct.pack('<II', len(header), 0x4E4F534A) + header
                + struct.pack('<II', len(binary), 0x004E4942) + binary)

def build_streets(site, buildings, surface, envelope):
    """Return local Y-up street geometry; no terrain edits, bridges or trunk routes."""
    e0, n0 = site['east'], site['north']; origin, _ = surface(e0, n0)
    buildings = [b for b in buildings if abs(b['east'] - e0) < 500 and abs(b['north'] - n0) < 500]
    geometry = Geometry(); valid = {}; edges = []
    def clear(x, z, width, depth):
        e, n = e0 + x, n0 + z
        if any(abs(e - b['east']) < (width + b['width']) / 2 + 2 and
               abs(n - b['north']) < (depth + b['depth']) / 2 + 2 for b in buildings):
            return False
        low, high = envelope(surface, e, n, width, depth)
        return low >= 5 and high - low <= .12
    for z in range(-350, 351, 50):
        for x in range(-350, 351, 50):
            valid[(x, z)] = clear(x, z, 8.5, 8.5)
    for (x, z), good in valid.items():
        if not good: continue
        for dx, dz in ((50, 0), (0, 50)):
            if valid.get((x + dx, z + dz)) and clear(x + dx / 2, z + dz / 2, 42.5 if dx else 8.5, 8.5 if dx else 42.5):
                edges.append((x, z, dx, dz))
    used = {(x, z) for x, z, _, _ in edges} | {(x + dx, z + dz) for x, z, dx, dz in edges}
    def point(x, z, lift=.025):
        h, error = surface(e0 + x, n0 + z)
        return x, h + error - origin + lift, z
    def paving(x0, z0, x1, z1, material=0, lift=.025):
        geometry.quad([point(x0, z0, lift), point(x1, z0, lift), point(x0, z1, lift), point(x1, z1, lift)], material)
    def curb(x0, z0, x1, z1):
        low = [point(x0, z0), point(x1, z0), point(x0, z1), point(x1, z1)]
        high = [(x, y + .13, z) for x, y, z in low]
        geometry.quad(high, 2)
        # Narrow curb sides use independent normals, preserving hard concrete edges.
        for a, b, normal in [(0, 1, (0, 0, -1)), (3, 2, (0, 0, 1)), (2, 0, (-1, 0, 0)), (1, 3, (1, 0, 0))]:
            geometry.quad([low[a], low[b], high[a], high[b]], 2, normal)
    for x, z in sorted(used): paving(x - 4, z - 4, x + 4, z + 4)
    for x, z, dx, dz in edges:
        if dx:
            paving(x + 4, z - 4, x + 46, z + 4)
            for side in (-1, 1):
                a, b = sorted((z + side * 4, z + side * 4.25)); curb(x + 4, a, x + 46, b)
            for offset in range(8, 44, 8): paving(x + offset, z - .06, x + offset + 3, z + .06, 1, .029)
        else:
            paving(x - 4, z + 4, x + 4, z + 46)
            for side in (-1, 1):
                a, b = sorted((x + side * 4, x + side * 4.25)); curb(a, z + 4, b, z + 46)
            for offset in range(8, 44, 8): paving(x - .06, z + offset, x + .06, z + offset + 3, 1, .029)
    return dict(geometry=geometry, originHeight=origin, junctions=len(used), segments=len(edges),
                centrelineMetres=len(edges) * 50, terrainModified=False, intercityConnected=False)
