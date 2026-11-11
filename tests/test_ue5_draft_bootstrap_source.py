"""Static verifications only; requires native Unreal Editor to generate a real .umap."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DraftWorldSourceTests(unittest.TestCase):
    def test_editor_creates_partitioned_level_without_overwriting(self):
        source = (ROOT / "scripts/ue5/create-terrain-draft-level.py").read_text(encoding="utf-8")
        compile(source, "<Unreal Python source>", "exec")
        self.assertIn("validate_sources()", source)
        self.assertIn("editor.new_level(PACKAGE, is_partitioned_world=True)", source)
        self.assertIn('if MAP.exists():', source)
        self.assertIn('"already_exists_not_modified"', source)
        self.assertIn("save_all_dirty_levels()", source)
        self.assertIn("hashlib.sha256(filename.read_bytes()).hexdigest()", source)
        self.assertIn('"landscapeImported": False', source)
        self.assertNotIn("os.unlink(", source)

    def test_windows_script_checks_ue_and_requires_manual_landscape_import(self):
        contents = (ROOT / "scripts/ue5/bootstrap-draft-landscape.ps1").read_text(encoding="utf-8")
        self.assertIn("UnrealEditor-Cmd.exe", contents)
        self.assertIn("generate-playtest-terrain.py", contents)
        self.assertIn("--verify-only", contents)
        self.assertIn("-ExecutePythonScript=", contents)
        self.assertIn("Import from File:", contents)
        self.assertIn("1587.301587", contents)

    def test_ignore_cache_and_track_binary_levels_with_git_lfs(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        for name in ["unreal/Binaries/", "unreal/Intermediate/", "unreal/Saved/",
                     "unreal/TerrainSource/", "unreal/TerrainPreview/"]:
            self.assertIn(name, gitignore)
        for extension in ["*.umap", "*.uasset"]:
            self.assertIn(extension + " filter=lfs diff=lfs merge=lfs -text", attributes)


if __name__ == "__main__":
    unittest.main()
