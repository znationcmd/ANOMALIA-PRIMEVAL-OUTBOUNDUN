"""Validate metro boarding apertures and catalogue source coverage before native import."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('metro',ROOT/'scripts/ue5/generate-metro.py')
metro=importlib.util.module_from_spec(spec);spec.loader.exec_module(metro)

class MetroGeometry(unittest.TestCase):
    def test_both_assembled_meshes_and_preserved_edits(self):
        with tempfile.TemporaryDirectory() as path:
            manifest=metro.generate(path)
            self.assertEqual({m['id'] for m in manifest['models']},{'metro','metro_wagon'})
            for item in manifest['models']:
                data=(Path(path)/item['file']).read_bytes()
                self.assertEqual(struct.unpack_from('<III',data),(0x46546c67,2,len(data)))
                size=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+size])
                self.assertEqual(len(g['meshes']),1)
                self.assertGreater(item['triangles'],1000)
                self.assertAlmostEqual(item['dimensionsMetresYUp'][0],18.5)
            edited=Path(path)/'metro_wagon.glb';edited.write_bytes(b'artist revision')
            with self.assertRaisesRegex(RuntimeError,'preserved'):metro.generate(path)
