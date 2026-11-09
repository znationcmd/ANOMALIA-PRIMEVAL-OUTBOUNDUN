"""Test SKJÆRØYÅS's faithful RAW16 merge and UE5 staging data."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"scripts"/"ue5"/"worldgen"
sys.path.insert(0,str(GEN))
import generate_skjaeroyaas as source
import prepare_skjaeroyaas_import as prep

EDITOR=ROOT/"unreal"/"EditorPython"/"stage_skjaeroyaas_world.py"
spec=importlib.util.spec_from_file_location("stage_skjaeroyaas_world",EDITOR)
stage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class SkjaeroyaasImportTests(unittest.TestCase):
    def test_source_to_import_without_overwriting(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/"original-tiles"
            b=Path(t)/"new-ue5-import"
            source.generate(a, samples_per_tile=33, preview_size=64)
            before={p.name:p.read_bytes() for p in a.iterdir()}
            report=prep.prepare(a,b)
            self.assertEqual(report["resolution"],[97,97])
            self.assertEqual(report["heightmapBytes"],97*97*2)
            self.assertEqual(report["villageMarkers"],6)
            self.assertEqual(report["roadCandidates"],5)
            self.assertGreater(report["forestAnchorCandidates"],10)
            self.assertFalse(report["isNativeUnrealLevel"])
            self.assertFalse(report["hasRoadSplines"])
            self.assertFalse(report["hasBuildings"])
            layout=stage.check_layout(b/"skjaeroyaas-layout.json")
            self.assertEqual(layout["name"],"SKJÆRØYÅS")
            self.assertEqual(len(layout["villages"]),6)
            result=stage.create_new_partitioned_staging_level(
                b/"skjaeroyaas-layout.json", confirm_create=False)
            self.assertTrue(result["dryRun"])
            self.assertEqual(result["level"],"/Game/Maps/SKJAEROYAAS_15KM_STAGE")
            self.assertEqual({p.name:p.read_bytes() for p in a.iterdir()},before)
            with self.assertRaises(FileExistsError):
                prep.prepare(a,b)

    def test_stitched_sample_values(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/"a",Path(t)/"b"
            source.generate(a,samples_per_tile=33,preview_size=64)
            prep.prepare(a,b)
            joined=(b/"SKJAEROYAAS_97x97.r16").read_bytes()
            n=33
            size=97
            # The overlapping tile borders appear exactly ONCE in mosaic.
            for col,row in [(0,0),(1,0),(2,1),(2,2)]:
                original=(a/f"height_x{col}_y{row}.r16").read_bytes()
                for localx,localy in [(0,0),(n-1,0),(0,n-1),(n-1,n-1)]:
                    gx=col*(n-1)+localx
                    gy=row*(n-1)+localy
                    self.assertEqual(
                        joined[2*(gy*size+gx):2*(gy*size+gx+1)],
                        original[2*(localy*n+localx):2*(localy*n+localx+1)]
                    )

    def test_corrupt_original_tile_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/"a"
            source.generate(a,samples_per_tile=33,preview_size=64)
            p=a/"height_x0_y1.r16"
            content=bytearray(p.read_bytes())
            content[0]^=1
            p.write_bytes(content)
            with self.assertRaisesRegex(ValueError,"SHA256"):
                prep.prepare(a,Path(t)/"b")
            self.assertFalse((Path(t)/"b").exists())

    def test_unknown_layout_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            doc=Path(t)/"wrong.json"
            doc.write_text(json.dumps({"schemaVersion":1,"worldId":"skarvik",
                                       "dimensionsKm":[48,48]}),encoding="utf-8")
            with self.assertRaises(ValueError):
                stage.check_layout(doc)


if __name__=="__main__":
    unittest.main()
