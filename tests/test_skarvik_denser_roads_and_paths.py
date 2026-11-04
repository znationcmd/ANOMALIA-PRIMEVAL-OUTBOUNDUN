"""Validate SKARVIK's denser 48km roads and pedestrian/forest paths.
Source-only test; existence of a planned route is not a claim of native geometry.
"""
import json,math,unittest
from pathlib import Path
from collections import deque,defaultdict
ROOT=Path(__file__).resolve().parents[1]
CITY=json.loads((ROOT/"public/config/skarvik-world-layout-48km.json").read_text(encoding="utf-8"))
TRANSPORT=json.loads((ROOT/"public/config/skarvik-transport-network-v2.json").read_text(encoding="utf-8"))
SETTLEMENTS={p["id"]:p for p in CITY["settlements"]}

def inside(p):
 return len(p)==2 and all(isinstance(x,(int,float)) and math.isfinite(x) and -23.9<x<23.9 for x in p)
def check_not_cross_city(edge):
 a,b=(SETTLEMENTS[edge[k]] for k in ("from","to"))
 for city in SETTLEMENTS.values():
  if city["id"] in (a["id"],b["id"]):continue
  for p,q in zip(edge["waypointsKm"],edge["waypointsKm"][1:]):
   for i in range(9):
    t=i/8
    xy=[p[j]*(1-t)+q[j]*t for j in range(2)]
    if (abs(xy[0]-city["eastKm"])<city["footprintKm"][0]/2+.04 and
        abs(xy[1]-city["northKm"])<city["footprintKm"][1]/2+.04):
     raise AssertionError((edge["id"],city["id"],xy))

class DenserSkarvikRoads(unittest.TestCase):
 def test_382_network_links_no_duplicates_connected(self):
  self.assertEqual(len(SETTLEMENTS),125)
  links=CITY["roads"]
  self.assertEqual(len(links),382)
  self.assertEqual(CITY["transportNetwork"]["existingRegionalConnections"],137)
  self.assertEqual(CITY["transportNetwork"]["newRegionalConnections"],245)
  seen=set();neighbors=defaultdict(set)
  for link in links:
   a,b=link["from"],link["to"]
   self.assertIn(a,SETTLEMENTS);self.assertIn(b,SETTLEMENTS)
   self.assertNotEqual(a,b)
   key=tuple(sorted((a,b)))
   self.assertNotIn(key,seen);seen.add(key)
   neighbors[a].add(b);neighbors[b].add(a)
   self.assertEqual(link["status"],"planned-not-constructed")
   self.assertFalse(link["nativeSplineBuilt"])
  frontier=deque(["citysample"]);found=set(frontier)
  while frontier:
   for other in neighbors[frontier.popleft()]:
    if other not in found:found.add(other);frontier.append(other)
  self.assertEqual(found,set(SETTLEMENTS))
  self.assertEqual(TRANSPORT["totalInterSettlementRoads"],len(links))
 def test_new_245_centerlines_bounded_and_do_not_cross_other_towns(self):
  new=[l for l in CITY["roads"] if l.get("id","").startswith("SK-RX-")]
  self.assertEqual(len(new),245)
  self.assertEqual(len({l["id"] for l in new}),245)
  for l in new:
   self.assertEqual(len(l["waypointsKm"]),4)
   self.assertTrue(all(inside(p) for p in l["waypointsKm"]))
   self.assertGreater(l["estimatedAlignmentKm"],.1)
   self.assertFalse(l["landscapeSlopeVerified"])
   check_not_cross_city(l)
 def test_992_street_segments_without_touching_citysample(self):
  layouts=TRANSPORT["localStreetLayouts"]
  self.assertEqual(len(layouts),124)
  self.assertNotIn("citysample",{x["settlementId"] for x in layouts})
  self.assertEqual(TRANSPORT["localStreetSegmentCount"],992)
  self.assertEqual({x["settlementId"] for x in layouts},set(SETTLEMENTS)-{"citysample"})
  for layout in layouts:
   s=SETTLEMENTS[layout["settlementId"]]
   self.assertEqual(len(layout["localSegments"]),8)
   self.assertFalse(layout["nativeRoadSurfacesBuilt"])
   for road in layout["localSegments"]:
    for p in road["pointsKm"]:
     self.assertTrue(inside(p))
     self.assertLessEqual(abs(p[0]-s["eastKm"]),s["footprintKm"][0]/2+.001)
     self.assertLessEqual(abs(p[1]-s["northKm"]),s["footprintKm"][1]/2+.001)
 def test_302_nature_paths_to_every_village(self):
  trails=TRANSPORT["trails"]
  self.assertEqual(TRANSPORT["trailPathCount"],302)
  self.assertEqual(len(trails),302)
  self.assertEqual(len({x["id"] for x in trails}),302)
  self.assertEqual({p["fromSettlement"] for p in trails},set(SETTLEMENTS))
  for path in trails:
   self.assertTrue(all(inside(pt) for pt in path["pointsKm"]))
   self.assertFalse(path["nativeSplineBuilt"])
   self.assertTrue(path["terrainSurveyRequired"])
   self.assertGreater(path["estimatedLengthKm"],.3)
   for point in path["pointsKm"][1:]:
    for s in SETTLEMENTS.values():
     if s["id"]==path["fromSettlement"]:continue
     self.assertFalse(abs(point[0]-s["eastKm"])<s["footprintKm"][0]/2+.02 and
                      abs(point[1]-s["northKm"])<s["footprintKm"][1]/2+.02)
 def test_native_integration_is_explicitly_unverified(self):
  self.assertEqual(TRANSPORT["status"],"TRANSPORT_CENTERLINES_ONLY_UNREAL_3D_IMPORT_PENDING")
  self.assertFalse(TRANSPORT["validationGates"]["terrainSplineBuildCompleted"])
  self.assertFalse(TRANSPORT["validationGates"]["collisionsAndSM5DriveTested"])
  self.assertFalse(CITY["transportNetwork"]["engineRoadMeshesConstructed"])
  self.assertEqual((CITY["extentKm"]["width"],CITY["extentKm"]["height"]),(48,48))
  self.assertFalse(CITY["citySample"]["trafficSpawns"])
  self.assertFalse(CITY["citySample"]["crowdSpawns"])

if __name__=="__main__":
 unittest.main()
