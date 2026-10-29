"""Regression tests for staged UE5 map/package migration safety."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"migrate-prigimalia-package-references.py"
spec=importlib.util.spec_from_file_location("prigimalia_paths",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PrigimaliaPackageMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"ANOMALIAZ-PRIGIMALIA"
        report=self.root/"unreal"/"Saved"/"BrandMigration"
        report.mkdir(parents=True)
        (report/"verified-source-backup.marker").write_text("independent clone",encoding="utf-8")
        (report/"asset-rename-report.json").write_text(json.dumps({
            "verified":True, "errors":[],
            "mapsRenamed":[{"old":"/Game/Maps/ANOMALIA_Playable_v1",
                            "new":"/Game/Maps/PRIGIMALIA_Playable_v1"}]
        }),encoding="utf-8")
        cfg=self.root/"unreal"/"Config"/"DefaultEngine.ini"
        cfg.parent.mkdir(parents=True)
        self.source=cfg
        self.original='''Map=/Game/Maps/ANOMALIA_Playable_v1.ANOMALIA_Playable_v1
SoftMap=/Game/Maps/ANOMALIA_Playable_v1
OtherMap=/Game/Maps/ANOMALIA_OtherWorld
Asset=/Game/Anomalia/Props/Torch.Torch
LegacySave=ANOMALIA_SAVE_V1
LegacyModule=/Script/AnomaliaPrimeval.AnomaliaGameMode
KeepFolder=D:\\\\ANOMALIA
'''
        cfg.write_text(self.original,encoding="utf-8")

    def test_dry_run_never_edits_files(self):
        result=module.migrate(self.root,False)
        self.assertFalse(result["applied"])
        self.assertGreater(result["changedFiles"],0)
        self.assertEqual(self.source.read_text(encoding="utf-8"),self.original)

    def test_only_confirmed_map_and_package_refs_change(self):
        result=module.migrate(self.root,True)
        self.assertTrue(result["nativeAssetsVerified"])
        updated=self.source.read_text(encoding="utf-8")
        self.assertIn("/Game/Maps/PRIGIMALIA_Playable_v1.PRIGIMALIA_Playable_v1",updated)
        self.assertIn("SoftMap=/Game/Maps/PRIGIMALIA_Playable_v1",updated)
        self.assertIn("OtherMap=/Game/Maps/ANOMALIA_OtherWorld",updated)
        self.assertIn("Asset=/Game/AnomaliaZPrigimalia/Props/Torch.Torch",updated)
        self.assertIn("LegacySave=ANOMALIA_SAVE_V1",updated)
        self.assertIn("LegacyModule=/Script/AnomaliaPrimeval.AnomaliaGameMode",updated)
        self.assertNotIn("ANOMALIA_Playable_v1.ANOMALIA_Playable_v1",updated)

    def test_exact_native_short_names_change_but_save_keys_do_not(self):
        source=self.root/"unreal/Source/Game.cpp"
        source.parent.mkdir(parents=True)
        source.write_text('Map.EndsWith(TEXT("ANOMALIA_Playable_v1")); Save="ANOMALIA_SAVE_V1"; Other="ANOMALIA_OtherWorld";',encoding="utf-8")
        module.migrate(self.root,True)
        updated=source.read_text(encoding="utf-8")
        self.assertIn('TEXT("PRIGIMALIA_Playable_v1")',updated)
        self.assertIn('"ANOMALIA_SAVE_V1"',updated)
        self.assertIn('"ANOMALIA_OtherWorld"',updated)

    def test_refuse_when_unreal_asset_report_not_verified(self):
        f=self.root/"unreal"/"Saved"/"BrandMigration"/"asset-rename-report.json"
        f.write_text(json.dumps({"verified":False,"errors":["Editor failure"]}),encoding="utf-8")
        with self.assertRaises(RuntimeError):
            module.migrate(self.root,True)
        self.assertEqual(self.source.read_text(encoding="utf-8"),self.original)


if __name__=="__main__":
    unittest.main()
