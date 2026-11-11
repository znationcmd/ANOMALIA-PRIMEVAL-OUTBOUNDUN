"""ANOMALIA draft terrain verification: math, seams and non-destructive writes."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ue5/generate-playtest-terrain.py"
spec = importlib.util.spec_from_file_location("anomalia_draft", SCRIPT)
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


class PlaytestLandscapeTests(unittest.TestCase):
    def test_draft_is_lower_cost_than_high_detail_source(self):
        info = draft.metadata({"tilesVerified": 144, "seamsVerified": 264})
        self.assertEqual(info["worldMeters"], [48000, 48000])
        self.assertEqual(info["tiles"], [12, 12])
        self.assertEqual(info["heightmapResolution"], [253, 253])
        self.assertEqual(info["totalLandscapeComponents"], 576)
        self.assertAlmostEqual(info["expectedHorizontalCoverageMeters"], 48000, places=5)
        self.assertEqual(info["recommendedImportScaleCm"]["z"], 200)

    def test_adjacent_tiles_match_for_every_border_sample(self):
        a = draft.edges(draft.tile_bytes(0, 0))
        east = draft.edges(draft.tile_bytes(1, 0))
        south = draft.edges(draft.tile_bytes(0, 1))
        self.assertEqual(len(draft.tile_bytes(0, 0)), 253 * 253 * 2)
        self.assertEqual(a[3], east[2], "east/west tiles must have identical height samples")
        self.assertEqual(a[1], south[0], "north/south tiles must have identical height samples")

    def test_save_resume_and_reject_different_existing_heightmap(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for y in range(2):
                for x in range(2):
                    self.assertTrue(draft.save_tile(folder, x, y))
                    self.assertFalse(draft.save_tile(folder, x, y))
            result = draft.verify_tiles(folder, cols=2, rows=2)
            self.assertEqual(result["tilesVerified"], 4)
            self.assertEqual(result["seamsVerified"], 4)
            original = (folder / draft.tile_name(0, 0)).read_bytes()
            (folder / draft.tile_name(0, 0)).write_bytes(b"do not silently replace")
            with self.assertRaisesRegex(ValueError, "NOT replaced"):
                draft.save_tile(folder, 0, 0)
            with self.assertRaisesRegex(ValueError, "byte count"):
                draft.verify_tiles(folder, cols=2, rows=2)
            self.assertEqual((folder / draft.tile_name(0, 0)).read_bytes(), b"do not silently replace")
            self.assertNotEqual(original, b"do not silently replace")

    def test_reject_missing_or_invalid_coordinates(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "Missing"):
                draft.verify_tiles(Path(temp), cols=1, rows=1)
        with self.assertRaises(ValueError):
            draft.tile_name(-1, 0)
        with self.assertRaises(ValueError):
            draft.tile_name(12, 0)


if __name__ == "__main__":
    unittest.main()
