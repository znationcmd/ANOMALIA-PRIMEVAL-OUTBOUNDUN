"""Source-only tests; never launch Unreal or alter existing worlds."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class WorldRealismSafetyTest(unittest.TestCase):
    def test_two_stable_public_names(self):
        names = module("map_titles", ROOT / "scripts/ue5/map_titles.py").load_titles()
        self.assertEqual(set(names), {"archipelago-v2", "inhabited-v2", "karskov-v1", "vorgrad-v1", "nemoris-v1", "drakheim-v1", "solynacalyra-v1", "nexavarkhos-v1"})
        self.assertEqual(names["archipelago-v2"], "SKARVIK")
        self.assertEqual(names["inhabited-v2"], "DRAZOVIA")
        for world in ("KARSKOV", "VORGRAD", "NEMORIS", "DRAKHEIM", "SOLYNACALYRA", "NEXAVARKHOS"):
            self.assertEqual(names[world.lower()+"-v1"], world)

    def test_catalog_names_cannot_change_world_identity(self):
        validator = module("map_titles", ROOT / "scripts/ue5/map_titles.py")
        raw = json.loads(validator.CATALOG.read_text(encoding="utf-8"))
        raw["maps"][0]["displayName"] = "Nouveau nom public"
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "maps.json"
            file.write_text(json.dumps(raw), encoding="utf-8")
            self.assertEqual(validator.load_titles(file)["archipelago-v2"], "Nouveau nom public")
            raw["maps"][0]["saveNamespace"] = "some-other-world"
            file.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ValueError):
                validator.load_titles(file)

    def test_native_pipeline_stays_opt_in(self):
        runner = module("inhabited_realism", ROOT / "scripts/ue5/run_inhabited_realism.py")
        with tempfile.TemporaryDirectory() as directory:
            result = runner.main(["--engine-root", directory,
                                  "--output", str(Path(directory) / "output")])
            self.assertEqual(result, 0)
            self.assertFalse((Path(directory) / "output").exists())
            names = [name for name, _ in runner.commands(Path(directory),
                                                           Path(directory) / "output")]
            self.assertEqual(names, ["residential-upgrade", "residential-audit",
                                     "urban-greenery", "real-gpu-review"])

    def test_missing_unreal_world_rejected_before_editing(self):
        runner = module("inhabited_realism2", ROOT / "scripts/ue5/run_inhabited_realism.py")
        with self.assertRaises(RuntimeError):
            runner.preflight(Path("/path/without/an/unreal/installation"))


if __name__ == "__main__":
    unittest.main()
