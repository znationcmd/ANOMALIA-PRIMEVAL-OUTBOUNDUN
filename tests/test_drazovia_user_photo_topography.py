"""DRAZOVIA 48 km photo-driven geography and non-destructive UE candidate tests."""
import unittest
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DrazoviaTopoSourceTest(unittest.TestCase):
    def test_unchanged_main_world_catalog(self):
        rows=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        world=next(i for i in rows if i["displayName"]=="DRAZOVIA")
        self.assertEqual(world["id"],"inhabited-v2")
        self.assertEqual(world["originalUnrealPackage"],"/Game/Maps/ANOMALIA_Inhabited_v2")
        self.assertEqual(world["widthKm"]*world["heightKm"],2304)
        self.assertEqual(len(rows),9)
    def test_safe_candidate_only_does_not_replace_skarvik(self):
        cpp=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.cpp").read_text()
        header=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.h").read_text()
        self.assertIn("CreateDrazoviaTopoCandidateLandscape",cpp)
        self.assertIn("CreateDrazoviaTopoCandidateLandscape",header)
        self.assertIn('World->GetPackage()->GetName()!=TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_Candidate")',cpp)
        self.assertIn('TEXT("DRAZOVIA"),TEXT("DRAZOVIA.r16")',cpp)
        self.assertIn('int64(Size)*int64(Size)*2',cpp)
        self.assertIn("Land->LandscapeComponents.Num()!=576",cpp)
    def test_real_user_image_manifest_and_source_lengths(self):
        data=json.loads((ROOT/"public/config/drazovia-photo-topography-audit.json").read_text())
        self.assertEqual(data["referencePhotoSha256"],"d31548b922e251ca06e06cb2d05359089685932e347a6237bb3f8e1782ca4222")
        self.assertEqual(data["sourceR16Sha256"],"42a7c9a38bfc3748bc8a6f8182354831a063875a405ba5b2cba53003e5dc9120")
        self.assertEqual(data["sourceBytes"],3025**2*2)
        self.assertEqual(data["mapAreaKm2"],2304)
        self.assertFalse(data["unrealNativeCandidateValidated"])
        self.assertFalse(data["originalDrazoviaReplaced"])
        self.assertEqual(round(data["landKm2"]+data["seaKm2"]),2304)
    def test_safe_drazovia_script_protects_both_live_worlds(self):
        script=(ROOT/"unreal/Scripts/create_drazovia_topo_candidate.py").read_text()
        self.assertIn('ANOMALIA_Inhabited_v2.umap',script)
        self.assertIn('ANOMALIA_Archipelago_v2.umap',script)
        self.assertIn('EXPECTED_SHA256=',script)
        self.assertIn('create_drazovia_topo_candidate_landscape()',script)
        self.assertIn("before!=after",script)
        self.assertIn("not level.new_level(PACKAGE,is_partitioned_world=True)",script)
        self.assertIn("newNativeMapProduced",json.dumps(json.loads((ROOT/"public/config/drazovia-photo-topography-audit.json").read_text())))
if __name__=="__main__":unittest.main()
