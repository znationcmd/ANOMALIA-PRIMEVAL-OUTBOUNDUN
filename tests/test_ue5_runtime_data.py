"""Exercise actual runtime staging and ownership safeguards; these are not Unreal tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stage_runtime', ROOT / 'scripts/ue5/stage-runtime-data.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RuntimeDataTests(unittest.TestCase):
    def fixture(self, root):
        config = root / 'public/config'
        config.mkdir(parents=True)
        for name in module.FILES:
            (config / name).write_bytes((ROOT / 'public/config' / name).read_bytes())

    def test_stage_actual_catalogue_preserve_server_overrides_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            server = root / 'unreal/Saved/Servers/test/loot_items_catalog.json'
            server.parent.mkdir(parents=True)
            server.write_text('user configuration remains untouched')
            self.assertEqual(module.stage(root), 3)
            self.assertEqual(module.stage(root), 3)
            staged = root / 'unreal/Content/Anomalia/Data/loot_items_catalog.json'
            self.assertEqual(len(json.loads(staged.read_text())['items']), 232)
            self.assertEqual(server.read_text(), 'user configuration remains untouched')
            self.assertEqual(staged.read_bytes(), (root / 'public/config/loot_items_catalog.json').read_bytes())

    def test_owned_defaults_update_but_artist_or_user_edits_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            module.stage(root)
            source = root / 'public/config/loot_spawns.json'
            doc = json.loads(source.read_text())
            doc['description'] = 'updated owned default'
            source.write_text(json.dumps(doc))
            module.stage(root)
            staged = root / 'unreal/Content/Anomalia/Data/loot_spawns.json'
            self.assertEqual(staged.read_bytes(), source.read_bytes())
            staged.write_text('a manual local edit')
            with self.assertRaisesRegex(ValueError, 'Preserving edited or unowned'):
                module.stage(root)
            self.assertEqual(staged.read_text(), 'a manual local edit')

    def test_invalid_input_rejects_whole_batch_without_partial_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            module.stage(root)
            staged = root / 'unreal/Content/Anomalia/Data/loot_items_catalog.json'
            before = staged.read_bytes()
            source = root / 'public/config/loot_items_catalog.json'
            source.write_text(source.read_text()+'\n')
            (root / 'public/config/loot_spawns.json').write_text('{broken')
            with self.assertRaises(ValueError):
                module.stage(root)
            self.assertEqual(staged.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
