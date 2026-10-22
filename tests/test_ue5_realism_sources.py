"""Asset import must preserve unknown files and accept only the pinned review inputs."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('realism_source_prepare',ROOT/'scripts/ue5/prepare-realism-sources.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)

class RealismSourceTests(unittest.TestCase):
    def test_registry_pins_every_download_and_license(self):
        models=json.loads((ROOT/'docs/art/realism-validation-sources.json').read_text())['models']
        self.assertEqual(len(models),7)
        self.assertEqual(len({m['id']for m in models}),7)
        for model in models:
            self.assertIn(model['license'],{'CC0-1.0','CC-BY-4.0'})
            self.assertTrue(model['author'])
            for file in model['files']:
                self.assertRegex(file['sha256'],r'^[0-9a-f]{64}$')
                self.assertGreater(file['bytes'],0)
                self.assertTrue(file['url'].startswith('https://'))

    def test_verified_cache_needs_no_network(self):
        with tempfile.TemporaryDirectory()as tmp,patch.object(prepare,'CACHE',Path(tmp)),patch.object(prepare.subprocess,'run')as run:
            target=Path(tmp)/'asset'/'source.glb';target.parent.mkdir();target.write_bytes(b'pinned')
            prepare.fetch(({'id':'asset'},{'path':'source.glb','bytes':6,'sha256':hashlib.sha256(b'pinned').hexdigest()}))
            run.assert_not_called();self.assertEqual(target.read_bytes(),b'pinned')

    def test_changed_cache_is_preserved_and_not_redownloaded(self):
        with tempfile.TemporaryDirectory()as tmp,patch.object(prepare,'CACHE',Path(tmp)),patch.object(prepare.subprocess,'run')as run:
            target=Path(tmp)/'asset'/'source.glb';target.parent.mkdir();target.write_bytes(b'artist edit')
            with self.assertRaises(ValueError):prepare.fetch(({'id':'asset'},{'path':'source.glb','bytes':6,'sha256':hashlib.sha256(b'pinned').hexdigest()}))
            run.assert_not_called();self.assertEqual(target.read_bytes(),b'artist edit')

    def test_source_paths_cannot_escape_the_owned_cache(self):
        with tempfile.TemporaryDirectory()as tmp,patch.object(prepare,'CACHE',Path(tmp)),patch.object(prepare.subprocess,'run')as run:
            with self.assertRaises(ValueError):prepare.fetch(({'id':'asset'},{'path':'../../outside.glb'}))
            run.assert_not_called()

if __name__=='__main__':unittest.main()
