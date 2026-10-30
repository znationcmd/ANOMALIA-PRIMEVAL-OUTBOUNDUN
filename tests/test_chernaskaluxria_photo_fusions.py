"""Verify the ten uploaded reference roles and original five-world terrain sources."""
import json
import math
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
import chernaskaluxria_world as world
import chernaskaluxria_topographic_fusion as fusion
from chernaskaluxria_geography_targets import plan as geography_plan

class FiveTopographicFusionTests(unittest.TestCase):
    def test_exact_user_photographic_pair_assignment(self):
        m=json.loads((ROOT/"public/config/prigimalia-topographic-fusion-manifest.json").read_text())
        mapping={x["name"]:x["references"] for x in m["worlds"]}
        self.assertEqual(mapping["VORGRAD"],[1,2])
        self.assertEqual(mapping["NEXAVARKHOS"],[3,4])
        self.assertEqual(mapping["SOLYNACALYRA"],[5,6])
        self.assertEqual(mapping["DRAKHEIM"],[7,8])
        self.assertEqual(mapping["CHERNASKALUXRIA"],list(range(1,11)))
        self.assertEqual({x["name"] for x in m["worlds"]},
          {"VORGRAD","NEXAVARKHOS","SOLYNACALYRA","DRAKHEIM","CHERNASKALUXRIA"})
        self.assertTrue(m["noMergeIntoMain"])
        self.assertIn("NEVER",m["policy"].upper())

    def test_dimensions_and_no_eight_world_conflicts(self):
        m=json.loads((ROOT/"public/config/prigimalia-topographic-fusion-manifest.json").read_text())
        expected={"VORGRAD":30,"NEXAVARKHOS":10,"SOLYNACALYRA":15,
                  "DRAKHEIM":20,"CHERNASKALUXRIA":100}
        for item in m["worlds"]:
            self.assertEqual(item["sizeKm"],[expected[item["name"]]]*2)
            self.assertFalse(item["nativeUmapBuilt"])
        catalog=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        self.assertEqual(len(catalog),9)
        self.assertEqual(len({r["saveNamespace"] for r in catalog}),9)
        self.assertEqual({x["displayName"] for x in catalog if x["displayName"] in expected},set(expected))
        self.assertFalse(any(x["serverSelectable"] for x in catalog if x["displayName"]=="CHERNASKALUXRIA"))

    def test_ninth_world_has_all_ten_reference_styles_active(self):
        self.assertEqual(set(fusion.FUSION_REFERENCES),{"1-2","3-4","5-6","7-8","9-10"})
        self.assertFalse(fusion.fusion_manifest()["realHeightSampleInput"])
        self.assertTrue(fusion.fusion_manifest()["originalTopographicOverlayCodeReady"])
        for name,x,y,_,_ in world.REGIONS:
            w=world.region_weights(x*1000,y*1000)
            z=fusion.source_height_overlay(x*1000,y*1000,w)
            self.assertTrue(math.isfinite(z))
            self.assertEqual(z,fusion.source_height_overlay(x*1000,y*1000,w))
        spans=[]
        for name,x,y,_,_ in world.REGIONS:
            a=world.terrain_height(x*1000,y*1000)
            b=world.terrain_height(x*1000+5,y*1000)
            self.assertTrue(math.isfinite(a))
            self.assertLess(abs(a-b),30)
            spans.append(a)
        self.assertGreater(max(spans)-min(spans),60)
        self.assertEqual(len(world.world_tiles()),400)
        self.assertEqual(len(world.world_manifest()["topographicFusion"]["imagePairs"]),5)

    def test_geometry_budget_stays_honest(self):
        g=geography_plan()
        self.assertEqual(g["mainlandTargetKm2"],5000)
        self.assertEqual(g["satelliteIslandsTargetKm2"],1750)
        self.assertEqual(g["seaTargetKm2"],3250)
        self.assertEqual(g["islandCount"],20)
        self.assertFalse(g["nativeUmapMatchesBudget"])
        self.assertFalse(g["physicalHeightmapMatchesBudget"])
        self.assertFalse(world.world_manifest()["revisedTwentyIslandHeightfieldGenerated"])

if __name__=="__main__":
    unittest.main()
