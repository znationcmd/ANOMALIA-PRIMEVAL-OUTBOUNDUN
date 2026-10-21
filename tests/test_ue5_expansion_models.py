"""Exercise actual generated geometry and native catalogue coverage, without Unreal."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('expansion',ROOT/'scripts/ue5/generate-assets-expansion.py')
MODULE=importlib.util.module_from_spec(spec);spec.loader.exec_module(MODULE)


class ExpansionGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name)
        cls.manifest=MODULE.generate(cls.base)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_complete_generic_native_catalogue_coverage(self):
        text=(ROOT/'unreal/Source/AnomaliaPrimeval/AnomaliaVehicleCatalog.cpp').read_text()
        ids=set(re.findall(r'MakeVehicle\(TEXT\("([a-z0-9_]+)"\)',text))
        self.assertEqual(set(MODULE.VEHICLES)|{'quad','snowmobile','jetski','zodiac','airliner'},ids)
        self.assertEqual(len(self.manifest['models']),33)
        self.assertEqual(len({m['objectPath'] for m in self.manifest['models']}),33)

    def test_glb_structure_geometry_normals_and_indices(self):
        for model in self.manifest['models']:
            with self.subTest(model=model['id']):
                data=(self.base/model['file']).read_bytes()
                self.assertEqual(len(data),model['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),model['sha256'])
                self.assertEqual(struct.unpack_from('<III',data),(0x46546C67,2,len(data)))
                length,kind=struct.unpack_from('<II',data,12);self.assertEqual(kind,0x4E4F534A)
                gltf=json.loads(data[20:20+length]);binary_length,binary_kind=struct.unpack_from('<II',data,20+length)
                self.assertEqual(binary_kind,0x004E4942);binary=data[28+length:]
                self.assertEqual(len(binary),binary_length)
                self.assertEqual(gltf['buffers'][0]['byteLength'],binary_length)
                triangles=0;positions=[]
                for primitive in gltf['meshes'][0]['primitives']:
                    count=gltf['accessors'][primitive['attributes']['POSITION']]['count']
                    positions.append(gltf['accessors'][primitive['attributes']['POSITION']])
                    for attr in ['POSITION','NORMAL']:
                        acc=gltf['accessors'][primitive['attributes'][attr]];view=gltf['bufferViews'][acc['bufferView']]
                        self.assertLessEqual(view['byteOffset']+view['byteLength'],len(binary))
                        values=struct.unpack_from('<'+'f'*(acc['count']*3),binary,view['byteOffset'])
                        self.assertTrue(all(math.isfinite(v) for v in values))
                        if attr=='NORMAL':
                            self.assertTrue(all(abs(sum(v*v for v in values[i:i+3])-1)<1e-5 for i in range(0,len(values),3)))
                    acc=gltf['accessors'][primitive['indices']];view=gltf['bufferViews'][acc['bufferView']]
                    self.assertEqual(acc['count']%3,0)
                    values=struct.unpack_from('<'+'I'*acc['count'],binary,view['byteOffset'])
                    self.assertLess(max(values),count);triangles+=acc['count']//3
                self.assertEqual(triangles,model['triangles'])
                for axis,dimension in enumerate(model['dimensionsMetresYUp']):
                    self.assertGreater(dimension,.1)
                    self.assertAlmostEqual(max(a['max'][axis] for a in positions)-min(a['min'][axis] for a in positions),dimension)
                self.assertFalse(model['drivingTested']);self.assertFalse(model['manufacturerReplica'])

    def test_repeat_is_identical_and_modified_art_is_preserved(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.base.iterdir()}
        MODULE.generate(self.base)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.base.iterdir()})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'transport_truck.glb';path.write_bytes(b'user art')
            with self.assertRaisesRegex(RuntimeError,'Existing art preserved'):MODULE.generate(folder)
            self.assertEqual(path.read_bytes(),b'user art')


if __name__=='__main__':unittest.main()
