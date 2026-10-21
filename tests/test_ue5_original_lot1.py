"""Check published GLB bytes before an expensive native import."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

BASE = Path(__file__).resolve().parents[1] / 'unreal/SourceAssets/OriginalLot1'


class OriginalLotTests(unittest.TestCase):
    def test_manifest_matches_all_eight_published_models(self):
        models = json.loads((BASE / 'manifest.json').read_text())['models']
        self.assertEqual(len(models), 8)
        self.assertEqual(len({m['id'] for m in models}), 8)
        for item in models:
            with self.subTest(model=item['id']):
                source = (BASE / item['file']).resolve()
                self.assertEqual(source.parent, BASE.resolve())
                data = source.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])
                self.assertEqual(len(data), item['bytes'])
                self.assertEqual(struct.unpack_from('<III', data), (0x46546C67, 2, len(data)))
                length, kind = struct.unpack_from('<II', data, 12)
                self.assertEqual(kind, 0x4E4F534A)
                gltf = json.loads(data[20:20 + length])
                primitives = gltf['meshes'][0]['primitives']
                positions = [gltf['accessors'][p['attributes']['POSITION']] for p in primitives]
                for axis, expected in enumerate(item['dimensionsMetresYUp']):
                    actual = max(p['max'][axis] for p in positions) - min(p['min'][axis] for p in positions)
                    self.assertAlmostEqual(actual, expected, places=5)
                self.assertEqual(sum(gltf['accessors'][p['indices']]['count'] // 3 for p in primitives), item['triangles'])
                self.assertTrue(all('pbrMetallicRoughness' in gltf['materials'][p['material']] for p in primitives))


if __name__ == '__main__':
    unittest.main()
