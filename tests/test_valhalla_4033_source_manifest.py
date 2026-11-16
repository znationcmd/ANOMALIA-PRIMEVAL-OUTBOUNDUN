"""Valhalla source metadata and UE5 staging preflight; never claims a playable level."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'config'/'worldgen'/'valhalla-extinction-source-manifest.json'
EXPANSION=ROOT/'config'/'worldgen'/'expansion-worlds.json'
STAGE=ROOT/'unreal'/'EditorPython'/'stage_valhalla_extinction_4033.py'

class Valhalla4033Tests(unittest.TestCase):
    def test_source_manifest(self):
        m=json.loads(MANIFEST.read_text(encoding='utf-8'))
        self.assertEqual(m['map'],'VALHALLA EXTINCTION')
        self.assertEqual(m['size_km'],[24,24])
        self.assertEqual(m['landscape_resolution'],[4033,4033])
        self.assertEqual(m['settlements'],28)
        self.assertEqual(m['architecture_placements'],555)
        self.assertEqual(m['draugr_spawns'],374)
        self.assertEqual(m['road_links'],67)
        self.assertTrue(m['verifiedZipCRC'])
        self.assertTrue(m['png16MatchesR16Bytes'])
        self.assertFalse(m['nativeUEMapCompiled'])
        self.assertFalse(m['playableBuildTested'])
        self.assertEqual(len(m['archiveSha256']),64)

    def test_catalog_adds_one_world_without_changing_twenty_originals(self):
        e=json.loads(EXPANSION.read_text(encoding='utf-8'))
        self.assertEqual([x['order'] for x in e['worlds']],[21,22,23,24])
        v=e['worlds'][-1]
        self.assertEqual(v['id'],'valhalla-extinction')
        self.assertEqual(v['widthKm']*v['heightKm'],576)
        self.assertEqual(e['combinedAreaKm2'],26441.18)

    def test_staging_script_preflight_rejects_bad_archive_without_unreal(self):
        spec=importlib.util.spec_from_file_location('valhalla_stage',STAGE)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'invalid.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('unrelated.txt','test')
            with self.assertRaisesRegex(ValueError,'Incomplete Valhalla'):
                m.create_level(p)
        self.assertEqual(m.ASSET,'/Game/Maps/VALHALLA_EXTINCTION')

if __name__=='__main__':unittest.main()
