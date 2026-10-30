"""Source-level tests for the independent 100 km native Landscape import."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
    sys.path.insert(0,str(ROOT/"scripts/ue5"))
    spec=importlib.util.spec_from_file_location(name,str(ROOT/path))
    x=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(x)
    return x

class ChernaskaluxriaNativeSourceTests(unittest.TestCase):
    def test_small_raw_sources_have_exact_matching_shared_edges(self):
        creator=module("ch_base_raw",Path("scripts/ue5/generate_chernaskaluxria_tiles.py"))
        self.assertEqual(creator.BASE_SAMPLES,253)
        self.assertEqual(creator.EXPECTED_BYTES,253*253*2)
        self.assertEqual(creator.METRES_PER_SAMPLE,5000/252)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            values=creator.generate(p,[(10,10),(11,10),(10,11)])
            self.assertEqual(len(values["tiles"]),3)
            self.assertEqual(creator.check_shared_edges(p,10,10),{"east":True,"south":True})
            for x in values["tiles"]:
                self.assertEqual((p/x["filename"]).stat().st_size,253*253*2)
            # Existing sources can be re-verified, but must never be overwritten.
            self.assertEqual(creator.generate(p,[(10,10)])["tiles"][0]["sha256"],
                             values["tiles"][0]["sha256"])
            with (p/"CHERNASKALUXRIA_x10_y10.r16").open("r+b") as fd:
                fd.seek(20)
                fd.write(b"\x00\x00\x00")
            with self.assertRaises(FileExistsError):
                creator.generate(p,[(10,10)])

    def test_editor_only_native_creator_never_merges_worlds(self):
        cpp=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.cpp").read_text()
        header=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.h").read_text()
        python=(ROOT/"unreal/Scripts/create_chernaskaluxria_native.py").read_text()
        self.assertIn("CreateChernaskaluxriaLandscapeTile(int32 Col,int32 Row)",header)
        self.assertIn('World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA")',cpp)
        self.assertIn("Land->LandscapeComponents.Num()!=4",cpp)
        self.assertIn("ALandscape* Land=World->SpawnActor<ALandscape>()",cpp)
        self.assertIn("new_level(PACKAGE,is_partitioned_world=True)",python)
        self.assertIn("Native C++ landscape import failed",python)
        self.assertIn("Existing world preserved; never recreate or overwrite",python)
        self.assertIn("NATIVE_PARTIAL_WORLD_SAVED_NOT_PLAYTESTED",python)
        self.assertIn('"completedNativeTiles=1"',python.replace('completedNativeTiles=1','"completedNativeTiles=1"'))

    def test_any_actual_world_retains_unique_identity(self):
        maps=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        self.assertEqual(len(maps),10)
        self.assertEqual(len({x["originalUnrealPackage"] for x in maps}),10)
        self.assertEqual(len({x["saveNamespace"] for x in maps}),10)
        own=next(x for x in maps if x["id"]=="chernaskaluxria-v1")
        self.assertEqual(own["originalUnrealPackage"],"/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA")
        self.assertFalse(own["serverSelectable"])

if __name__=="__main__":
    unittest.main()
