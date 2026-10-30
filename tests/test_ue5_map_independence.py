"""Guard the six separate worlds and deterministic new-world population plans.

These tests are offline simulations; they do not certify native UE gameplay.
"""
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def load_module(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SixIndependentWorldsTest(unittest.TestCase):
    def test_stable_independent_packages_and_save_namespaces(self):
        rows=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text(encoding="utf-8"))["maps"]
        self.assertEqual(len(rows),6)
        self.assertEqual(len({r["id"] for r in rows}),6)
        self.assertEqual(len({r["originalUnrealPackage"] for r in rows}),6)
        self.assertEqual(len({r["saveNamespace"] for r in rows}),6)
        self.assertTrue(all(r["independentWorld"] is True for r in rows))
        self.assertTrue(all(r["serverSelectable"] is False for r in rows))
        dimensions={r["displayName"]:r["widthKm"] for r in rows}
        self.assertEqual(dimensions,{"SKARVIK":48,"DRAZOVIA":48,
                                     "KARSKOV":30,"VORGRAD":30,
                                     "NEMORIS":20,"DRAKHEIM":20})

    def test_server_browser_catalog_has_six_discrete_packages(self):
        c=(ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaServerBrowserLibrary.cpp").read_text()
        h=(ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaServerBrowserLibrary.h").read_text()
        rows=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        for row in rows:
            self.assertIn('TEXT("'+row["id"]+'")',c)
            self.assertIn('TEXT("'+row["displayName"]+'")',c)
            self.assertIn('TEXT("'+row["originalUnrealPackage"]+'")',c)
        self.assertIn("FilterByMap",h)
        self.assertIn("Server.MapId != MapId",c)
        self.assertIn("Card.bPlayableValidated = false",c)

    def test_four_distinct_biome_profiles_and_auto_building_plans(self):
        planner=load_module("four_world_layout_test","unreal/Scripts/four_world_layout.py")
        profiles=planner.PROFILES
        self.assertEqual(set(profiles),{"KARSKOV","VORGRAD","NEMORIS","DRAKHEIM"})
        self.assertEqual(len({p["theme"] for p in profiles.values()}),4)
        # Simulate modestly sloped elevated land, deliberately not native terrain.
        fake_height=lambda e,n:80.+2.*math.sin(e/2400.)+2.*math.cos(n/1800.)
        for name in sorted(profiles):
            a=planner.plan(name,fake_height)
            b=planner.plan(name,fake_height)
            self.assertEqual(a,b, name+" plan must be reproducible")
            self.assertEqual(a["package"],"/Game/Maps/PRIGIMALIA_"+name)
            self.assertGreaterEqual(len(a["sites"]),5)
            self.assertGreater(len(a["buildings"]),180)
            self.assertGreater(len(a["vegetation"]),50)
            self.assertFalse(a["roadsBuilt"] if "roadsBuilt" in a else a["intercityRoadsBuilt"])
            self.assertFalse(a["gameplayTested"])
            self.assertEqual(len({x["id"] for x in a["buildings"]}),len(a["buildings"]))
            self.assertEqual(len({x["id"] for x in a["vegetation"]}),len(a["vegetation"]))

    def test_no_fake_native_creation_claim(self):
        source=(ROOT/"unreal/Scripts/create_four_additional_maps.py").read_text()
        self.assertIn("new_level(package,is_partitioned_world=True)",source)
        self.assertIn("create_named_world_landscape(NAME)",source)
        self.assertIn("NATIVE_WORLD_SAVED_NOT_PLAYTESTED",source)
        self.assertIn("Existing or partly authored world preserved",source)


if __name__=="__main__":
    unittest.main()
