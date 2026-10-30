"""Marine island geography for CHERNASKALUXRIA; not a native UE map test."""
import json
import math
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
import chernaskaluxria_archipelago as islands
import chernaskaluxria_world as world
import chernaskaluxria_gameplay_pcg as gameplay

class SatelliteIslandsTests(unittest.TestCase):
    def test_all_island_size_classes_and_distinct_centres(self):
        targets=Counter(i["targetKm2"] for i in islands.SATELLITE_ISLANDS)
        self.assertGreaterEqual(targets[200],2)
        self.assertGreaterEqual(targets[100],3)
        self.assertGreaterEqual(targets[50],3)
        self.assertEqual(set(targets),{200,100,50})
        self.assertEqual(len({i["id"] for i in islands.SATELLITE_ISLANDS}),len(islands.SATELLITE_ISLANDS))
        for item in islands.SATELLITE_ISLANDS:
            cx,cy=item["centreKm"]
            ax,ay=item["axesKm"]
            self.assertLess(abs(cx)+ax,50)
            self.assertLess(abs(cy)+ay,50)
            approx=math.pi*ax*ay
            self.assertLess(abs(approx-item["targetKm2"]),3)
            self.assertGreater(world.terrain_height(cx*1000,cy*1000),1)
            self.assertTrue(item["discovery"])

    def test_real_water_ring_and_actual_island_land_area_near_targets(self):
        # Count actual source height above sea within island's intended shore
        # at 250m. Does NOT assert actual Unreal navmesh/shoreline usability.
        for item in islands.SATELLITE_ISLANDS:
            cx,cy=item["centreKm"]
            ax,ay=item["axesKm"]
            size=int(math.ceil(max(ax,ay)*1000/250))
            dry=0
            for j in range(-size,size+1):
                y=cy*1000+j*250
                for i in range(-size,size+1):
                    x=cx*1000+i*250
                    if islands.satellite_land_mask(item,x,y) and world.terrain_height(x,y)>0:
                        dry+=1
            area=dry*0.0625
            self.assertLess(abs(area-item["targetKm2"]),item["targetKm2"]*.18,
                            (item["id"],area,item["targetKm2"]))
            # A complete marine belt with submerged points in four directions.
            for vx,vy in ((1,0),(-1,0),(0,1),(0,-1)):
                outer_x=cx*1000+vx*ax*1250
                outer_y=cy*1000+vy*ay*1250
                self.assertLess(world.terrain_height(outer_x,outer_y),0.,
                                ("island_not_water_separated",item["id"],vx,vy))

    def test_bridges_tunnels_and_boat_travel_are_plans_not_deployed(self):
        proposals=islands.crossing_plans(world.terrain_height)
        self.assertGreaterEqual(len(proposals),6)
        self.assertGreaterEqual(sum(v["type"]=="bridge" for v in proposals),3)
        self.assertGreaterEqual(sum(v["type"]=="undersea-tunnel" for v in proposals),3)
        for entry in proposals:
            self.assertLess(entry["channelCentreMeters"][2],0,
                            ("crossing_does_not_cross_water",entry["id"]))
            self.assertGreater(entry["spanOrRouteMeters"],1000)
            self.assertFalse(entry["physicalStructureBuilt"])
            self.assertFalse(entry["routeOpenToPlayers"])
        self.assertEqual(len(islands.interisland_voyages()),len(islands.SATELLITE_ISLANDS))
        self.assertTrue(all(not route["waterNavigationTested"] for route in islands.interisland_voyages()))

    def test_world_keeps_one_map_400_tiles_and_nine_biomes(self):
        manifest=world.world_manifest()
        self.assertEqual(manifest["tileCount"],400)
        self.assertEqual(manifest["unrealPackage"],"/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA")
        self.assertEqual(len(manifest["satelliteIslands"]),len(islands.SATELLITE_ISLANDS))
        self.assertEqual(len(manifest["plannedCrossings"]),6)
        self.assertFalse(manifest["bridgesAndTunnelsBuilt"])
        self.assertEqual({a["dominantBiome"] for a in manifest["tiles"]},set(world.NAMES))
        self.assertEqual(len(gameplay.starter_mobility_hubs()),9)
        self.assertFalse(manifest["gameplayValidated"])

    def test_water_surface_increases_and_big_islands_remain(self):
        # Coarse source-only area estimate; CI will also report exact observed ratio.
        result=islands.sampled_surface_area(world.terrain_height,500)
        self.assertEqual(result["totalKm2"],10000)
        self.assertGreater(result["waterKm2"],1700)
        self.assertGreater(result["landKm2"],4500)
        self.assertLess(result["landKm2"],8200)
        print("CHERNASKALUXRIA_ISLAND_SOURCE_AREA "+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    unittest.main()
