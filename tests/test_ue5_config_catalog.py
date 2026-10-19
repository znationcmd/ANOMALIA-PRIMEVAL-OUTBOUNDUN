import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "unreal/Config/Anomalia/settings-catalog.json"


class UE5ConfigCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.entries = cls.catalog["entries"]
        cls.by_id = {entry["id"]: entry for entry in cls.entries}
        cls.config = json.loads((ROOT / "unreal/Config/Anomalia/config.json").read_text(encoding="utf-8"))

    def test_schema_and_ids_are_valid_and_unique(self):
        self.assertEqual(self.catalog["schemaVersion"], 1)
        self.assertEqual(len(self.by_id), len(self.entries))
        self.assertEqual(
            {entry["status"] for entry in self.entries} - set(self.catalog["statuses"]), set()
        )
        self.assertTrue(all({"name", "description", "type", "range", "default", "scope", "mechanism", "mechanismPath"} <= entry.keys() for entry in self.entries))

    def test_functional_claims_point_to_existing_code(self):
        active = [entry for entry in self.entries if entry["status"] in {"functional", "partial"}]
        for entry in active:
            with self.subTest(id=entry["id"]):
                self.assertTrue((ROOT / entry["mechanismPath"]).is_file())
        # A metadata file must never be described as an implemented Unreal map.
        for entry in self.entries:
            self.assertNotEqual(entry["file"], ".umap")
        self.assertEqual(self.by_id["legacy.engineAssets"]["status"], "migration_only")

    def test_server_and_survival_defaults_match_runtime_template(self):
        expected = {
            "server.name": self.config["server"]["name"],
            "server.port": self.config["server"]["port"],
            "server.maxPlayers": self.config["server"]["maxPlayers"],
            "server.mode": self.config["server"]["mode"],
            "server.thirdPerson": self.config["server"]["thirdPerson"],
            "server.timeMultiplier": self.config["server"]["timeMultiplier"],
            "survival.hungerDrainPerSecond": self.config["survival"]["hungerDrainPerSecond"],
            "survival.thirstDrainPerSecond": self.config["survival"]["thirstDrainPerSecond"],
            "survival.starvationDamagePerSecond": self.config["survival"]["starvationDamagePerSecond"],
        }
        for key, value in expected.items():
            with self.subTest(id=key):
                self.assertEqual(self.by_id[key]["default"], value)
        self.assertEqual(self.by_id["server.port"]["range"], {"min": 1024, "max": 65535})
        self.assertEqual(self.by_id["server.maxPlayers"]["range"], {"min": 1, "max": 64})
        self.assertEqual(self.by_id["server.timeMultiplier"]["range"], {"min": 0.1, "max": 24})

    def test_legacy_formats_are_explicitly_migration_only(self):
        legacy = self.by_id["legacy.configFiles"]
        self.assertEqual(legacy["status"], "migration_only")
        self.assertEqual(legacy["scope"], "migration")
        expected = {
            "admin_config.json", "scenarios.json", "mods.json", "cfggameplay.json",
            "world-settings.json", "creatures.json", "vehicles.xml", "types.xml",
            "globals.xml", "events.xml", "cfglootspawn.xml", "cfgplayerspawnpoints.xml",
            "cfgspawnabletypes.xml", "cfgeventspawns.xml", "messages.xml", "economy.xml",
            "ai.xml", "Game.ini", "GameUserSettings.ini", "serverDZ.cfg", "cfgeconomycore.xml",
        }
        self.assertTrue(expected <= set(legacy["formats"]))
        self.assertEqual(self.by_id["legacy.engineAssets"]["status"], "migration_only")
        self.assertEqual(self.by_id["legacy.engineAssets"]["scope"], "migration")
        self.assertTrue({".umap", ".uasset", ".pbo", ".ark"} <= set(self.by_id["legacy.engineAssets"]["formats"]))
        self.assertEqual(self.by_id["graphics.performanceTargets"]["status"], "not_implemented")


if __name__ == "__main__":
    unittest.main()
