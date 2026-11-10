"""Read-only next-stage SKARVIK city, roads and coastal-settlement tests."""
import importlib.util
from pathlib import Path
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/plan_skarvik_continuity_next_batch.py"
spec=importlib.util.spec_from_file_location("skarvik_continuity",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SkarvikCoastTests(unittest.TestCase):
    def test_actual_native_source_masterplan_is_preserved(self):
        master,h1=mod.read(mod.MASTER)
        coast,h2=mod.read(mod.COAST)
        original_master=mod.MASTER.read_bytes()
        original_coast=mod.COAST.read_bytes()
        result=mod.plan(master,coast)
        self.assertEqual(result["worldSizeKm"],[48,48])
        self.assertEqual(result["existingSettlements"],125)
        self.assertEqual(result["relocationsPendingManualApproval"],67)
        self.assertEqual(result["regionalRoadsInMasterplan"],382)
        self.assertEqual(result["routeRecordsWithoutGeometry"],137)
        self.assertTrue(result["originalCoastalUnrealWorldsPreserved"])
        self.assertEqual(len(result["allSettlements"]),125)
        self.assertEqual(len(result["allRoadChecks"]),382)
        self.assertFalse(result["SM5PIEValidated"])
        self.assertFalse(result["finalCoastalMapChanged"])
        self.assertTrue(all(not a["approvedForNativeWriting"] for a in
                            result["allSettlements"]))
        self.assertEqual(mod.MASTER.read_bytes(),original_master)
        self.assertEqual(mod.COAST.read_bytes(),original_coast)

    def test_only_a_new_isolated_output_is_written(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/"brand-new"
            report=mod.generate(mod.MASTER,mod.COAST,out)
            self.assertEqual(report["sourceSHA256"]["worldPlan"],
                             mod.read(mod.MASTER)[1])
            files={p.name for p in out.iterdir()}
            self.assertEqual(files,{"skarvik-next-native-survey.json",
                                    "skarvik-relocations-review.csv",
                                    "skarvik-road-endpoint-gaps.csv"})
            self.assertEqual(len((out/"skarvik-relocations-review.csv").read_text(
                  encoding="utf-8-sig").splitlines()),68)
            self.assertEqual(len((out/"skarvik-road-endpoint-gaps.csv").read_text(
                  encoding="utf-8-sig").splitlines()),383)
            with self.assertRaises(FileExistsError):
                mod.generate(mod.MASTER,mod.COAST,out)

    def test_real_city_sample_footprint_never_moves(self):
        master,_=mod.read(mod.MASTER)
        coast,_=mod.read(mod.COAST)
        master["citySample"]["cityCenterKm"]=[-2,-8]
        with self.assertRaisesRegex(ValueError,"City Sample"):
            mod.plan(master,coast)

    def test_distinct_skarvik_y_axis_convention(self):
        self.assertEqual(mod.world_to_cm([2,-8]),[200000,800000])
        self.assertTrue(mod.rect_overlaps([2,-8],[4,4],[3,-8],[1,1]))
        self.assertFalse(mod.rect_overlaps([2,-8],[4,4],[18,18],[1,1]))


if __name__=="__main__":
    unittest.main()
