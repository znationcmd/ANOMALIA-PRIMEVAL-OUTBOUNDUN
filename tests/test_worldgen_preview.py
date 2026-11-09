"""Native-free tests for deterministic, isolated ANOMALIA'Z worldgen previews."""
from __future__ import annotations

import importlib.util
import json
import struct
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "ue5" / "worldgen" / "preview_world.py"
spec = importlib.util.spec_from_file_location("anomalia_preview_world", MODULE)
worldgen = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(worldgen)


class WorldgenPreviewTests(unittest.TestCase):
    def test_four_started_world_profiles(self):
        profiles = worldgen.load_profiles()
        for wid, km in [("racconia-varkovia", 16), ("unknown-horror-x", 20),
                        ("skarvik", 48), ("drazovia", 48)]:
            self.assertIn(wid, profiles)
            self.assertEqual(profiles[wid]["widthKm"], km)

    def test_reproducible_seed_and_density(self):
        profile = worldgen.load_profiles()["racconia-varkovia"]
        a = worldgen.generate_plan(profile, grid=32)
        b = worldgen.generate_plan(profile, grid=32)
        self.assertEqual(a, b)
        self.assertAlmostEqual(a["previewLandFraction"], 0.65, delta=0.002)
        self.assertEqual(a["density"], 0.65)
        self.assertEqual(a["pcgCandidateCells"], round(a["pcgEligibleCells"] * 0.65))
        self.assertFalse(a["nativeUE5MapGenerated"])
        self.assertFalse(a["originalWorldModified"])
        c = worldgen.generate_plan(profile, grid=32, seed_override="different-seed")
        self.assertNotEqual(a["biomes"], c["biomes"])

    def test_started_maps_remain_synthetic_preview_and_untouched(self):
        for wid in ("unknown-horror-x", "skarvik", "drazovia"):
            p = worldgen.generate_plan(worldgen.load_profiles()[wid], grid=32)
            self.assertIn("synthetic", p["warnings"][0].lower())
            self.assertEqual(p["terrainPolicy"].startswith("preserve"), True)
            self.assertFalse(p["nativePCGBaked"])
            self.assertTrue(p["roads"] is not None)

    def test_road_cells_only_on_preview_land(self):
        p = worldgen.generate_plan(worldgen.load_profiles()["racconia-varkovia"], grid=32)
        for r in p["roads"]:
            for x, y in r["cells"]:
                self.assertNotEqual(p["biomes"][y * p["grid"] + x], "ocean")

    def test_protected_actor_blocks_scatter_and_roads(self):
        profile = worldgen.load_profiles()["racconia-varkovia"]
        protected = [{"id": "Existing hospital", "xMeters": 0, "yMeters": 0,
                      "radiusMeters": 2800}]
        plan = worldgen.generate_plan(profile, grid=32, protected=protected)
        self.assertEqual(plan["protectedActorIds"], ["Existing hospital"])
        blocked = set(plan["protectedCells"])
        self.assertTrue(blocked)
        self.assertFalse(blocked.intersection(plan["scatterIndices"]))
        for r in plan["roads"]:
            for x, y in r["cells"]:
                self.assertNotIn(y * 32 + x, blocked)

    def test_existing_r16_is_sampled_readonly(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "existing.r16"
            # 33 x 33 ORIGINAL samples; left half land, right half sea.
            raw = b"".join(struct.pack("<H", 40000 if x < 16 else 21000)
                           for y in range(33) for x in range(33))
            source.write_bytes(raw)
            cells, checksum, size = worldgen.sample_existing_r16(source, 32, 32768)
            self.assertEqual(size, 33)
            self.assertEqual(len(cells), 16*32)
            plan = worldgen.generate_plan(
                worldgen.load_profiles()["drazovia"], 32,
                source_land_cells=cells, source_sha=checksum, source_resolution=size)
            self.assertEqual(plan["sourceR16HashSha256"], checksum)
            self.assertAlmostEqual(plan["previewLandFraction"], .5)
            self.assertEqual(source.read_bytes(), raw)
            self.assertIn("read-only", plan["warnings"][0])
            self.assertFalse(plan["originalWorldModified"])

    def test_protection_schema_rejects_invalid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "protected.json"
            path.write_text(json.dumps({"schemaVersion": 1, "protected": [
                {"id": "A", "xMeters": 0, "yMeters": 0, "radiusMeters": -1}]}))
            with self.assertRaisesRegex(ValueError, "Negative"):
                worldgen.load_protected(path)

    def test_staging_never_overwrites_outputs(self):
        plan = worldgen.generate_plan(worldgen.load_profiles()["racconia-varkovia"], grid=32)
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "new-run"
            result = worldgen.write_isolated(plan, dest)
            self.assertEqual(len(result), 2)
            self.assertTrue((dest / "preview.ppm").read_bytes().startswith(b"P6\n"))
            with self.assertRaises(FileExistsError):
                worldgen.write_isolated(plan, dest)
            with self.assertRaisesRegex(ValueError, "OUTSIDE"):
                worldgen.write_isolated(plan, ROOT / "GeneratedWorlds" / "test")

if __name__ == "__main__":
    unittest.main()
