"""Checks for ORIGINAL SKJÆRØYÅS 15x15 km Landscape source generation."""
import importlib.util
import json
import math
import struct
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "ue5" / "worldgen" / "generate_skjaeroyaas.py"
spec = importlib.util.spec_from_file_location("skjaeroyaas_terrain", MODULE)
generator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(generator)


def tile_data(base: Path, x: int, y: int, n: int) -> bytes:
    data = (base / f"height_x{x}_y{y}.r16").read_bytes()
    assert len(data) == n*n*2
    return data


class NorwegianWorldTests(unittest.TestCase):
    def test_registry_preserves_20_plus_three(self):
        core = json.loads((ROOT / "config/worldgen/worlds.json").read_text(encoding="utf-8"))
        more = json.loads((ROOT / "config/worldgen/expansion-worlds.json").read_text(encoding="utf-8"))
        self.assertEqual(len(core["worlds"]), 20)
        self.assertEqual(len(more["worlds"]), 3)
        self.assertEqual({m["name"] for m in more["worlds"]},
                         {"UNKNOWN HORROR X", "KÖNIGSBRÜCK", "SKJÆRØYÅS"})
        self.assertAlmostEqual(sum(m["areaKm2"] for m in core["worlds"] + more["worlds"]), 25865.18)
        self.assertEqual(more["worlds"][-1]["areaKm2"], 225)
        profiles = json.loads((ROOT / "config/worldgen/starter-worlds.json").read_text(encoding="utf-8"))
        self.assertIn("skjaeroyaas", [p["worldId"] for p in profiles["profiles"]])

    def test_original_heightfield_has_sea_and_snow(self):
        self.assertLess(generator.terrain(7500, 7500), 0)
        self.assertGreater(generator.terrain(-4200, 2800), 800)
        self.assertEqual(generator.encode_height(0), 32768)
        self.assertEqual(generator.encode_height(100), 34368)
        self.assertEqual(generator.SEED, "ANOMALIA-2026-SKJAEROYAAS")

    def test_seamless_tiles_and_protected_output(self):
        with tempfile.TemporaryDirectory() as base:
            target = Path(base) / "new-map"
            manifest = generator.generate(target, samples_per_tile=33, preview_size=64)
            self.assertEqual(manifest["dimensionsKm"], [15, 15])
            self.assertEqual(manifest["tileGrid"], [3, 3])
            self.assertEqual(len(manifest["tiles"]), 9)
            self.assertFalse(manifest["terrainCreatedInUnreal"])
            self.assertFalse(manifest["nativeLevelPackaged"])
            self.assertTrue((target / "skjaeroyaas-overview.png").read_bytes().startswith(
                b"\x89PNG\r\n\x1a\n"))
            self.assertTrue(0.58 < manifest["previewLandFraction"] < 0.67)
            n = 33
            for y in range(3):
                for x in range(3):
                    current = tile_data(target, x, y, n)
                    if x < 2:
                        adjacent = tile_data(target, x+1, y, n)
                        # East edge of (x,y) == west edge of (x+1,y)
                        for row in range(n):
                            self.assertEqual(current[(row*n+n-1)*2:(row*n+n)*2],
                                             adjacent[(row*n)*2:(row*n+1)*2])
                    if y < 2:
                        adjacent = tile_data(target, x, y+1, n)
                        # South edge of (x,y) == north edge of (x,y+1)
                        self.assertEqual(current[-n*2:], adjacent[:n*2])
            with self.assertRaises(FileExistsError):
                generator.generate(target, samples_per_tile=33, preview_size=64)
            with self.assertRaisesRegex(ValueError, "OUTSIDE"):
                generator.generate(ROOT / "TEMP-SKJAEROYAAS-NEVER-CREATE",
                                   samples_per_tile=33, preview_size=64)

    def test_valid_raw16_encoding_range(self):
        for x,y in [(-7500,-7500),(-2000,-4000),(7500,7500),(-4200,2800)]:
            height = generator.terrain(x,y)
            encoded = generator.encode_height(height)
            self.assertTrue(0 <= encoded <= 65535)
            reconstructed = (encoded-32768)*generator.Z_SCALE_CM/12800.0
            self.assertAlmostEqual(height, reconstructed, delta=0.04)

if __name__ == "__main__":
    unittest.main()
