"""Integration contract: confirms previously separate UE5 work is retained.

These are SOURCE checks, not evidence of an Unreal Engine compile or playtest.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "unreal/Source/AnomaliaZPrigimalia"
SCRIPTS = ROOT / "scripts/ue5"


class WorldHomesteadIntegrationTests(unittest.TestCase):
    def test_native_survivor_inventory_farming_remains_present(self):
        for name in ("AnomaliaZPrigimaliaSurvivor.cpp", "AnomaliaZPrigimaliaInventoryComponent.cpp",
                     "AnomaliaZPrigimaliaHomesteadStation.cpp", "AnomaliaZPrigimaliaVitalsComponent.cpp",
                     "AnomaliaZPrigimaliaServerBrowserLibrary.cpp"):
            self.assertTrue((CODE / name).is_file(), name)
        gm = (CODE / "AnomaliaZPrigimaliaGameMode.cpp").read_text(encoding="utf-8")
        self.assertIn("SpawnConfiguredHomestead();", gm)
        self.assertIn("LoadPersistentPlayer(NewPlayer);", gm)

    def test_two_world_bootstrap_paths_coexist_without_overwrites(self):
        for name in ("create-first-world.py", "create-first-world.ps1",
                     "create-terrain-draft-level.py", "bootstrap-draft-landscape.ps1",
                     "generate-playtest-terrain.py", "generate-terrain.py"):
            self.assertTrue((SCRIPTS / name).is_file(), name)
        first = (SCRIPTS / "create-first-world.py").read_text(encoding="utf-8")
        draft = (SCRIPTS / "create-terrain-draft-level.py").read_text(encoding="utf-8")
        self.assertIn("if OUTPUT_MAP.exists():", first)
        self.assertIn("if MAP.exists():", draft)
        self.assertNotEqual("ANOMALIA_FirstTest", "ANOMALIA_TerrainDraft")

    def test_azerty_qwerty_and_python_editor_are_enabled(self):
        keys = (ROOT / "unreal/Config/DefaultInput.ini").read_text(encoding="utf-8")
        for key in ("W", "Z"):
            self.assertIn(f'AxisName="MoveForward",Scale=1.000000,Key={key}', keys)
        for key in ("A", "Q"):
            self.assertIn(f'AxisName="MoveRight",Scale=-1.000000,Key={key}', keys)
        project = json.loads((ROOT / "unreal/AnomaliaZPrigimalia.uproject").read_text(encoding="utf-8"))
        self.assertTrue(any(p.get("Name") == "PythonScriptPlugin" and p.get("Enabled")
                            for p in project.get("Plugins", [])))


if __name__ == "__main__":
    unittest.main()
