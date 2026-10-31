"""Regression guards for the isolated DRAZOVIA native V3 heightmap import.

V1 and V2 lost root LandscapeComponents after their ChangeGridSize() call.
V3 must validate all 576 real components and save the new .umap BEFORE
any World Partition landscape proxy redistribution is attempted.
This test checks repository source; a green test is NOT a native UE5 import.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CPP=ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.cpp"
HDR=ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.h"
PY=ROOT/"unreal/Scripts/create_drazovia_izurvive_candidate_v3.py"
WINDOWS=ROOT/"scripts/windows/import_drazovia_new_native_v3.ps1"
PACKAGE="/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate"
SHA="704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c"

class DrazoviaV3SafetyTests(unittest.TestCase):
    def test_v3_cpp_import_preserves_components_until_save(self):
        content=CPP.read_text(encoding="utf-8")
        marker="AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateDrazoviaIzurviveCandidateV3Landscape()"
        self.assertIn(marker,content)
        part=content.split(marker,1)[1].split(
            "int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectDrazoviaIzurviveCandidateV3Components(",1)[0]
        self.assertIn('TEXT("'+PACKAGE+'")',part)
        self.assertIn("DRAZOVIA_NEW_TOPO_48KM_3025.r16",part)
        self.assertIn("Land->LandscapeComponents.Num()!=576",part)
        self.assertIn("Land->CreateLandscapeInfo()",part)
        self.assertNotIn("Subsystem->ChangeGridSize(",part)
        self.assertNotIn("ANOMALIA_Inhabited_v2",part)
    def test_v3_inspection_native_576(self):
        content=CPP.read_text(encoding="utf-8")
        marker="int32 UAnomaliaZPrigimaliaWorldImportLibrary::InspectDrazoviaIzurviveCandidateV3Components("
        self.assertIn(marker,content)
        part=content.split(marker,1)[1].split(
            "AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape()",1)[0]
        self.assertIn("Land->LandscapeComponents.Num()",part)
        self.assertIn("GetLandscapeInfo()",part)
        self.assertIn("N!=576",part)
        self.assertIn(PACKAGE,part)
        self.assertIn("CreateDrazoviaIzurviveCandidateV3Landscape",HDR.read_text())
    def test_v3_python_stays_isolated_and_verifies_raw(self):
        source=PY.read_text(encoding="utf-8")
        compile(source,str(PY),"exec")
        self.assertIn(SHA,source)
        self.assertIn("v3-first-import.json",source)
        self.assertIn("is_partitioned_world=True",source)
        self.assertIn("inspect_drazovia_izurvive_candidate_v3_components",source)
        self.assertIn("landscapeGridPartitioningDeferred",source)
        self.assertIn("before!=after",source)
        self.assertIn("Candidate map already exists",source)
        self.assertIn(PACKAGE,source)
    def test_windows_does_not_overwrite_old_map_or_earlier_candidates(self):
        s=WINDOWS.read_text(encoding="utf-8")
        self.assertIn("D:\\ANOMALIAZ-PRIGIMALIA",s)
        self.assertIn("D:\\ANOMALIA",s)
        self.assertIn("CreateDrazoviaIzurviveCandidateV3Landscape",s)
        self.assertIn("InspectDrazoviaIzurviveCandidateV3Components",s)
        self.assertIn("v3-first-import.json",s)
        self.assertIn("v3",s)
        self.assertIn("Get-FileHash",s)
        self.assertIn("refusing overwrite",s)
        self.assertNotIn("NewReferenceV2_Candidate.umap",s)
        self.assertNotIn("unreal-import.log",s)

if __name__=="__main__":
    unittest.main()
