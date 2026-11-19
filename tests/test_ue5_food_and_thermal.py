import json
import pathlib
import shutil
import subprocess
import unittest
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

class FoodAndThermalTests(unittest.TestCase):
    def test_all_food_catalog_entries_have_real_consumption_rules(self):
        count = 0
        for name in ('loot_items_catalog.json', 'rp_items_catalog.json'):
            data = json.loads((ROOT / 'public/config' / name).read_text(encoding='utf-8'))
            for item in data['items']:
                if item.get('category') not in {'canned_food', 'fresh_food'}:
                    continue
                rule = item.get('use', {})
                assert rule.get('action') == 'eat', item['id']
                assert 0 < rule.get('hunger', 0) <= 100, item['id']
                count += 1
        assert count >= 26

    def test_freezing_thawing_and_exposure_regressions(self):
        compiler = shutil.which('g++') or shutil.which('clang++')
        if not compiler:
            self.skipTest('A C++17 compiler is needed for thermal core regression execution')
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        binary = pathlib.Path(temporary.name) / 'thermal-regression'
        subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', str(ROOT / 'tests/thermal_model_regression.cpp'), '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)], check=True, capture_output=True, text=True)
        assert '12 thermal regression scenarios passed' in result.stdout

if __name__ == "__main__":
    unittest.main()
