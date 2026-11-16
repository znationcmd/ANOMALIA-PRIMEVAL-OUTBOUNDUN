"""Non-Unreal reproducibility and safety tests for VALHALLA EXTINCTION."""
import importlib.util
import json
import math
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('valhalla_generator',BASE/'scripts'/'ue5'/'worldgen'/'generate_valhalla_extinction.py')
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
spec2=importlib.util.spec_from_file_location('valhalla_stage',BASE/'unreal'/'EditorPython'/'stage_valhalla_extinction_world.py')
stage=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(stage)


class ValhallaWorldTests(unittest.TestCase):
    def test_exact_ue_dimensions_and_terrain_encoding(self):
        self.assertEqual(gen.SAMPLES,2017)
        self.assertEqual(gen.COUNT*(gen.TILE_SAMPLES-1)+1,gen.SAMPLES)
        self.assertAlmostEqual((gen.SAMPLES-1)*gen.X_SCALE_CM/100,24000,places=5)
        self.assertEqual(int(gen.height_as_u16(0)),32768)
        self.assertEqual(int(gen.height_as_u16(100)),34368)
        self.assertLess(gen.elevation_at(12000,12000),0)
        self.assertGreater(gen.elevation_at(-6000,5100),300)

    def test_original_viking_zombie_layout(self):
        layout=gen.build_layout()
        self.assertEqual(layout['name'],'VALHALLA EXTINCTION')
        self.assertEqual(layout['dimensionsKm'],[24,24])
        self.assertEqual(len(layout['villages']),12)
        self.assertGreaterEqual(len(layout['runeShrines']),4)
        self.assertEqual(len(layout['draugrSpawnCandidates']),168)
        self.assertEqual(len({x['id'] for x in layout['villages']}),12)
        self.assertTrue(all(abs(x['xMeters'])<12000 and abs(x['yMeters'])<12000 for x in layout['villages']))
        self.assertEqual({x['id'] for x in layout['zombieArchetypes']},
            {'draugr-thrall','draugr-huskarl','draugr-berserker','draugr-shieldmaiden','draugr-seidr'})
        self.assertFalse(layout['gameplayReady'])

    def test_staging_dryrun_and_missing_assets(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            layout=Path(td)/'layout.json'
            layout.write_text(json.dumps(gen.build_layout()),encoding='utf-8')
            a=stage.check_layout(layout)
            self.assertEqual(len(a['villages']),12)
            result=stage.create_level(layout)
            self.assertTrue(result['dryRun'])
            self.assertFalse(result['landscapeImported'])
            b=Path(td)/'bindings.json';b.write_text('{}',encoding='utf-8')
            r=stage.place_real_assets(layout,b)
            self.assertFalse(r['ready'])
            self.assertIn('longhouse',r['missingAssetBindings'])

if __name__=='__main__': unittest.main()