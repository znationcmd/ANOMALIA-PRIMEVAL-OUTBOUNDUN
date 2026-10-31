"""All 11 ANOMALIA'Z worlds need distinct provisional settlement densities.
The public technical Unreal map catalogue currently covers only 6 of them.
"""
import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]/"public/config"
EXPECTED = {
    "SKARVIK", "DRAZOVIA", "KARSKOV", "VORGRAD", "NEMORIS",
    "DRAKHEIM", "SOLYNACALYRA", "NEXAVARKHOS", "CHERNASKALUXRIA",
    "F.A.L.C", "KOLCHIEM ORIGINS",
}


class LocalityDensityByMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (BASE/"prigimalia-settlement-density-by-map.json").read_text("utf-8")
        )
        cls.catalog = json.loads(
            (BASE/"anomalia-map-catalog.json").read_text("utf-8")
        )

    def test_all_eleven_worlds_are_accounted_for(self):
        maps = self.config["maps"]
        self.assertEqual(len(maps), 11)
        self.assertEqual({m["name"] for m in maps}, EXPECTED)
        self.assertEqual(len({m["mapId"] for m in maps}), 11)
        self.assertEqual(self.config["scope"]["targetMapCount"], 11)
        self.assertTrue(self.config["scope"]["technicalCatalogNotExhaustive"])

    def test_existing_six_runtime_map_dimensions_unchanged(self):
        targets = {m["mapId"]: m for m in self.config["maps"]}
        for technical in self.catalog["maps"]:
            with self.subTest(map=technical["displayName"]):
                plan = targets[technical["id"]]
                self.assertEqual(plan["name"], technical["displayName"])
                self.assertEqual(plan["sizeKm"], [
                    technical["widthKm"], technical["heightKm"]
                ])
        self.assertEqual(len(self.catalog["maps"]), 6)

    def test_known_dimensions_and_no_fabricated_unknown_sizes(self):
        targets = {m["name"]: m for m in self.config["maps"]}
        self.assertEqual(targets["CHERNASKALUXRIA"]["sizeKm"], [100,100])
        self.assertEqual(targets["F.A.L.C"]["sizeKm"], [26.5,26.5])
        for missing in ["SOLYNACALYRA", "NEXAVARKHOS", "KOLCHIEM ORIGINS"]:
            self.assertIsNone(targets[missing]["sizeKm"])

    def test_all_locality_targets_are_consistent_and_only_planned(self):
        maps = self.config["maps"]
        for plan in maps:
            with self.subTest(map=plan["name"]):
                self.assertEqual(plan["total"], sum(plan[k] for k in [
                    "majorCities", "smallTowns", "towns", "villages"
                ]))
                self.assertGreater(plan["villages"], plan["majorCities"])
        self.assertEqual(next(m["total"] for m in maps if m["name"] == "SKARVIK"), 125)
        self.assertTrue(all(m["total"] < 125 for m in maps if m["name"] != "SKARVIK"))
        self.assertEqual(sum(m["total"] for m in maps), 468)
        self.assertTrue(self.config["constructionGuards"]["doNotModifyOriginalD"])
        self.assertTrue(self.config["constructionGuards"]["gradeFoundationPadsWithSmoothBlends"])
        self.assertEqual(
            self.config["designStatus"],
            "ALL_11_WORLDS_PLANNED_NATIVE_SETTLEMENT_POPULATION_INCOMPLETE"
        )


if __name__ == "__main__":
    unittest.main()
