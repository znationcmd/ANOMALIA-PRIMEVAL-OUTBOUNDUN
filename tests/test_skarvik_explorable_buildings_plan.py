"""Source-only verification: plan is not confused with playable interiors."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"public/config/skarvik-explorable-buildings.json"
class TestSkarvikExplorableBuildingPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(SPEC.read_text(encoding="utf-8"))
    def test_unimplemented_state_and_protected_world(self):
        self.assertEqual(self.data["world"],"SKARVIK")
        self.assertEqual(self.data["developmentState"],"DESIGN_ONLY_NOT_INSTALLED")
        self.assertTrue(self.data["accessStrategy"]["allBuildingsExplorableTarget"])
        self.assertTrue(any("DRAZOVIA" in x for x in self.data["prohibited"]))
        self.assertIn("fitted doors on City Sample facades",self.data["unverifiedOrMissing"])
    def test_real_interiors_required(self):
        required={"house","apartment","retail","civic","industrial","subterranean"}
        self.assertEqual(required,{row["id"] for row in self.data["categories"]})
        for row in self.data["categories"]:
            self.assertGreater(len(row["requiredRooms"]),0)
            self.assertGreater(len(row["loot"]),0)
        for x in ["actualDoorwayAndTraversableRooms","noInvisibleWalls","streamedWithoutTeleport",
                  "persistenceAfterReload","PIEAndPackagedVerified"]:
            self.assertTrue(self.data["acceptBeforeClaim"][x])
    def test_optimized_not_guaranteed(self):
        self.assertIn("Intel Iris Xe",self.data["accessStrategy"]["qualityTarget"])
        self.assertTrue(self.data["accessStrategy"]["noTeleportsForNormalDoors"])
        self.assertTrue(self.data["accessStrategy"]["scalableHighriseRule"])
if __name__=="__main__":
    unittest.main()
