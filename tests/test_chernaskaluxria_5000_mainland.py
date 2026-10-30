"""Do not confuse 5000 km2 MAINLAND with total land or total ninth-world size."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
import chernaskaluxria_geography_targets as targets
import chernaskaluxria_world as world

class ChMainlandTargetTest(unittest.TestCase):
    def test_exact_area_budget_and_twenty_distinct_islands(self):
        d=targets.plan()
        self.assertEqual(d["worldAreaKm2"],10000)
        self.assertEqual(d["mainlandTargetKm2"],5000)
        self.assertEqual(d["satelliteIslandsTargetKm2"],1750)
        self.assertEqual(d["seaTargetKm2"],3250)
        self.assertEqual(d["landTargetKm2"],6750)
        self.assertEqual(d["islandCount"],20)
        self.assertEqual(d["islandCountsByAreaKm2"],{200:3,100:6,50:11})
        self.assertEqual(Counter(i["targetKm2"] for i in d["plannedIslands"]),{200:3,100:6,50:11})
        self.assertEqual(sum(i["targetKm2"] for i in d["plannedIslands"]),1750)
        self.assertEqual(len({i["id"] for i in d["plannedIslands"]}),20)
        self.assertFalse(d["physicalHeightmapMatchesBudget"])
        self.assertFalse(d["nativeUmapMatchesBudget"])
        self.assertFalse(d["seaNavigationPlaytested"])
        self.assertTrue(all(not i["separatedByNavigableWater"] for i in d["plannedIslands"]))

    def test_nine_maps_unchanged_and_current_geometry_not_misrepresented(self):
        catalog=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        self.assertEqual(len(catalog),9)
        self.assertEqual(sum(v["widthKm"]*v["heightKm"] for v in catalog),17533)
        ninth=next(m for m in catalog if m["displayName"]=="CHERNASKALUXRIA")
        self.assertFalse(ninth["serverSelectable"])
        self.assertEqual(ninth["widthKm"],100)
        self.assertEqual(ninth["heightKm"],100)
        manifest=world.world_manifest()
        self.assertTrue(manifest["currentTerrainUsesOnlyEightDraftSatellites"])
        self.assertFalse(manifest["revisedTwentyIslandHeightfieldGenerated"])
        self.assertEqual(len(manifest["satelliteIslands"]),8)
        self.assertEqual(len(manifest["targetGeography"]["plannedIslands"]),20)
        self.assertEqual(manifest["targetGeography"]["seaTargetKm2"],3250)
        self.assertEqual(manifest["targetGeography"]["mainlandTargetKm2"],5000)
        self.assertFalse(manifest["gameplayValidated"])

if __name__=="__main__":
    unittest.main()
