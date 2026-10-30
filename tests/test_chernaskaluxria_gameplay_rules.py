"""Source tests for independent ninth-world mobility, sparse danger and PCG decisions."""
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))

import chernaskaluxria_gameplay_pcg as pcg
import chernaskaluxria_world as world
import export_chernaskaluxria_pcg_review as exporter


class ChernaskaluxriaGameplayRulesTest(unittest.TestCase):
    def test_all_biomes_have_early_transport_without_crossworld_edit(self):
        hubs=pcg.starter_mobility_hubs()
        self.assertEqual(len(hubs),9)
        self.assertEqual({h["region"] for h in hubs},set(pcg.BIOME_RULES))
        catalog=(ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaVehicleCatalog.cpp").read_text()
        for hub in hubs:
            self.assertIn('TEXT("'+hub["vehicleId"]+'")',catalog)
            self.assertTrue(hub["requiresPhysicalRoadAndVerifiedRig"])
            self.assertFalse(hub["serverSpawnConfirmed"])
            self.assertFalse(hub["flyingMountConfirmed"])
            x,y,z=hub["unrealCm"]
            self.assertLessEqual(abs(x),5_000_000)
            self.assertLessEqual(abs(y),5_000_000)
            self.assertTrue(math.isfinite(z))
        template=pcg.server_vehicle_template()
        self.assertEqual(template["mapId"],"chernaskaluxria-v1")
        self.assertEqual(len(template["vehicles"]),9)
        self.assertFalse(template["activatedOnServer"])
        self.assertEqual(len({h["region"] for h in template["hubs"]}),9)

    def test_danger_cells_sparse_and_radiation_not_falsely_activated(self):
        for e,n,surf,biome in ((32000,8000,"sand","arid-highlands"),
                               (25000,-27000,"ash","devastated-exclusion")):
            p=pcg.plan_population_cell(e,n,surf,100,True)
            self.assertEqual(p["worldId"],"chernaskaluxria-v1")
            self.assertEqual(p["region"],biome)
            self.assertLessEqual(len(p["staticCandidates"]),12)
            self.assertFalse(p["radiationDamageActive"])
            self.assertFalse(p["fullyAuthoredInUE"])
            self.assertTrue(all(v["serverOnly"] and not v["activeInUnreal"] for v in p["spawnEvents"]))
            if biome=="devastated-exclusion":
                self.assertTrue(p["radiationHazardDesign"])
                self.assertTrue(p["radiationWarningAndProtectionNeeded"])
            else:self.assertFalse(p["radiationHazardDesign"])

    def test_real_asphalt_mask_and_verified_enemy_assets_required(self):
        # Without real surface masks no wrecked cars, without AI classes no zombie waves.
        for e in range(-1750,2000,250):
            p=pcg.plan_population_cell(e,0,"asphalt",100,True)
            self.assertLessEqual(len(p["staticCandidates"]),p["maxStaticPerCell"])
            self.assertTrue(all(v["kind"].startswith("licensed_") for v in p["staticCandidates"]))
            for event in p["spawnEvents"]:
                self.assertEqual(event["kind"],"zombie-group")
                self.assertEqual(event["count"],5)
                self.assertTrue(event["serverOnly"])
                self.assertFalse(event["activeInUnreal"])
            inactive=pcg.plan_population_cell(e,0,"asphalt",100,False)
            self.assertEqual(inactive["spawnEvents"],[])
            far=pcg.plan_population_cell(e,0,"asphalt",1500,True)
            self.assertEqual(far["spawnEvents"],[])
        # No asphalt should ever be assumed from coordinates or a biome alone.
        c=pcg.plan_population_cell(0,0,"soil",100,True)
        self.assertFalse(any(v["kind"]=="licensed_abandoned_vehicle" for v in c["staticCandidates"]))

    def test_population_reproducible_bounded_and_streamed_only(self):
        self.assertEqual(pcg.CELL_SIZE_M,250)
        for e,n,s in ((0,0,"asphalt"),(-22000,11000,"soil"),
                      (-9000,-27000,"soil"),(28000,34000,"snow")):
            a=pcg.plan_population_cell(e,n,s,125,True)
            b=pcg.plan_population_cell(e,n,s,125,True)
            self.assertEqual(a,b)
            self.assertLessEqual(len(a["staticCandidates"]),a["maxStaticPerCell"])
            self.assertTrue(all(x["requiresVerifiedLicensedAsset"] for x in a["staticCandidates"]))
        with self.assertRaises(ValueError):
            pcg.plan_population_cell(60000,0,"sand")
        with self.assertRaises(ValueError):
            pcg.plan_population_cell(0,0,"unknown")
        self.assertEqual(len(world.world_tiles()),400)
        self.assertEqual(len(pcg.BIOME_RULES),9)

    def test_native_gamemode_large_world_vehicle_bounds_guarded_by_map(self):
        cpp=(ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaGameMode.cpp").read_text()
        self.assertIn('EndsWith(TEXT("PRIGIMALIA_CHERNASKALUXRIA"))',cpp)
        self.assertIn('ScopedMapId!=TEXT("chernaskaluxria-v1")',cpp)
        self.assertIn('bChMap ? 5000000.0 : 2400000.0',cpp)
        self.assertIn('FMath::Abs(X) > XYLimitCm',cpp)

    def test_preview_artifacts_not_deployed_into_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"pcg-review"
            result=exporter.export(out)
            self.assertFalse(result["changesAppliedToServer"])
            self.assertEqual(len(result["files"]),5)
            fauna_rules=json.loads((out/"fauna-encounters.review.json").read_text())
            self.assertEqual(fauna_rules["mapId"],"chernaskaluxria-v1")
            self.assertEqual(len(fauna_rules["smallIslandFauna"]),20)
            self.assertFalse(fauna_rules["gameplayIntegrationEnabled"])
            hubs=json.loads((out/"starter-hubs.review.json").read_text())["hubs"]
            self.assertEqual(len(hubs),9)
            j=json.loads((out/"world-map-policy.json").read_text())
            self.assertTrue(j["dangerZones"]["radiationWarningsBeforeDamage"])
            self.assertEqual(j["dangerZones"]["maxPerPlayerConcurrentAI"],10)
            with self.assertRaises(FileExistsError):exporter.export(out)


if __name__=="__main__":
    unittest.main()
