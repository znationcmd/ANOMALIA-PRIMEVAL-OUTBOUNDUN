"""Offline regression tests for ANOMALIA official Sketchfab acquisition and UE importer."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / 'scripts' / 'ue5' / name
    spec = importlib.util.spec_from_file_location(name.removesuffix('.py'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acquire = load_script('sketchfab_acquire.py')
ue = load_script('sketchfab_import_unreal.py')


class SketchfabPipelineTests(unittest.TestCase):
    def test_catalogue_all_37_and_preserve_bmw_e39(self):
        rows = acquire.read_catalogue()
        self.assertEqual(len(rows), 37)
        self.assertTrue(any('BMW E38' in x['nom'] for x in rows))
        self.assertFalse(any('BMW E39' in x['nom'] for x in rows))
        self.assertEqual(sum(x['statut'] == 'telechargement_confirme' for x in rows), 13)
        self.assertTrue(all(x['integration'] == 'catalogue_seulement' for x in rows))
        self.assertTrue(all(x['ue_catalog_type'] for x in rows if x['groupe'] != 'Divers'))

    def test_licence_cannot_assume_commercial_rights(self):
        self.assertTrue(acquire.license_allowed({'license': {'slug': 'cc-by'}}))
        self.assertTrue(acquire.license_allowed({'license': {'slug': 'cc0'}}))
        self.assertFalse(acquire.license_allowed({'license': {'slug': 'cc-by-nc'}}))
        self.assertFalse(acquire.license_allowed({'license': {'slug': 'cc-by-nd'}}))
        self.assertFalse(acquire.license_allowed({'license': {'slug': 'cc-by-sa'}}))
        self.assertFalse(acquire.license_allowed({}))

    def test_secure_zip_extraction_rejects_traversal_and_symlinks(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            good = base / 'safe.zip'
            with zipfile.ZipFile(good, 'w') as archive:
                archive.writestr('scene.gltf', '{"asset": {"version": "2.0"}}')
            acquire.extract_safe(good, base / 'out')
            self.assertTrue((base / 'out/scene.gltf').exists())
            with self.assertRaises(FileExistsError):
                acquire.extract_safe(good, base / 'out')
            bad = base / 'bad.zip'
            with zipfile.ZipFile(bad, 'w') as archive:
                archive.writestr('../../danger', 'oops')
            with self.assertRaises(ValueError):
                acquire.extract_safe(bad, base / 'outside')
            self.assertFalse((base / 'danger').exists())

    def test_discovery_requires_receipt_and_never_imports_unverified_folder(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'bad/extrait').mkdir(parents=True)
            (root / 'bad/extrait/scene.gltf').write_text('{}')
            self.assertEqual(ue.discovered(root), [])
            good = root / ('model_' + 'a'*8)
            (good / 'extrait').mkdir(parents=True)
            (good / 'extrait/scene.gltf').write_text('{}')
            (good / 'provenance.json').write_text(json.dumps({'uid': 'a'*32}))
            result = ue.discovered(root)
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0][1].startswith('/Game/Imported/Sketchfab/'))
            self.assertTrue(ue.safe_asset_name('BMW E38 /car'))

    def test_preflight_needs_no_token_no_network(self):
        with tempfile.TemporaryDirectory() as d:
            result = acquire.main(['--catalogue', str(acquire.CATALOGUE), '--output', d])
            self.assertEqual(result, 0)
            self.assertEqual(list(Path(d).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
# end-of-script