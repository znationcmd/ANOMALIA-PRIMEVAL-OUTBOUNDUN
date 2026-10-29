"""Regression guard for Unreal C++ includes in nested Tests/ source files.

The real UE5 Editor build still must be run on Windows: this check only verifies
that quoted project-local headers resolve relative to each native source file.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "unreal" / "Source" / "AnomaliaZPrigimalia"
NESTED = ROOT / "Tests" / "AnomaliaZPrigimaliaPersistenceTests.cpp"

class TestNativeIncludePaths(unittest.TestCase):
    def test_automation_code_kept_and_project_headers_resolve(self):
        source = NESTED.read_text(encoding="utf-8")
        self.assertIn("#if WITH_DEV_AUTOMATION_TESTS", source)
        self.assertIn("FAnomaliaZPrigimaliaPersistenceTest", source)
        self.assertIn("FAnomaliaZPrigimaliaCatalogTest", source)
        for name in ("AnomaliaZPrigimaliaConfigLibrary.h", "AnomaliaZPrigimaliaVehicleCatalog.h"):
            with self.subTest(header=name):
                include = f'../{name}'
                self.assertIn(f'#include "{include}"', source)
                self.assertTrue((NESTED.parent / include).is_file(), include)
        self.assertNotIn('#include "AnomaliaZPrigimaliaConfigLibrary.h"', source)
        self.assertNotIn('#include "AnomaliaZPrigimaliaVehicleCatalog.h"', source)

class TestCoreOnlineLinkDependency(unittest.TestCase):
    def test_persistent_player_identity_links_coreonline(self):
        # Unreal documentation locates FUniqueNetIdWrapper::ToString in CoreOnline.
        # Source-level guard only; Windows UE5.8 linker build must be verified separately.
        build = (ROOT / "AnomaliaZPrigimalia.Build.cs").read_text(encoding="utf-8")
        gamemode = (ROOT / "AnomaliaZPrigimaliaGameMode.cpp").read_text(encoding="utf-8")
        self.assertIn('PrivateDependencyModuleNames.Add("CoreOnline");', build)
        self.assertIn("AAnomaliaZPrigimaliaGameMode::GetPersistentPlayerId", gamemode)
        self.assertIn("NetId.ToString()", gamemode)
        self.assertIn("SavePersistentPlayer(", gamemode)

if __name__ == "__main__":
    unittest.main()
