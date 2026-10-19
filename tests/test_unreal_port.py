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
        self.assertEqual(len(ids), 27)
        self.assertEqual(len(set(ids)), len(ids))
        for expected in ("transport_truck", "semi_truck", "quad", "buggy", "snowmobile",
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

    def test_migration_script_is_non_destructive(self):
        source = (ROOT / "scripts" / "migrate-to-ue5.py").read_text(encoding="utf-8")
        self.assertIn("if destination.exists():", source)
        self.assertIn("conflicts", source)
        self.assertNotIn("rmtree(", source)
        self.assertNotIn("unlink(", source)

if __name__ == "__main__":
    unittest.main()
