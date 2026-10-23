"""Static UE5 migration checks. These do not replace compiling in Unreal Editor."""
from __future__ import annotations
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "unreal" / "Source" / "AnomaliaPrimeval"

class UnrealPortTests(unittest.TestCase):
    def test_project_and_cpp_module_present(self):
        self.assertTrue((ROOT / "unreal" / "AnomaliaPrimeval.uproject").is_file())
        for name in ["AnomaliaGameMode", "AnomaliaSurvivor",
                     "AnomaliaConfigLibrary", "AnomaliaVehicleCatalog", "AnomaliaVehiclePawn"]:
            self.assertTrue((SOURCE / (name + ".h")).is_file(), name)
            self.assertTrue((SOURCE / (name + ".cpp")).is_file(), name)

    def test_requested_vehicle_catalog_is_unique(self):
        cpp = (SOURCE / "AnomaliaVehicleCatalog.cpp").read_text(encoding="utf-8")
        ids = re.findall(r'MakeVehicle\(TEXT\("([^"]+)"\)', cpp)
        self.assertEqual(len(ids), 45)
        self.assertEqual(len(set(ids)), len(ids))
        for expected in ("airliner", "airplane", "train", "farm_tractor", "transport_truck", "semi_truck", "quad", "buggy", "snowmobile",
                         "jetski", "zodiac", "dirt_bike", "kart", "formula_one", "motorcycle",
                         "car", "suv", "police", "gendarmerie", "fire_engine", "ambulance",
                         "armored_van", "van", "fighter_jet", "attack_helicopter",
                         "transport_helicopter", "monster_truck", "carrier", "warship",
                         "submarine"):
            self.assertIn(expected, ids)

    def test_server_isolation_and_no_cross_server_writes(self):
        cpp = (SOURCE / "AnomaliaConfigLibrary.cpp").read_text(encoding="utf-8")
        self.assertIn('TEXT("Servers")', cpp)
        self.assertIn('TEXT("userProfile")', cpp)
        self.assertIn("ValidId(ServerId)", cpp)
        pawn = (SOURCE / "AnomaliaVehiclePawn.cpp").read_text(encoding="utf-8")
        self.assertIn("HasAuthority()", pawn)
        self.assertIn("DOREPLIFETIME", pawn)
        self.assertIn("ServerSetControls_Implementation", pawn)

    def test_vehicle_interaction_is_server_authoritative(self):
        survivor = (SOURCE / "AnomaliaSurvivor.cpp").read_text(encoding="utf-8")
        vehicle = (SOURCE / "AnomaliaVehiclePawn.cpp").read_text(encoding="utf-8")
        inputs = (ROOT / "unreal" / "Config" / "DefaultInput.ini").read_text(encoding="utf-8")
        self.assertIn('ActionName="Interact",Key=E', inputs)
        self.assertIn("ServerTryEnterVehicle_Implementation", survivor)
        self.assertIn("Candidate->HasDriver()", survivor)
        self.assertIn("FVector::DistSquared", survivor)
        self.assertIn("DriverController->Possess(this)", vehicle)
        self.assertIn("ServerExitVehicle_Implementation", vehicle)
        self.assertIn("DriverController->Possess(Survivor)", vehicle)
        self.assertIn("Survivor->SetActorHiddenInGame(false)", vehicle)
        self.assertNotIn("Survivor->Destroy()", vehicle)

    def test_vehicle_fuel_is_server_authoritative_and_replicated(self):
        header = (SOURCE / "AnomaliaVehiclePawn.h").read_text(encoding="utf-8")
        cpp = (SOURCE / "AnomaliaVehiclePawn.cpp").read_text(encoding="utf-8")
        self.assertIn("ReplicatedUsing=OnRep_Fuel", header)
        self.assertIn("BlueprintAuthorityOnly", header)
        self.assertIn("FuelConsumptionPerSecond", header)
        self.assertIn("HasAuthority() || !FMath::IsFinite(AmountPercent)", cpp)
        self.assertIn("DOREPLIFETIME(AAnomaliaVehiclePawn, FuelPercent)", cpp)
        self.assertIn("FuelPercent > KINDA_SMALL_NUMBER", cpp)
        self.assertIn("OnFuelChanged(FuelPercent)", cpp)
        self.assertNotIn("ServerRefuel", header)  # no unrestricted client refuel RPC

    def test_vehicle_tuning_is_scoped_validated_and_replicated(self):
        import json
        game_mode = (SOURCE / "AnomaliaGameMode.cpp").read_text(encoding="utf-8")
        header = (SOURCE / "AnomaliaVehiclePawn.h").read_text(encoding="utf-8")
        pawn = (SOURCE / "AnomaliaVehiclePawn.cpp").read_text(encoding="utf-8")
        template = json.loads((ROOT / "unreal" / "Config" / "Anomalia" / "vehicles.example.json").read_text(encoding="utf-8"))
        for key in ("fuelPercent", "fuelConsumptionPerSecond", "speedMultiplier"):
            self.assertIn(key, template["vehicles"][0])
            self.assertIn('TEXT("' + key + '")', game_mode)
        self.assertIn('TEXT("Servers"), ServerId, TEXT("vehicles.json")', game_mode)
        self.assertIn("ConfigureRuntimeTuning(", game_mode)
        self.assertIn("HasAuthority()", pawn)
        self.assertIn("FMath::IsFinite(InitialFuelPercent)", pawn)
        self.assertIn("SpeedMultiplier * (100000.f / 3600.f)", pawn)
        self.assertIn("DOREPLIFETIME(AAnomaliaVehiclePawn, SpeedMultiplier)", pawn)
        self.assertIn("ReplicatedUsing=OnRep_Tuning", header)
        self.assertNotIn("ServerSetFuel", header)

    def test_game_mode_loads_independent_server_config(self):
        header = (SOURCE / "AnomaliaGameMode.h").read_text(encoding="utf-8")
        cpp = (SOURCE / "AnomaliaGameMode.cpp").read_text(encoding="utf-8")
        self.assertIn("FAnomaliaServerSettings ActiveServerSettings", header)
        self.assertIn("virtual void InitGame(", header)
        self.assertIn('ParseOption(Options, TEXT("AnomaliaServerId"))', cpp)
        self.assertIn("RequestedId.Len() <= 64", cpp)
        self.assertIn("LoadServerSettings(ServerId, ActiveServerSettings", cpp)
        self.assertNotIn("SaveServerSettings(ServerId", cpp)

    def test_vehicle_spawns_are_bounded_and_server_scoped(self):
        cpp = (SOURCE / "AnomaliaGameMode.cpp").read_text(encoding="utf-8")
        header = (SOURCE / "AnomaliaGameMode.h").read_text(encoding="utf-8")
        self.assertIn("SpawnConfiguredVehicles()", header)
        self.assertRegex(cpp, r"if\s*\(HasAuthority\(\)\)\s*\{\s*SpawnConfiguredHomestead\(\);\s*SpawnConfiguredVehicles\(\);")
        self.assertIn('TEXT("Servers"), ServerId, TEXT("vehicles.json")', cpp)
        self.assertIn("Spawned >= 64", cpp)
        self.assertIn("Bytes > 262144", cpp)
        self.assertIn("FMath::IsFinite(X)", cpp)
        self.assertIn("FindVehicleDefinition(VehicleId, Definition)", cpp)
        self.assertNotIn("ServerSpawnVehicle", cpp)
        template = ROOT / "unreal" / "Config" / "Anomalia" / "vehicles.example.json"
        import json
        parsed = json.loads(template.read_text(encoding="utf-8"))
        self.assertTrue(parsed["vehicles"])

    def test_survival_rates_are_per_server_and_authoritative(self):
        import json
        template = json.loads((ROOT / "unreal" / "Config" / "Anomalia" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(template["survival"]["hungerDrainPerSecond"], 0.015)
        self.assertEqual(template["survival"]["thirstDrainPerSecond"], 0.025)
        header = (SOURCE / "AnomaliaConfigLibrary.h").read_text(encoding="utf-8")
        loader = (SOURCE / "AnomaliaConfigLibrary.cpp").read_text(encoding="utf-8")
        survivor = (SOURCE / "AnomaliaSurvivor.cpp").read_text(encoding="utf-8")
        for name in ("HungerDrainPerSecond", "ThirstDrainPerSecond", "StarvationDamagePerSecond"):
            self.assertIn(name, header)
            self.assertIn(name, loader)
            self.assertIn("ActiveServerSettings." + name, survivor)
        self.assertIn("GetAuthGameMode()", survivor)
        self.assertIn("if (!HasAuthority()) return;", survivor)
        self.assertIn('Root->SetObjectField(TEXT("survival"), Survival)', loader)
        self.assertIn('Root->TryGetObjectField(TEXT("survival")', loader)

    def test_4k60_console_targets_are_configured_but_not_claimed_certified(self):
        import configparser
        root = ROOT / "unreal" / "Config"
        engine = (root / "DefaultEngine.ini").read_text(encoding="utf-8")
        for setting in ("r.Nanite.ProjectEnabled=True", "r.AntiAliasingMethod=4",
                        "r.DynamicRes.FrameTimeBudget=16.6667", "r.Shadow.Virtual.Enable=1"):
            self.assertIn(setting, engine)
        # Unreal INI arrays use repeated +Key entries; the preset scalars remain unique.
        presets = configparser.ConfigParser(strict=False)
        presets.read(root / "DefaultGame.ini", encoding="utf-8")
        for name in ("PC_High", "PS5_Target", "XboxSeriesX_Target", "XboxSeriesS_Target", "Android_Mobile_Target", "IOS_Mobile_Target", "Performance_Fallback"):
            section = "Anomalia." + name
            self.assertIn(section, presets)
            minimum = presets.getint(section, "RenderScaleMin")
            maximum = presets.getint(section, "RenderScaleMax")
            self.assertTrue(25 <= minimum <= maximum <= 100)
        cpp = (SOURCE / "AnomaliaPerformanceLibrary.cpp").read_text(encoding="utf-8")
        self.assertIn("GGameIni", cpp)
        self.assertIn("SaveSettings()", cpp)
        self.assertNotIn("SaveServerSettings", cpp)

    def test_mobile_renderer_does_not_override_pc_settings(self):
        import configparser
        root = ROOT / "unreal" / "Config"
        for platform in ("Android", "IOS"):
            config = configparser.ConfigParser()
            config.read(root / platform / (platform + "Engine.ini"))
            renderer = config["/Script/Engine.RendererSettings"]
            self.assertFalse(renderer.getboolean("r.MobileHDR"))
            self.assertFalse(renderer.getboolean("r.Nanite.ProjectEnabled"))
            self.assertEqual(renderer.getint("r.DynamicGlobalIlluminationMethod"), 0)
        presets = configparser.ConfigParser(strict=False)
        presets.read(root / "DefaultGame.ini")
        for name in ("Android_Mobile_Target", "IOS_Mobile_Target"):
            self.assertEqual(presets.getint("Anomalia." + name, "FrameRateLimit"), 30)

    def test_migration_script_is_non_destructive(self):
        source = (ROOT / "scripts" / "migrate-to-ue5.py").read_text(encoding="utf-8")
        self.assertIn("if destination.exists():", source)
        self.assertIn("conflicts", source)
        self.assertNotIn("rmtree(", source)
        self.assertNotIn("unlink(", source)

if __name__ == "__main__":
    unittest.main()
