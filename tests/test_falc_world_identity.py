import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
from falc_world_plan import world_plan

class FalcWorldTests(unittest.TestCase):
    def test_tenth_map_is_independent_and_not_falsely_ready(self):
        rows=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        self.assertEqual(len(rows),10)
        self.assertEqual(len({x["id"] for x in rows}),10)
        self.assertEqual(len({x["saveNamespace"] for x in rows}),10)
        self.assertEqual(len({x["originalUnrealPackage"] for x in rows}),10)
        w=next(x for x in rows if x["id"]=="falc-v1")
        self.assertEqual(w["originalUnrealPackage"],"/Game/Maps/PRIGIMALIA_FALC")
        self.assertEqual(w["displayName"],"F.A.L.C")
        self.assertFalse(w["serverSelectable"])
        self.assertEqual(w["widthKm"],26.5)
        self.assertEqual(w["heightKm"],26.5)
    def test_real_area_and_image_reference_integrity(self):
        p=world_plan()
        self.assertEqual(p["totalKm2"],702.25)
        self.assertEqual(p["targetLandKm2"],500.)
        self.assertEqual(p["targetWaterKm2"],202.25)
        self.assertEqual(p["inputReference"],"user-current-message-fused-topography-for-FALC")
        self.assertEqual(p["referenceMustNotBeReplacedBy"],"DRAZOVIA-topography")
        self.assertFalse(p["nativeLandscapeCreated"])
        self.assertFalse(p["binaryR16GeneratedFromThisReference"])
        self.assertFalse(p["drazoviaModified"])

if __name__=="__main__":unittest.main()
