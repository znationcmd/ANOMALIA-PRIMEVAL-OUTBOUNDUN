"""Test exported geometry, not Unreal runtime claims."""
import importlib.util,json,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('road_mesh',ROOT/'unreal/Scripts/road_mesh.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class RoadMeshTests(unittest.TestCase):
    def test_terrain_deformation_and_bridge_connection(self):
        source=(ROOT/'unreal/SourceAssets/Infrastructure/Bridge/bridge50m.glb').read_bytes()
        data,origin=module.build_road(lambda x,y: .02*x,13000,13500,13500,270.25,source)
        magic,version,size=struct.unpack_from('<III',data);self.assertEqual((magic,version,size),(0x46546c67,2,len(data)))
        n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:]
        self.assertEqual(len(doc['meshes'][0]['primitives']),3)
        road=doc['meshes'][0]['primitives'][0];acc=doc['accessors'][road['attributes']['POSITION']];view=doc['bufferViews'][acc['bufferView']]
        values=struct.unpack_from('<'+'f'*(acc['count']*3),binary,view['byteOffset'])
        self.assertEqual(acc['count'],202);self.assertAlmostEqual(values[-5]+origin[1],270.25,places=4)
        self.assertAlmostEqual(values[1]+origin[1],260.30,places=4)
        self.assertEqual(acc['max'][0]-acc['min'][0],500)
        self.assertEqual(len(doc['images']),2)
        for old,new in zip(json.loads(source[20:20+struct.unpack_from('<I',source,12)[0]])['images'],doc['images']):
            self.assertEqual(new['mimeType'],old['mimeType'])
