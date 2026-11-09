"""Contract checks: catalog data is valid; geometry and preservation rules are explicit."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ue5" / "worldgen" / "validate_world_catalog.py"
SPEC = ROOT / "docs" / "ANOMALIA_WORLDGEN_MULTI_MAPS_SPEC.md"
spec = importlib.util.spec_from_file_location("worldgen_validator", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class WorldgenCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads(module.CATALOG_PATH.read_text(encoding="utf-8"))

    def test_catalog_contains_twenty_maps(self):
        result = module.validate_catalog(self.catalog)
        self.assertEqual(result["worldCount"], 20)
        self.assertEqual(result["totalAreaKm2"], 24340.18)
        self.assertIn("CHERNASKALUXRIA", result["mapsWithoutConfirmedDimensions"])

    def test_racconia_seed_and_two_meanings_of_65_percent(self):
        world = next(w for w in self.catalog["worlds"] if w["id"] == "racconia-varkovia")
        self.assertEqual(world["seed"], "ANOMALIA-2026")
        self.assertEqual(world["placementDensity"], .65)
        self.assertEqual(world["landFraction"], .65)
        self.assertEqual(world["seaFraction"], .35)

    def test_mismatched_dimensions_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["worlds"][-1]["widthKm"] = 15
        with self.assertRaisesRegex(ValueError, "Dimensions"):
            module.validate_catalog(catalog)

    def test_duplicate_ids_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["worlds"][-1]["id"] = catalog["worlds"][0]["id"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.validate_catalog(catalog)

    def test_incomplete_fraction_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["worlds"][-1]["seaFraction"] = None
        with self.assertRaisesRegex(ValueError, "Land/sea"):
            module.validate_catalog(catalog)

    def test_spec_requires_non_destructive_generation(self):
        text = SPEC.read_text(encoding="utf-8")
        for keyword in ("--dry-run", "protected-actors", "World Partition", "PCG", "RACCONIA-VARKOVIA"):
            self.assertIn(keyword, text)


if __name__ == "__main__":
    unittest.main()
