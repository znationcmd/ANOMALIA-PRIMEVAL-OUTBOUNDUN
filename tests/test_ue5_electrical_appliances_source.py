"""Static electrical-appliance source contract checks (NOT a native UE5 build)."""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "unreal" / "Source" / "AnomaliaPrimeval"
EXAMPLE = ROOT / "unreal" / "Config" / "Anomalia" / "appliances.example.json"


def source(name: str) -> str:
    return (CPP / name).read_text(encoding="utf-8")


class ElectricalAppliancesSourceTests(unittest.TestCase):
    def test_real_actor_classes_and_native_light(self):
        for name in ("AnomaliaPowerGenerator", "AnomaliaRefrigerator",
                     "AnomaliaBatteryCharger", "AnomaliaWorkLight"):
            h, cpp = source(name + ".h"), source(name + ".cpp")
            self.assertIn("UCLASS(Blueprintable)", h, name)
            self.assertIn("SetIsReplicatedByDefault", h + cpp if name == "AnomaliaInventoryComponent" else "SetIsReplicatedByDefault")
            self.assertIn("HasAuthority()", cpp, name)
            self.assertIn("GetLifetimeReplicatedProps", cpp, name)
        light = source("AnomaliaWorkLight.cpp")
        self.assertIn("USpotLightComponent", light)
        self.assertIn("SetVisibility(bIsLit)", light)
        self.assertIn("PowerGenerator->IsSupplyingActor(this)", light)

    def test_charger_preserves_battery_state(self):
        c = source("AnomaliaBatteryCharger.cpp")
        inventory = source("AnomaliaInventoryComponent.cpp")
        self.assertIn("TryRemoveItemWithState(TEXT(\"car_battery\")", c)
        self.assertIn("TryAddItemWithState(TEXT(\"car_battery\")", c)
        self.assertIn("BatteryCharge01", c)
        self.assertIn("batteryCharge01", inventory)
        self.assertIn("OutBatteryCharge01", inventory)

    def test_player_owned_rpc_access(self):
        h = source("AnomaliaSurvivor.h")
        c = source("AnomaliaSurvivor.cpp")
        for name in ("ServerInsertBattery", "ServerRemoveBattery", "ServerSetWorkLightOn",
                     "ServerRefuelGenerator", "ServerPickupGenerator", "ServerPlaceGenerator"):
            self.assertIn("void " + name + "(", h)
            self.assertIn("void AAnomaliaSurvivor::" + name + "_Implementation(", c)
        self.assertIn("FMath::Square(300.f)", c)
        self.assertIn("IsLocallyControlled()", c)
        self.assertIn("TryRemoveItem(TEXT(\"gasoline_canister\"), 1)", c)

    def test_generator_can_move_and_power_all_devices(self):
        generator = source("AnomaliaPowerGenerator.cpp")
        self.assertIn("TryPickupOnServer", generator)
        self.assertIn("TryPlaceOnServer", generator)
        self.assertIn("SetReplicateMovement(true)", generator)
        self.assertIn("!IsValid(Carrier)", generator)
        self.assertIn('TEXT("position")', generator)
        for name in ("AnomaliaRefrigerator.cpp", "AnomaliaBatteryCharger.cpp",
                     "AnomaliaWorkLight.cpp"):
            self.assertIn("PowerGenerator->IsSupplyingActor(this)", source(name))

    def test_example_appliances_connected(self):
        data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        generators = {x["id"]: x for x in data["generators"]}
        self.assertGreaterEqual(len(generators), 1)
        for category in ("refrigerators", "batteryChargers", "workLights"):
            self.assertGreaterEqual(len(data[category]), 1)
            for row in data[category]:
                self.assertIn(row["generatorId"], generators)
                g = generators[row["generatorId"]]
                distance_cm = math.sqrt(sum((float(row[axis])-float(g[axis]))**2 for axis in ("x","y","z")))
                self.assertLessEqual(distance_cm, 1500, (category, row["id"]))
        spawn = source("AnomaliaGameMode.cpp")
        for key in ("generators", "refrigerators", "batteryChargers", "workLights"):
            self.assertIn('TEXT("'+key+'")', spawn)
        self.assertIn("SpawnConfiguredAppliances()", spawn)

    def test_saves_are_server_scoped_and_installer_preserves_local_edits(self):
        for name in ("AnomaliaPowerGenerator.cpp", "AnomaliaRefrigerator.cpp",
                     "AnomaliaBatteryCharger.cpp", "AnomaliaWorkLight.cpp"):
            code = source(name)
            self.assertIn("ProjectSavedDir()", code, name)
            self.assertIn("Game->ServerId" if name in ("AnomaliaRefrigerator.cpp", "AnomaliaBatteryCharger.cpp") else "Mode->ServerId", code, name)
        ps = (ROOT / "scripts" / "ue5" / "Install-Anomalia-Electricite.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-FileHash", ps)
        self.assertIn("CONFLITS.txt", ps)
        self.assertIn("Copy-Item", ps)
        self.assertIn("Remove-Item", ps)
        self.assertNotIn("Remove-Item -LiteralPath $Project -Recurse", ps)


if __name__ == "__main__":
    unittest.main()
