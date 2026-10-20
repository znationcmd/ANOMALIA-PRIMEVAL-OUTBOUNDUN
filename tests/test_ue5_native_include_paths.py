"""Regression guard for Unreal C++ includes in nested Tests/ source files.

The real UE5 Editor build still must be run on Windows: this check only verifies
that quoted project-local headers resolve relative to each native source file.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "unreal" / "Source" / "AnomaliaPrimeval"
NESTED = ROOT / "Tests" / "AnomaliaPersistenceTests.cpp"

class TestNativeIncludePaths(unittest.TestCase):
    def test_automation_code_kept_and_project_headers_resolve(self):
        source = NESTED.read_text(encoding="utf-8")
        self.assertIn("#if WITH_DEV_AUTOMATION_TESTS", source)
        self.assertIn("FAnomaliaPersistenceTest", source)
        self.assertIn("FAnomaliaCatalogTest", source)
        for name in ("AnomaliaConfigLibrary.h", "AnomaliaVehicleCatalog.h"):
            with self.subTest(header=name):
                include = f'../{name}'
                self.assertIn(f'#include "{include}"', source)
                self.assertTrue((NESTED.parent / include).is_file(), include)
        self.assertNotIn('#include "AnomaliaConfigLibrary.h"', source)
        self.assertNotIn('#include "AnomaliaVehicleCatalog.h"', source)

if __name__ == "__main__":
    unittest.main()
