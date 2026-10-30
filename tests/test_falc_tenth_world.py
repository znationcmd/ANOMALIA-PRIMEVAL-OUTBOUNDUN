"""Guard the tenth F.A.L.C world, synthetic RAW16 generator and UE native safety."""
from __future__ import annotations
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/ue5"))
import falc_from_composite_r16 as falc

class FALCTenthMapTests(unittest.TestCase):
    def test_tenth_world_is_separate_from_both_drazovia_and_skarvik(self):
        records=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        self.assertEqual(len(records),10)
        ids={v["id"] for v in records}
        paths={v["originalUnrealPackage"] for v in records}
        save_namespaces={v["saveNamespace"] for v in records}
        self.assertEqual(len(ids),10)
        self.assertEqual(len(paths),10)
        self.assertEqual(len(save_namespaces),10)
        falc_record=next(v for v in records if v["id"]=="falc-v1")
        drazovia=next(v for v in records if v["id"]=="inhabited-v2")
        skarvik=next(v for v in records if v["id"]=="archipelago-v2")
        self.assertEqual(drazovia["originalUnrealPackage"],"/Game/Maps/ANOMALIA_Inhabited_v2")
        self.assertEqual(skarvik["originalUnrealPackage"],"/Game/Maps/ANOMALIA_Archipelago_v2")
        self.assertEqual(falc_record["displayName"],"F.A.L.C")
        self.assertEqual(falc_record["originalUnrealPackage"],"/Game/Maps/PRIGIMALIA_FALC")
        self.assertEqual(falc_record["widthKm"],26.5)
        self.assertEqual(falc_record["heightKm"],26.5)
        self.assertFalse(falc_record["serverSelectable"])
        self.assertAlmostEqual(sum(v["widthKm"]*v["heightKm"] for v in records),18235.25)
        self.assertAlmostEqual(26.5*26.5,702.25)
        self.assertAlmostEqual(702.25-500,202.25)

    def test_four_quadrant_source_conversion_matches_exact_shared_edges(self):
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td)
            raw=temp/"DRAZOVIA-original.r16"
            y,x=np.ogrid[-1:1:3025j,-1:1:3025j]
            # The fixture imitates a synthetic archipelago only; real user
            # FALC source lives in separate conversation ZIP, not in git.
            height=(150-180*np.sqrt(x*x+y*y)
                    +15*np.sin(x*7)*np.cos(y*5))
            encoded=np.clip(np.round(32768+height*16),0,65535).astype("<u2")
            encoded.tofile(raw)
            output=temp/"generated"
            result=falc.build(raw,output)
            self.assertEqual(result["mapId"],"falc-v1")
            self.assertEqual(result["quadrantCount"],4)
            self.assertEqual(result["sharedEdgesVerified"],4)
            self.assertEqual(result["worldAreaKm2"],702.25)
            self.assertLess(abs(result["measuredLandKm2"]-500),1)
            self.assertEqual(result["sourceSha256"],falc.sha(raw))
            self.assertEqual(len(list(output.glob("FALC_x*.r16"))),4)
            self.assertEqual((output/"FALC_26_5KM_MASTER_2017.r16").stat().st_size,2017**2*2)
            self.assertEqual(sum(p.stat().st_size for p in output.glob("FALC_x*.r16")),4*1009**2*2)
            a=np.fromfile(output/"FALC_x00_y00.r16",dtype="<u2").reshape(1009,1009)
            e=np.fromfile(output/"FALC_x01_y00.r16",dtype="<u2").reshape(1009,1009)
            s=np.fromfile(output/"FALC_x00_y01.r16",dtype="<u2").reshape(1009,1009)
            self.assertTrue(np.array_equal(a[:,-1],e[:,0]))
            self.assertTrue(np.array_equal(a[-1,:],s[0,:]))
            with self.assertRaises(FileExistsError):
                falc.build(raw,output)
            self.assertEqual(raw.stat().st_size,3025**2*2)

    def test_real_ue_importer_is_guarded_before_any_world_edit(self):
        header=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.h").read_text()
        cpp=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.cpp").read_text()
        author=(ROOT/"unreal/Scripts/create_falc_native.py").read_text()
        self.assertIn("CreateFALCLandscapeTile(int32 Col,int32 Row)",header)
        self.assertIn('World->GetPackage()->GetName()!=TEXT("/Game/Maps/PRIGIMALIA_FALC")',cpp)
        self.assertIn('TEXT("TerrainSource"),TEXT("FALC")',cpp)
        self.assertIn("Land->LandscapeComponents.Num()!=64",cpp)
        self.assertIn("new_level(PACKAGE,is_partitioned_world=True)",author)
        self.assertIn("Existing FALC world must never be recreated/overwritten",author)
        self.assertIn("FALC_NATIVE_LEVEL_SAVED_NOT_PLAYTESTED",author)
        self.assertIn("if num_components!=256",author)
        browser=(ROOT/"unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaServerBrowserLibrary.cpp").read_text()
        self.assertIn('TEXT("falc-v1")',browser)
        self.assertIn("26.5f",browser)
        self.assertIn("Card.WidthKmExact = Definition.Side",browser)

if __name__=="__main__":
    unittest.main()
