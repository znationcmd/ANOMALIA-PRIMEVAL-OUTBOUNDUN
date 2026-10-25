"""Tests of build orchestration only; no Unreal compilation is simulated as evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("ue5_build", Path(__file__).resolve().parents[1] / "scripts/ue5/validate-build.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

class BuildDriverTests(unittest.TestCase):
    def test_missing_engine_records_block_without_running_compiler(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.subprocess, "run") as run:
            root = Path(directory)
            self.assertEqual(driver.validate(root / "missing", root / "evidence"), 2)
            run.assert_not_called()
            report = json.loads((root / "evidence/report.json").read_text())
            self.assertEqual(report["compilation"], "not_run")
            self.assertEqual(report["execution"], "not_run")

    def test_compiler_failure_stops_before_game_target(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.sys, "platform", "linux"):
            root = Path(directory)
            batch = root / "Engine/Build/BatchFiles/Linux"
            batch.mkdir(parents=True)
            (batch / "Build.sh").touch()
            (root / "Engine/Build/Build.version").write_text('{"MajorVersion":5}')
            with patch.object(driver.subprocess, "run") as run:
                run.return_value.returncode = 6
                self.assertEqual(driver.validate(root, root / "evidence"), 1)
                self.assertEqual(run.call_count, 1)
            report = json.loads((root / "evidence/report.json").read_text())
            self.assertEqual(report["compilation"], "failed")
            self.assertEqual(report["execution"], "not_run")

    def run_native_fixture(self, native_result):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.sys, "platform", "linux"):
            root = Path(directory)
            batch = root / "Engine/Build/BatchFiles/Linux"
            batch.mkdir(parents=True)
            (batch / "Build.sh").touch()
            (root / "Engine/Build/Build.version").write_text('{"MajorVersion":5}')
            def invoke(command, **kwargs):
                if "-NullRHI" in command:
                    export = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-ReportExportPath=")))
                    if native_result is not None:
                        (export / "index.json").write_text(json.dumps(native_result))
                return type("Result", (), {"returncode": 0})()
            with patch.object(driver.subprocess, "run", side_effect=invoke):
                code = driver.validate(root, root / "evidence", run_tests=True)
            return code, json.loads((root / "evidence/report.json").read_text())

    def test_zero_exit_without_test_report_does_not_pass(self):
        code, report = self.run_native_fixture(None)
        self.assertEqual(code, 1)
        self.assertEqual(report["compilation"], "passed")
        self.assertEqual(report["nativeTests"], "failed")

    def test_partial_test_report_does_not_pass(self):
        code, report = self.run_native_fixture({"tests": [{"fullTestPath": "Anomalia.Native.VehicleCatalog", "state": "Success"}]})
        self.assertEqual(code, 1)
        self.assertEqual(report["nativeTests"], "failed")

    def test_all_expected_native_results_still_do_not_claim_playable_game(self):
        code, report = self.run_native_fixture({"tests": [
            {"fullTestPath": name, "state": "Success"} for name in
            ("Anomalia.Native.VehicleCatalog", "Anomalia.Native.ProfileIsolation", "Anomalia.Native.TransportDynamics",
             "Anomalia.Native.DoorLeafAuthorityAndCollision", "Anomalia.Native.CrewEntryAndSafeExitGeometry", "Anomalia.Native.ChaosRoadConfiguration")]})
        self.assertEqual(code, 0)
        self.assertEqual(report["nativeTests"], "passed")
        self.assertEqual(report["execution"], "not_run")
        self.assertEqual(report["worldPlayable"], "not_verified")

    def test_legacy_success_report_without_interaction_tests_is_rejected(self):
        code, report = self.run_native_fixture({"tests": [
            {"fullTestPath": name, "state": "Success"} for name in
            ("Anomalia.Native.VehicleCatalog", "Anomalia.Native.ProfileIsolation", "Anomalia.Native.TransportDynamics")]})
        self.assertEqual(code, 1)
        self.assertEqual(report["nativeTests"], "failed")


