"""Build orchestration regression fixtures, never evidence of a native UE build."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("ue5_build", Path(__file__).resolve().parents[1] / "scripts/ue5/validate-build.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
NAMES = ("Anomalia.Native.VehicleCatalog", "Anomalia.Native.ProfileIsolation")
PASS = {"tests": [{"fullTestPath": name, "state": "Success"} for name in NAMES]}


def engine_fixture(root, version=None):
    batch = root / "Engine/Build/BatchFiles/Linux"
    batch.mkdir(parents=True)
    (batch / "Build.sh").touch()
    (root / "Engine/Build/Build.version").write_text(json.dumps(
        version if version is not None else {"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 3}))
    editor = root / "Engine/Binaries/Linux/UnrealEditor"
    editor.parent.mkdir(parents=True)
    editor.touch()


class BuildDriverTests(unittest.TestCase):
    def test_missing_engine_records_block_without_running_compiler(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.subprocess, "run") as run:
            root = Path(directory)
            self.assertEqual(driver.validate(root / "missing", root / "evidence"), 2)
            run.assert_not_called()
            report = json.loads((root / "evidence/report.json").read_text())
            self.assertEqual(report["compilation"], "not_run")
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["execution"], "not_run")

    def test_other_engine_version_is_blocked_before_compilation(self):
        for version in ({"MajorVersion": 5, "MinorVersion": 6}, {"MajorVersion": 6, "MinorVersion": 0}):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                engine_fixture(root, version)
                with patch.object(driver.subprocess, "run") as run:
                    self.assertEqual(driver.validate(root, root / "evidence"), 2)
                    run.assert_not_called()

    def test_malformed_version_still_records_failure_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine_fixture(root)
            (root / "Engine/Build/Build.version").write_text("not JSON")
            self.assertEqual(driver.validate(root, root / "evidence"), 2)
            self.assertEqual(json.loads((root / "evidence/report.json").read_text())["status"], "BLOCKED")

    def test_compiler_failure_stops_before_game_target(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.sys, "platform", "linux"):
            root = Path(directory)
            engine_fixture(root)
            with patch.object(driver.subprocess, "run") as run:
                run.return_value.returncode = 6
                self.assertEqual(driver.validate(root, root / "evidence"), 1)
                self.assertEqual(run.call_count, 1)
            report = json.loads((root / "evidence/report.json").read_text())
            self.assertEqual(report["compilation"], "failed")
            self.assertEqual(report["execution"], "not_run")

    def test_compiler_timeout_is_recorded_and_stops_pipeline(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.sys, "platform", "linux"):
            root = Path(directory)
            engine_fixture(root)
            with patch.object(driver.subprocess, "run", side_effect=subprocess.TimeoutExpired("UBT", 5)) as run:
                self.assertEqual(driver.validate(root, root / "evidence", build_timeout=5), 1)
                self.assertEqual(run.call_count, 1)
            report = json.loads((root / "evidence/report.json").read_text())
            self.assertEqual(report["targets"][0]["exitCode"], 124)

    def run_native_fixture(self, native_result, code=0, extra_expected=()):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.sys, "platform", "linux"):
            root = Path(directory)
            engine_fixture(root)
            seen = []
            def invoke(command, **kwargs):
                seen.append(command)
                if "-NullRHI" in command:
                    export = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("-ReportExportPath=")))
                    if native_result is not None:
                        (export / "index.json").write_text(json.dumps(native_result))
                    return type("Result", (), {"returncode": code})()
                return type("Result", (), {"returncode": 0})()
            with patch.object(driver.subprocess, "run", side_effect=invoke), \
                 patch.object(driver, "expected_native_tests", return_value=set(NAMES) | set(extra_expected)):
                result = driver.validate(root, root / "evidence", run_tests=True)
            return result, json.loads((root / "evidence/report.json").read_text()), seen

    def test_zero_exit_without_test_report_does_not_pass(self):
        code, report, _ = self.run_native_fixture(None)
        self.assertEqual(code, 1)
        self.assertEqual(report["compilation"], "passed")
        self.assertEqual(report["nativeTests"], "failed")

    def test_partial_test_report_does_not_pass(self):
        code, report, _ = self.run_native_fixture({"tests": [PASS["tests"][0]]})
        self.assertEqual(code, 1)
        self.assertEqual(report["nativeTests"], "failed")

    def test_any_failed_or_incomplete_result_blocks_validation(self):
        for state in ("Fail", "NotRun", "InProcess"):
            with self.subTest(state=state):
                code, report, _ = self.run_native_fixture({"tests": PASS["tests"] + [
                    {"fullTestPath": "Anomalia.Native.Other", "state": state}]})
                self.assertEqual(code, 1)
                self.assertEqual(report["nativeTests"], "failed")

    def test_nonzero_editor_exit_cannot_pass_with_good_test_report(self):
        code, report, _ = self.run_native_fixture(PASS, code=3)
        self.assertEqual(code, 1)
        self.assertEqual(report["nativeTests"], "failed")

    def test_malformed_native_report_types_fail_without_leaving_running_state(self):
        for data in ([], {"tests": ["bad row"]}, {"tests": None}):
            with self.subTest(data=data):
                code, report, _ = self.run_native_fixture(data)
                self.assertEqual(code, 1)
                self.assertEqual(report["nativeTests"], "failed")

    def test_future_registered_tests_cannot_be_silently_omitted(self):
        code, _, _ = self.run_native_fixture(PASS, extra_expected=("Anomalia.Native.NewFeature",))
        self.assertEqual(code, 1)

    def test_all_expected_native_results_still_do_not_claim_playable_game(self):
        code, report, commands = self.run_native_fixture(PASS)
        self.assertEqual(code, 0)
        self.assertEqual(report["nativeTests"], "passed")
        self.assertEqual(report["execution"], "not_run")
        self.assertEqual(report["worldPlayable"], "not_verified")
        self.assertIn("-TestExit=Automation Test Queue Empty", commands[-1])
        self.assertNotIn("; Quit", " ".join(commands[-1]))

    def test_expected_test_discovery_reads_cpp_registrations(self):
        self.assertTrue(set(NAMES).issubset(driver.expected_native_tests()))

    def test_world_generation_requires_new_report_and_real_map(self):
        # These are orchestration fixtures, not generated Unreal assets.
        for mode, expected_code in (("missing_report", 1), ("missing_map", 1), ("good", 0)):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                engine = root / "engine"
                engine_fixture(engine)
                repo = root / "repo"
                project = repo / "unreal/AnomaliaPrimeval.uproject"
                project.parent.mkdir(parents=True)
                project.write_text("{}")
                map_file = repo / "unreal/Content/Maps/ANOMALIA_FirstTest.umap"
                # A stale success report may not be accepted instead of this run's report.
                evidence = root / "evidence"
                evidence.mkdir()
                (evidence / "first-world-stale.json").write_text('{"status":"umap_created_needs_ue_play_test"}')
                def invoke(command, **kwargs):
                    if "env" in kwargs:
                        if mode != "missing_report":
                            Path(kwargs["env"]["ANOMALIA_WORLD_REPORT"]).write_text(json.dumps({
                                "status": "umap_created_needs_ue_play_test", "mapPackage": driver.MAP_PACKAGE}))
                        if mode == "good":
                            map_file.parent.mkdir(parents=True)
                            map_file.write_bytes(b"orchestration-fixture" * 100)
                    return type("Result", (), {"returncode": 0})()
                with patch.object(driver, "ROOT", repo), patch.object(driver.sys, "platform", "linux"), \
                     patch.object(driver.subprocess, "run", side_effect=invoke):
                    self.assertEqual(driver.validate(engine, evidence, create_world=True), expected_code)
                report = json.loads((evidence / "report.json").read_text())
                self.assertEqual(report["worldPlayable"], "not_verified")
                self.assertEqual(report["worldGeneration"], "passed" if expected_code == 0 else "failed")
