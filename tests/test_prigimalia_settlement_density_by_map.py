"""No other world falsely inherits SKARVIK's 125 urban localities."""
import json
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/"public/config"
class LocalityDensityByMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((BASE/"prigimalia-settlement-density-by-map.json").read_text("utf-8"))
        cls.catalog=json.loads((BASE/"anomalia-map-catalog.json").read_text("utf-8"))
    def test_every_known_map_has_specific_density(self):
        catalog={x["id"]:x for x in self.catalog["maps"]}
        target={x["mapId"]:x for x in self.config["maps"]}
        self.assertEqual(set(target),set(catalog))
        for k,plan in target.items():
            with self.subTest(map=k):
                self.assertEqual(plan["sizeKm"],[catalog[k]["widthKm"],catalog[k]["heightKm"]])
                self.assertEqual(plan["total"],sum(plan[x] for x in ["majorCities","smallTowns","towns","villages"]))
                self.assertGreater(plan["villages"],plan["majorCities"])
                self.assertLess(plan["total"],126)
                self.assertIn("planning",plan["status"].lower()) if k!="archipelago-v2" else None
    def test_skarvik_stays_125_and_all_others_are_sparser(self):
        maps={m["name"]:m for m in self.config["maps"]}
        self.assertEqual(maps["SKARVIK"]["total"],125)
        self.assertEqual(len(maps),6)
        self.assertTrue(all(m["total"]<125 for k,m in maps.items() if k!="SKARVIK"))
        self.assertEqual(sum(m["total"] for m in maps.values()),295)
        self.assertTrue(self.config["constructionGuards"]["gradeFoundationPadsWithSmoothBlends"])
        self.assertTrue(self.config["constructionGuards"]["doNotModifyOriginalD"])
        self.assertEqual(self.config["designStatus"],"PLANNING_ONLY_NOT_NATIVE_POPULATED")

if __name__=="__main__":
    unittest.main()
