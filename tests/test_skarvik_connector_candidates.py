"""Real 48×48km SKARVIK coastal road connector source QA."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"scripts/skarvik_design_missing_connectors.py"
spec=importlib.util.spec_from_file_location("skarvik_connector_stage",FILE)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SourceRoadChecks(unittest.TestCase):
    def test_approved_existing_48km_towns_and_roads(self):
        master,_=audit._read(audit.ORIGINAL)
        coast,_=audit._read(audit.COAST)
        result=audit.propose(master,coast)
        self.assertEqual(result["existingTownCount"],125)
        self.assertEqual(result["regionalRoutes"],382)
        self.assertEqual(result["unapprovedCoastalRelocations"],67)
        self.assertEqual(result["routesWithoutPolyline"],137)
        self.assertEqual(result["routesDisconnectedBeyond250M"],236)
        self.assertTrue(result["citySample4KmPreserved"])
        self.assertEqual(result["offshoreIslandsPreserved"],7)
        self.assertEqual(result["roadMeshesAdded"],0)
        self.assertFalse(result["nativeLandscapeModified"])
        self.assertFalse(result["PIEOrSM5DriveTestPassed"])
        self.assertGreater(len(result["allConnectorCandidates"]),236)
        self.assertTrue(all(not x["approvedForNativeAsphaltBuild"] for x in
                        result["allConnectorCandidates"]))
        self.assertEqual(audit.to_ue_cm([2,-8]),[200000,800000])

    def test_source_maps_immutable_and_output_separate(self):
        master=audit.ORIGINAL.read_bytes()
        coast=audit.COAST.read_bytes()
        with tempfile.TemporaryDirectory() as root:
            out=Path(root)/"new-proposals"
            result=audit.stage(audit.ORIGINAL,audit.COAST,out)
            self.assertEqual(len(result["allConnectorCandidates"])+1,
              len((out/"skarvik-all-connector-review.csv").read_text(
                encoding="utf-8-sig").splitlines()))
            self.assertEqual(len(result["first20SurveyCandidates"])+1,
              len((out/"skarvik-first20-native-checks.csv").read_text(
                encoding="utf-8-sig").splitlines()))
            with self.assertRaises(FileExistsError):
                audit.stage(audit.ORIGINAL,audit.COAST,out)
        self.assertEqual(audit.ORIGINAL.read_bytes(),master)
        self.assertEqual(audit.COAST.read_bytes(),coast)

    def test_refuse_city_sample_relocation(self):
        master,_=audit._read(audit.ORIGINAL)
        coast,_=audit._read(audit.COAST)
        master["citySample"]["cityCenterKm"]=[20,-8]
        with self.assertRaisesRegex(ValueError,"City Sample"):
            audit.propose(master,coast)

if __name__=="__main__":
    unittest.main()
