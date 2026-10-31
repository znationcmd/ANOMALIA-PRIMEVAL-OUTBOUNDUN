"""Guard DRAZOVIA newer reference; source photo/R16 are in user-owned conversation ZIP."""
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"public/config/drazovia-izurvive-new-reference-audit.json"
CPP=ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.cpp"
HDR=ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.h"
AUTHOR=ROOT/"unreal/Scripts/create_drazovia_izurvive_candidate.py"
class DrazoviaIzurviveSourceTest(unittest.TestCase):
 def test_new_reference_not_confused_with_old_candidate(self):
  doc=json.loads(AUDIT.read_text())
  self.assertEqual(doc["mapId"],"inhabited-v2")
  self.assertEqual(doc["sideKm"],48)
  self.assertEqual(doc["areaKm2"],2304)
  self.assertEqual(doc["raw16Bytes"],3025*3025*2)
  self.assertEqual(doc["sourceImageName"],"IMG_8278.jpeg")
  self.assertEqual(doc["raw16Sha256"],"704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c")
  self.assertEqual(doc["newCandidateMap"],"/Game/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate")
  self.assertNotEqual(doc["newCandidateMap"],doc["preservedOriginalMap"])
  self.assertFalse(doc["candidateNativeUmapProduced"])
  self.assertFalse(doc["gameplayTested"])
  self.assertFalse(doc["sourceBinaryCommitted"])
 def test_cplusplus_new_importer_always_rejects_old_world(self):
  cpp=CPP.read_text()
  hdr=HDR.read_text()
  self.assertIn("CreateDrazoviaIzurviveCandidateLandscape",cpp)
  self.assertIn("CreateDrazoviaIzurviveCandidateLandscape",hdr)
  segment=cpp.split("CreateDrazoviaIzurviveCandidateLandscape()",1)[1].split("AActor* UAnomaliaZPrigimaliaWorldImportLibrary::CreateArchipelagoLandscape",1)[0]
  self.assertIn('TEXT("/Game/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate")',segment)
  self.assertIn('TEXT("DRAZOVIA_NEW_TOPO_48KM_3025.r16")',segment)
  self.assertIn("World->DestroyActor(Land)",segment)
  self.assertIn("Land->LandscapeComponents.Num()!=576",segment)
  self.assertNotIn("ANOMALIA_Inhabited_v2",segment)
 def test_editor_author_guarded(self):
  s=AUTHOR.read_text()
  self.assertIn("Protected original",s)
  self.assertIn("EXPECTED_SHA256",s)
  self.assertIn("704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c",s)
  self.assertIn("Candidate map already exists",s)
  self.assertIn("before!=after",s)
  self.assertIn("is_partitioned_world=True",s)
  compile(s,str(AUTHOR),"exec")
if __name__=="__main__":unittest.main()
