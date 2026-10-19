"""Fast deterministic checks for the Unreal heightmap source generator."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ue5/generate-terrain.py"
spec = importlib.util.spec_from_file_location("terrain_source", SCRIPT)
terrain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(terrain)

class TerrainSourceTests(unittest.TestCase):
    def test_map_measurement_exceeds_land_target_and_is_48km(self):
        metrics = terrain.generate(Path("unused"), measure_only=True)
        self.assertEqual(metrics["worldWidthKm"], 48)
        self.assertEqual(metrics["totalAreaKm2"], 2304)
        self.assertGreater(metrics["dryLandKm2SampledAt25m"], 300)
        self.assertEqual(metrics["heightmapResolution"], 1009)

    def test_adjacent_heightmap_edges_match_exactly(self):
        x = np.array([[-4000.0, 0.0, 4000.0]], dtype=np.float32)
        y = np.array([[12000.0, 12000.0, 12000.0]], dtype=np.float32)
        left, _ = terrain.height_at(x[:, :2], y[:, :2])
        right, _ = terrain.height_at(x[:, 1:], y[:, 1:])
        self.assertEqual(float(left[0, -1]), float(right[0, 0]))
        a, b = terrain.encode_height(left), terrain.encode_height(right)
        self.assertEqual(int(a[0, -1]), int(b[0, 0]))

    def test_raw_encoding_is_little_endian_unsigned_16_bit(self):
        encoded = terrain.encode_height(np.array([-512.0, 0.0, 512.0]))
        self.assertEqual(encoded.dtype, np.dtype("<u2"))
        self.assertEqual(encoded.tolist(), [0, 32768, 65535])
