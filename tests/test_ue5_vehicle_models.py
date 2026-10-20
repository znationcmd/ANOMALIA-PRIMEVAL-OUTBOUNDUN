"""Real source-asset and preparation checks. These do not run Unreal or prove gameplay."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'unreal/SourceAssets/Vehicles'
spec=importlib.util.spec_from_file_location('vehicle_prepare',ROOT/'scripts/ue5/prepare-vehicle-model.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)

class VehicleSourceAssetTests(unittest.TestCase):
    def setUp(self): self.item=json.loads((BASE/'manifest.json').read_text())['models'][0]
    def test_actual_glb_geometry_materials_and_licence(self):
        source=BASE/self.item['sourceFile'];data=source.read_bytes()
        self.assertEqual(len(data),self.item['bytes'])
        self.assertEqual(hashlib.sha256(data).hexdigest(),self.item['sha256'])
        d,_=prepare.load_glb(source)
        self.assertEqual(d['asset']['version'],'2.0')
        self.assertGreater(d['accessors'][d['meshes'][0]['primitives'][0]['attributes']['POSITION']]['count'],4000)
        self.assertTrue(d['materials']);self.assertTrue(d['images'])
        self.assertIn('amvlab',(source.parent/'LICENSE').read_text())
        self.assertIn('CC BY 4.0',(source.parent/'LICENSE').read_text())
    def test_preparation_is_deterministic_and_preserves_source_and_materials(self):
        source=BASE/self.item['sourceFile'];before=source.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            destination=Path(folder)/'baked.glb'
            digest=prepare.prepare(source,destination,self.item['sha256'])
            self.assertEqual(digest,self.item['preparedSha256'])
            self.assertEqual(prepare.prepare(source,destination,self.item['sha256']),digest)
            self.assertEqual(source.read_bytes(),before)
            original,_=prepare.load_glb(source);baked,_=prepare.load_glb(destination)
            self.assertEqual(original['materials'],baked['materials'])
            self.assertEqual(original['images'],baked['images'])
            self.assertEqual(baked['nodes'],[dict(mesh=0,name='ANOMALIA_airliner_baked')])
            a=baked['accessors'][0]
            dimensions=np.array(a['max'])-a['min']
            self.assertTrue(35<max(dimensions)<40) # actual aircraft metres, not miniature/raw DCC units
    def test_source_tamper_and_overwrite_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'different.glb';out.write_bytes(b'user-owned asset')
            with self.assertRaises(FileExistsError): prepare.prepare(BASE/self.item['sourceFile'],out,self.item['sha256'])
            self.assertEqual(out.read_bytes(),b'user-owned asset')
            with self.assertRaises(ValueError): prepare.prepare(BASE/self.item['sourceFile'],Path(folder)/'new.glb','0'*64)
    def test_wrong_hierarchy_is_not_silently_imported_as_one_part(self):
        with self.assertRaises(ValueError): prepare.transform(dict(nodes=[{},{}],meshes=[{}]))

if __name__=='__main__': unittest.main()
