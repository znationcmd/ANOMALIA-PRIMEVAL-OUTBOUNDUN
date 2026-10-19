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
