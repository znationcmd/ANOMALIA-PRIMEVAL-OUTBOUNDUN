"""Static and functional offline tests for ANOMALIA editor and homestead.
Does NOT compile or execute Unreal Engine.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ue5/anomalia-editor-tools.py"
spec = importlib.util.spec_from_file_location("anomalia_editor_tools", SCRIPT)
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
SOURCE = ROOT / "unreal/Source/AnomaliaZPrigimalia"


def cpp(name: str) -> str:
    return (SOURCE / name).read_text(encoding="utf-8")


class EditorScopeTests(unittest.TestCase):
    def test_one_server_does_not_write_another_server(self):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch)
            p1 = tools.add_object(home, "server_a", "bed1", "bed", 0, 0, 10, 0)
            p2 = tools.add_object(home, "server_b", "cow1", "cow", 40, 50, 0, 0)
            self.assertNotEqual(p1, p2)
            self.assertEqual([v["id"] for v in tools.read_world(home, "server_a")["placements"]], ["bed1"])
            self.assertEqual([v["id"] for v in tools.read_world(home, "server_b")["placements"]], ["cow1"])
            tools.remove_object(home, "server_a", "bed1")
            self.assertEqual(len(tools.read_world(home, "server_a")["placements"]), 0)
            self.assertEqual(len(tools.read_world(home, "server_b")["placements"]), 1)

    def test_no_traversal_or_unapproved_world_content(self):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch)
            for identifier in ("../main", "x/y", "..", "other server", ""):
                with self.assertRaises(ValueError):
                    tools.read_world(home, identifier)
            with self.assertRaises(ValueError):
                tools.add_object(home, "safe", "x", "untrusted_code", 0, 0, 0, 0)
            with self.assertRaises(ValueError):
                tools.add_object(home, "safe", "x", "chair", float("nan"), 0, 0, 0)
            self.assertFalse((home / "Servers" / "safe").exists())

    def test_duplicate_placements_fail_without_overwrite(self):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch)
            p = tools.add_object(home, "safe", "bed1", "bed", 0, 0, 0, 0)
            original = p.read_bytes()
            with self.assertRaises(ValueError):
                tools.add_object(home, "safe", "bed1", "chair", 0, 0, 0, 0)
            self.assertEqual(original, p.read_bytes())

    def test_invalid_existing_layout_is_preserved(self):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch)
            file = home / "Servers" / "myserver" / "Editor" / "world.json"
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("{bad", encoding="utf-8")
            with self.assertRaises(ValueError):
                tools.add_object(home, "myserver", "chair1", "chair", 0, 0, 0, 0)
            self.assertEqual(file.read_text(encoding="utf-8"), "{bad")

    def test_mod_tool_is_data_only_and_does_not_claim_console_crossplay(self):
        with tempfile.TemporaryDirectory() as scratch:
            location = tools.mod_template(Path(scratch), "furniture_pack")
            result = tools.lint_mod(location)
            self.assertEqual(result["contentType"], "data-only")
            self.assertEqual(result["platforms"], ["pc"])
            result["platforms"] = ["pc", "ps5"]
            (location / "mod.json").write_text(json.dumps(result), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not approved"):
                tools.lint_mod(location)


class HomesteadSourceTests(unittest.TestCase):
    def test_sleep_bed_and_fatigue_are_authoritative_and_persisted(self):
        player = cpp("AnomaliaZPrigimaliaSurvivor.cpp")
        header = cpp("AnomaliaZPrigimaliaSurvivor.h")
        mode = cpp("AnomaliaZPrigimaliaGameMode.cpp")
        keys = (ROOT / "unreal/Config/DefaultInput.ini").read_text(encoding="utf-8")
        self.assertIn("DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, Fatigue)", player)
        self.assertIn("DOREPLIFETIME(AAnomaliaZPrigimaliaSurvivor, bSleeping)", player)
        self.assertIn("ServerRequestRest_Implementation", player)
        self.assertIn("bSleeping = false;", player)
        self.assertIn("IsRestPlace()", player)
        self.assertIn("GetCharacterMovement()->DisableMovement()", player)
        self.assertIn("HasAuthority()", player)
        self.assertIn("RestoreFatigue", header)
        self.assertIn('TEXT("fatigue")', mode)
        self.assertIn('ActionName="Rest",Key=R', keys)

    def test_farm_harvest_requires_server_and_inventory_success(self):
        station = cpp("AnomaliaZPrigimaliaHomesteadStation.cpp")
        player = cpp("AnomaliaZPrigimaliaSurvivor.cpp")
        inventory = cpp("AnomaliaZPrigimaliaInventoryComponent.cpp")
        self.assertIn("if (!HasAuthority()", station)
        self.assertIn("Survivor->InventoryComponent->TryAddItem(ItemId, 1)", station)
        self.assertIn("NextHarvestTime = Now + 120.f", station)
        self.assertIn('TEXT("milk")', station)
        self.assertIn('TEXT("egg")', station)
        self.assertIn('TEXT("honey")', station)
        self.assertIn('TEXT("milk")', inventory)
        self.assertIn("NearestFarm->TryHarvest(this)", player)

    def test_editor_spawns_only_own_server_world_after_validation(self):
        mode = cpp("AnomaliaZPrigimaliaGameMode.cpp")
        self.assertIn('TEXT("Servers"), ServerId,', mode)
        self.assertIn('TEXT("Editor"), TEXT("world.json")', mode)
        self.assertIn("StoredServer != ServerId", mode)
        self.assertIn("SeenIds.Contains(ObjectId)", mode)
        self.assertIn("Rows->Num() > 256", mode)
        self.assertIn("SpawnConfiguredHomestead();", mode)
        self.assertIn("TryGetNumberField", mode)
        self.assertNotIn("ServerSpawnFurniture_Implementation", mode)

    def test_official_menu_does_not_pretend_servers_online(self):
        browser = cpp("AnomaliaZPrigimaliaServerBrowserLibrary.cpp")
        header = cpp("AnomaliaZPrigimaliaServerBrowserLibrary.h")
        self.assertIn("Result.Reserve(15)", browser)
        self.assertIn("Index <= 5", browser)
        for label in ("PVE", "PVP", "RP"):
            self.assertIn(f'TEXT("{label}")', browser)
        self.assertIn("Card.bOnline = false", browser)
        self.assertIn("Card.bProvisioned = false", browser)
        self.assertIn("FilterByMode", header)
        self.assertIn("Card.Mode != Mode", browser)

    def test_tractor_is_defined_but_not_claimed_modelled(self):
        vehicle = cpp("AnomaliaZPrigimaliaVehicleCatalog.cpp")
        self.assertIn('TEXT("farm_tractor")', vehicle)
        self.assertIn('TEXT("Tracteur agricole")', vehicle)


if __name__ == "__main__":
    unittest.main()
