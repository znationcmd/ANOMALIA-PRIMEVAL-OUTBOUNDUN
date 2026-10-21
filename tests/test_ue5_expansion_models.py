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

    def test_building_entrances_floors_and_upper_landings(self):
        # Segment/triangle intersections against the exported GLB, not builder boxes.
        def hit(a,b,triangle):
            direction=MODULE.sub(b,a);v0,v1,v2=triangle
            e1,e2=MODULE.sub(v1,v0),MODULE.sub(v2,v0)
            p=MODULE.cross(direction,e2);det=sum(x*y for x,y in zip(e1,p))
            if abs(det)<1e-9:return False
            tvec=MODULE.sub(a,v0);u=sum(x*y for x,y in zip(tvec,p))/det
            if u<0 or u>1:return False
            q=MODULE.cross(tvec,e1);v=sum(x*y for x,y in zip(direction,q))/det
            if v<0 or u+v>1:return False
            t=sum(x*y for x,y in zip(e2,q))/det
            return 0<=t<=1
        for name in MODULE.BUILDINGS:
            with self.subTest(building=name):
                data=(self.base/(name+'.glb')).read_bytes();length=struct.unpack_from('<I',data,12)[0]
                doc=json.loads(data[20:20+length]);binary=data[28+length:];triangles=[]
                for primitive in doc['meshes'][0]['primitives']:
                    acc=doc['accessors'][primitive['attributes']['POSITION']];view=doc['bufferViews'][acc['bufferView']]
                    values=struct.unpack_from('<'+'f'*(acc['count']*3),binary,view['byteOffset'])
                    vertices=[values[i:i+3] for i in range(0,len(values),3)]
                    acc=doc['accessors'][primitive['indices']];view=doc['bufferViews'][acc['bufferView']]
                    indices=struct.unpack_from('<'+'I'*acc['count'],binary,view['byteOffset'])
                    triangles.extend(tuple(vertices[j] for j in indices[i:i+3]) for i in range(0,len(indices),3))
                # Building front is negative local Z, independent of Unreal axis conversion.
                depth=12 if name=='residence_4floors' else (14 if name in ['hospital','fire_station'] else 9)
                a,b=(0,1.2,-depth/2-1),(0,1.2,-depth/2+1)
                self.assertFalse(any(hit(a,b,t) for t in triangles),'Entrance is sealed')
                a,b=(3,1.2,-depth/2-1),(3,1.2,-depth/2+1)
                self.assertTrue(any(hit(a,b,t) for t in triangles),'Adjacent wall missing')
                self.assertTrue(any(hit((0,1,0),(0,-.4,0),t) for t in triangles),'Ground floor missing')
                if name in ['residence_4floors','townhouse','hospital','police_station']:
                    self.assertTrue(any(hit((0,3.2,-1.2),(0,2.7,-1.2),t) for t in triangles),'Upper stair landing disconnected')

    def test_repeat_is_identical_and_modified_art_is_preserved(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.base.iterdir()}
        MODULE.generate(self.base)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.base.iterdir()})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'transport_truck.glb';path.write_bytes(b'user art')
            with self.assertRaisesRegex(RuntimeError,'Existing art preserved'):MODULE.generate(folder)
            self.assertEqual(path.read_bytes(),b'user art')


if __name__=='__main__':unittest.main()
