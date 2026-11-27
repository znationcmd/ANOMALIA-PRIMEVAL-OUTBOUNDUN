"""Contract tests for CHERNASKALUXRIA's 100x100 km, 475-site masterplan.
The plan is not a substitute for a native playable Unreal Engine world.
"""
import json
import math
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LAYOUT=json.loads((ROOT/"public/config/chernaskaluxria-world-layout-100km.json").read_text(encoding="utf-8"))
CATALOG=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text(encoding="utf-8"))
DENSITY=json.loads((ROOT/"public/config/prigimalia-settlement-density-by-map.json").read_text(encoding="utf-8"))

class ChernaskaluxriaTest(unittest.TestCase):
    def test_dimensions_and_total(self):
        self.assertEqual(LAYOUT["worldSizeKm"],[100,100])
        self.assertEqual(LAYOUT["totalAreaKm2"],10000)
        self.assertEqual(LAYOUT["counts"],{"majorCities":25,"smallTowns":35,"towns":100,"villages":315,"total":475})
        sites=LAYOUT["settlements"]
        self.assertEqual(len(sites),475)
        self.assertEqual(Counter(s["settlementClass"] for s in sites),Counter({"major-city":25,"small-town":35,"town":100,"village":315}))
        self.assertEqual(len({s["id"] for s in sites}),475)
        self.assertEqual(len({s["name"].casefold() for s in sites}),475)

    def test_every_site_inside_boundary_and_not_overlapping(self):
        sites=LAYOUT["settlements"]
        for s in sites:
            x,y=s["eastKm"],s["northKm"]
            w,h=s["footprintKm"]
            self.assertGreater(w,0)
            self.assertGreater(h,0)
            self.assertLessEqual(abs(x)+w/2,50)
            self.assertLessEqual(abs(y)+h/2,50)
            self.assertFalse(s["worldPartitionActorsVerified"])
            self.assertFalse(s["terrainGradeValidated"])
        for i,a in enumerate(sites):
            for b in sites[i+1:]:
                overlap=(abs(a["eastKm"]-b["eastKm"])<.5*(a["footprintKm"][0]+b["footprintKm"][0])
                         and abs(a["northKm"]-b["northKm"])<.5*(a["footprintKm"][1]+b["footprintKm"][1]))
                self.assertFalse(overlap,f"{a['id']} overlaps {b['id']}")

    def test_connected_road_network_is_planned_not_built(self):
        sites=LAYOUT["settlements"]
        ids={s["id"] for s in sites}
        edges=LAYOUT["roadNetwork"]["roads"]
        self.assertEqual(len(edges),677)
        self.assertEqual(LAYOUT["roadNetwork"]["nativeSplinesBuilt"],0)
        adj={i:set() for i in ids}
        for r in edges:
            self.assertIn(r["from"],ids)
            self.assertIn(r["to"],ids)
            self.assertFalse(r["nativeSplineBuilt"])
            self.assertNotEqual(r["from"],r["to"])
            adj[r["from"]].add(r["to"])
            adj[r["to"]].add(r["from"])
        stack=[sites[0]["id"]]
        visited=set()
        while stack:
            node=stack.pop()
            if node in visited:continue
            visited.add(node)
            stack.extend(adj[node]-visited)
        self.assertEqual(len(visited),475)

    def test_11_independent_maps_preserved(self):
        maps=CATALOG["maps"]
        self.assertEqual(len(maps),11)
        self.assertEqual(len({m["id"] for m in maps}),11)
        map_record=next(m for m in maps if m["displayName"]=="CHERNASKALUXRIA")
        self.assertEqual((map_record["widthKm"],map_record["heightKm"]),(100,100))
        self.assertEqual(map_record["originalUnrealPackage"],"/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA")
        self.assertFalse(map_record["serverSelectable"])
        self.assertFalse(map_record["nativeWorldOpenedAndPlaytested"])
        other=next(m for m in maps if m["displayName"]=="SKARVIK")
        self.assertEqual((other["widthKm"],other["heightKm"]),(48,48))

    def test_density_and_no_false_native_completion(self):
        m=next(x for x in DENSITY["maps"] if x["name"]=="CHERNASKALUXRIA")
        self.assertEqual(m["sizeKm"],[100,100])
        self.assertEqual((m["total"],m["majorCities"],m["smallTowns"],m["towns"],m["villages"]),(475,25,35,100,315))
        self.assertEqual(m["placementPolicy"]["plannedRoadSegments"],677)
        self.assertEqual(m["placementPolicy"]["realNativeBuildingsPlaced"],0)
        self.assertTrue(LAYOUT["constructionGuards"]["originalNativeMapOnDReadOnly"])
        self.assertTrue(LAYOUT["constructionGuards"]["doNotEraseOtherTenMaps"])

if __name__=="__main__":
    unittest.main()
