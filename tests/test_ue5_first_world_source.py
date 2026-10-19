"""Static checks for ANOMALIA's first World Partition .umap creation tool.

These checks do NOT constitute a native Unreal Editor run.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ue5/create-first-world.py"
RUNNER = ROOT / "scripts/ue5/create-first-world.ps1"
PROJECT = ROOT / "unreal/AnomaliaPrimeval.uproject"


class FirstWorldSourceTests(unittest.TestCase):
    def test_script_syntax_and_partitioned_world(self):
        source = SCRIPT.read_text(encoding="utf-8")
        compile(source, str(SCRIPT), "exec")
        self.assertIn("new_level(MAP_PACKAGE, is_partitioned_world=True)", source)
        self.assertIn("save_all_dirty_levels()", source)
        self.assertIn("OUTPUT_MAP.exists()", source)
        self.assertIn('report("already_exists_not_modified")', source)
        self.assertIn('report("umap_created_needs_ue_play_test"', source)
        self.assertIn("spawn(unreal.PlayerStart", source)
        self.assertNotIn("unlink(", source)
        self.assertNotIn("rmtree(", source)

    def test_python_editor_plugin_is_enabled(self):
        project = json.loads(PROJECT.read_text(encoding="utf-8"))
        self.assertTrue(any(p["Name"] == "PythonScriptPlugin" and p["Enabled"]
                            for p in project["Plugins"]))

    def test_windows_command_needs_native_unreal_and_checks_report(self):
        runner = RUNNER.read_text(encoding="utf-8")
        self.assertIn("UnrealEditor-Cmd.exe", runner)
        self.assertIn("-ExecutePythonScript=", runner)
        self.assertIn("first-world-report.json", runner)
        self.assertIn("Test-Path -LiteralPath $Result.mapFile", runner)


if __name__ == "__main__":
    unittest.main()
