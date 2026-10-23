"""Source regression checks for the UE5.8 installed engine target configuration.

A successful test does NOT prove the native Unreal C++ build passes; it only
guards against the specific UBT shared editor environment mismatch reported
on 2026-10-20 after installing MSVC 14.50 + Windows SDK 10.0.26100.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "unreal" / "Source"

class InstalledEngineTargets(unittest.TestCase):
    def test_editor_and_game_use_compatible_ue58_build_settings(self):
        for name in ("AnomaliaPrimevalEditor.Target.cs", "AnomaliaPrimeval.Target.cs"):
            with self.subTest(target=name):
                code = (SOURCE / name).read_text(encoding="utf-8")
                self.assertIn("DefaultBuildSettings = BuildSettingsVersion.V7;", code)
                self.assertNotIn("DefaultBuildSettings = BuildSettingsVersion.V5;", code)
                self.assertNotIn("DefaultBuildSettings = BuildSettingsVersion.V6;", code)
                self.assertNotIn("BuildEnvironment = TargetBuildEnvironment.Unique", code)
                self.assertNotIn("bOverrideBuildEnvironment = true", code)
                self.assertIn('ExtraModuleNames.Add("AnomaliaPrimeval");', code)

if __name__ == "__main__":
    unittest.main()
