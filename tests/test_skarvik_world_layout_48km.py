"""Validate the new SKARVIK world specification without loading Unreal or licensed assets."""
import json
import unittest
from collections import defaultdict, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"public/config/skarvik-world-layout-48km.json"
CATALOG=ROOT/"public/config/anomalia-map-catalog.json"
SKARVIK_STAGING=ROOT/"public/config/skarvik-citysample-sm5-replacement.json"

class SkarvikWorldSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(SPEC.read_text(encoding="utf-8"))
        cls.catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.staged=json.loads(SKARVIK_STAGING.read_text(encoding="utf-8"))
    def test_world_extent_and_original_identity(self):
        extent=self.data["extentKm"]
        self.assertEqual((extent["width"],extent["height"]),(48,48))
        self.assertEqual((extent["xMin"],extent["xMax"],extent["northMin"],extent["northMax"]),(-24,24,-24,24))
        skarvik=next(x for x in self.catalog["maps"] if x["displayName"]=="SKARVIK")
        self.assertEqual((skarvik["widthKm"],skarvik["heightKm"]),(48,48))
        self.assertEqual(skarvik["originalUnrealPackage"],"/Game/Maps/ANOMALIA_Archipelago_v2")
        self.assertEqual(self.staged["skarvikWorldExtentKm"],[48,48])
        self.assertTrue(self.staged["guards"]["neverShrinkSkarvikTo4Km"])
        self.assertFalse(self.staged["gates"]["activateSKARVIK"])
    def test_every_settlement_inside_world_without_footprint_overlap(self):
        places=self.data["settlements"]
        self.assertGreaterEqual(len(places),15)
        self.assertEqual(len({x["id"] for x in places}),len(places))
        for p in places:
            w,h=p["footprintKm"]
            self.assertGreater(w,0);self.assertGreater(h,0)
            self.assertLessEqual(abs(p["eastKm"])+w/2,24)
            self.assertLessEqual(abs(p["northKm"])+h/2,24)
            self.assertIn(p["biome"],{z["id"] for z in self.data["biomeZones"]})
        for i,a in enumerate(places):
            for b in places[i+1:]:
                overlapping=abs(a["eastKm"]-b["eastKm"])<(a["footprintKm"][0]+b["footprintKm"][0])/2 and abs(a["northKm"]-b["northKm"])<(a["footprintKm"][1]+b["footprintKm"][1])/2
                self.assertFalse(overlapping,(a["id"],b["id"]))
    def test_snow_desert_forest_and_multiple_big_cities(self):
        places=self.data["settlements"]
        self.assertGreaterEqual(len([p for p in places if p["kind"]=="large-city"]),2)
        self.assertGreaterEqual(len([p for p in places if p["biome"]=="snow" and p["kind"] in ("town","village")]),2)
        self.assertGreaterEqual(len([p for p in places if p["biome"]=="desert"]),3)
        self.assertGreaterEqual(len([p for p in places if p["biome"]=="forest"]),3)
        city=self.data["citySample"]
        self.assertEqual(city["fullCityKm"],[4,4])
        self.assertFalse(city["gameplayTransferred"])
        self.assertFalse(city["sm5Optimized"])
        self.assertEqual(city["trafficSpawns"],0)
        self.assertEqual(city["crowdSpawns"],0)
    def test_road_graph_is_fully_connected(self):
        nodes={p["id"] for p in self.data["settlements"]}
        neighbors=defaultdict(set)
        for edge in self.data["roads"]:
            a,b=edge["from"],edge["to"]
            self.assertIn(a,nodes);self.assertIn(b,nodes)
            self.assertNotEqual(a,b)
            neighbors[a].add(b);neighbors[b].add(a)
        seen={"citysample"};todo=deque(seen)
        while todo:
            for n in neighbors[todo.popleft()]:
                if n not in seen:
                    seen.add(n);todo.append(n)
        self.assertEqual(seen,nodes)
    def test_no_implied_complete_asset_import(self):
        self.assertIn("NOT_DONE",self.data["status"])
        self.assertEqual(self.data["citySample"]["assetStatus"] if "assetStatus" in self.data["citySample"] else "not-migrated","not-migrated")
        self.assertTrue(self.data["rules"]["keepOriginalSkarvik"])
        self.assertTrue(self.data["rules"]["maintainOtherMaps"])

if __name__=="__main__":
    unittest.main()
