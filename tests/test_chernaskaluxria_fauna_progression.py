"""Offline CHERNASKALUXRIA fauna progression tests; not evidence of live AI."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
import chernaskaluxria_fauna_progression as fauna
from chernaskaluxria_geography_targets import plan as geography

def first_candidate(species,kwargs):
    for i in range(30000):
        p=fauna.population_plan(cell_id=f"test-{species}-{i}",**kwargs)
        if any(x["speciesId"]==species for x in p["candidateEncounters"]):
            return p
    raise AssertionError("No candidate found in deterministic test sweep for "+species)

class FaunaContracts(unittest.TestCase):
    def test_all_twenty_islands_have_original_fauna_roles(self):
        self.assertEqual(len(fauna.ISLANDS),20)
        self.assertEqual(set(fauna.ISLANDS),{r["id"] for r in geography()["plannedIslands"]})
        self.assertEqual(fauna.review_manifest()["islandPlanCounts"],{200:3,100:6,50:11})
        small=[(name,info) for name,info in fauna.ISLANDS.items() if info["sizeKm2"]==50]
        self.assertEqual(len(small),11)
        self.assertGreaterEqual(sum("pteranodon" in info["fauna"] for _,info in small),4)
        self.assertGreaterEqual(sum("genetic_anomaly" in info["fauna"] for _,info in small),2)
        self.assertTrue(all(len(info["fauna"])>=1 for info in fauna.ISLANDS.values()))
        self.assertEqual(len(fauna.biome_progression()),5)
        self.assertEqual(fauna.WORLD_ID,"chernaskaluxria-v1")

    def test_no_active_creatures_without_verified_geography(self):
        p=fauna.population_plan(cell_id="not-surveyed",zone="metropolis",
            biome="central-metropolis",distance_from_start_m=9000,player_distance_m=50)
        self.assertEqual(p["candidateEncounters"],[])
        self.assertFalse(p["activatedInUnreal"])
        self.assertFalse(p["assetsAndAIControllersVerified"])
        q=fauna.population_plan(cell_id="near-starter",zone="metropolis",
            biome="central-metropolis",geography_verified=True,
            distance_from_start_m=200,player_distance_m=100)
        self.assertEqual(q["candidateEncounters"],[])
        self.assertTrue(q["starterProtected"])

    def test_zombies_five_only_with_authority_and_budgets(self):
        args=dict(zone="metropolis",biome="central-metropolis",
            geography_verified=True,player_distance_m=50,distance_from_start_m=5000)
        valid=first_candidate("zombie",args)
        self.assertEqual(valid["candidateEncounters"][0]["count"],5)
        self.assertTrue(valid["candidateEncounters"][0]["serverAuthoritativeRequired"])
        self.assertFalse(valid["candidateEncounters"][0]["actualActorSpawningEnabled"])
        blocked=fauna.population_plan(cell_id=valid["cellId"],**(args|{"active_ai_in_cell":3}))
        self.assertEqual(blocked["candidateEncounters"],[])
        blocked=fauna.population_plan(cell_id=valid["cellId"],**(args|{"active_ai_near_player":8}))
        self.assertEqual(blocked["candidateEncounters"],[])
        far=fauna.population_plan(cell_id=valid["cellId"],**(args|{"player_distance_m":3000}))
        self.assertEqual(far["candidateEncounters"],[])

    def test_remote_trex_requires_wilderness_far_from_spawns(self):
        args=dict(zone="wilderness",biome="farming-lowlands",geography_verified=True,
            distance_from_start_m=9500,distance_from_settlement_m=4500,player_distance_m=200)
        p=first_candidate("trex",args)
        self.assertEqual(p["candidateEncounters"][0]["tier"],5)
        for kw in ({"distance_from_start_m":2000},{"distance_from_settlement_m":500},
                   {"active_ai_on_server":150}):
            q=fauna.population_plan(cell_id=p["cellId"],**(args|kw))
            self.assertNotIn("trex",[x["speciesId"] for x in q["candidateEncounters"]])

    def test_megalodon_and_mosasaur_do_not_spawn_in_safe_seaways(self):
        args=dict(zone="deep_sea",biome="coastal-ports",geography_verified=True,
            player_distance_m=200,distance_from_start_m=10000,
            water_depth_m=85,shore_distance_m=4000,safe_route_distance_m=4000)
        m=first_candidate("mosasaur",args)
        self.assertEqual(m["candidateEncounters"][0]["count"],1)
        for unsafe in ({"water_depth_m":12},{"safe_route_distance_m":200},
                       {"shore_distance_m":100}):
            q=fauna.population_plan(cell_id=m["cellId"],**(args|unsafe))
            self.assertEqual(q["candidateEncounters"],[])
        # Depth is required, not guessed from an island or coordinate.
        with self.assertRaises(ValueError):
            fauna.population_plan(cell_id="ocean",zone="channel",biome="coastal-ports",
                geography_verified=True,player_distance_m=50,
                distance_from_start_m=10000)
        s=first_candidate("megalodon",args|{"zone":"channel","water_depth_m":25})
        self.assertLessEqual(s["candidateEncounters"][0]["count"],1)
        self.assertFalse(s["candidateEncounters"][0]["actualActorSpawningEnabled"])

    def test_only_planned_small_islands_get_nests_and_anomaly_labs(self):
        for name,species in (("frosh","pteranodon"),("naxor","genetic_anomaly")):
            island=fauna.ISLANDS[name]
            args=dict(zone="small_island",biome=island["biome"],island_id=name,
                geography_verified=True,player_distance_m=100,
                distance_from_start_m=7000)
            p=first_candidate(species,args)
            self.assertTrue(p["candidateEncounters"][0]["requiresVerifiedOwnedOrLicensedCreatureAssets"])
            self.assertFalse(p["candidateEncounters"][0]["tamingAndMountRidingVerified"])
        with self.assertRaises(ValueError):
            fauna.population_plan(cell_id="bad",zone="small_island",island_id="invalid",
                biome="paradise-islands")

    def test_manifest_does_not_claim_installed_assets(self):
        manifest=fauna.review_manifest()
        self.assertFalse(manifest["creatureAssetPathsResolved"])
        self.assertFalse(manifest["gameplayIntegrationEnabled"])
        self.assertFalse(manifest["nativePlaytestsPassed"])
        self.assertFalse(manifest["protectedMarineRouteRules"]["surveyedRoutesExist"])
        self.assertTrue(manifest["sourceOnly"])
        self.assertEqual(manifest["maxConcurrentAI"]["perServer"],150)

if __name__=="__main__":
    unittest.main()
