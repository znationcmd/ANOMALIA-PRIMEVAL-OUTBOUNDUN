"""Compile with UE 5.8 and retain native evidence; source tests are never build evidence."""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import platform as host_platform
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
MAP_PACKAGE = "/Game/Maps/ANOMALIA_FirstTest"


def expected_native_tests() -> set[str]:
    """Every registered native test must report success, including future additions."""
    expected = set()
    for source in (ROOT / "unreal/Source").rglob("*.cpp"):
        expected.update(re.findall(r'IMPLEMENT_SIMPLE_AUTOMATION_TEST\s*\(\s*\w+\s*,\s*"(Anomalia\.Native\.[^"]+)"',
                                   source.read_text(encoding="utf-8")))
    if not expected:
        raise ValueError("No Anomalia.Native tests registered in this checkout")
    return expected


def validate(engine: Path, output: Path, run_tests: bool = False,
             create_world: bool = False, build_timeout: int = 7200) -> int:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"startedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "compilation": "not_run", "execution": "not_run", "worldPlayable": "not_verified",
              "worldGeneration": "not_run", "nativeTests": "not_run", "targets": [],
              "engineRoot": str(engine), "requiredEngine": "5.8",
              "host": {"system": sys.platform, "architecture": host_platform.machine(),
                       "cpuCount": os.cpu_count(), "freeDiskBytes": shutil.disk_usage(output).free}}
    report_file = output / "report.json"

    def save():
        report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def block(message):
        report["error"] = message
        report["status"] = "BLOCKED"
        save()
        print(message, file=sys.stderr)
        return 2

    save()
    if sys.platform not in ("win32", "linux"):
        return block("This build driver supports Windows and Linux hosts only")
    platform = "Win64" if sys.platform == "win32" else "Linux"
    report["targetPlatform"] = platform
    build = engine / "Engine/Build/BatchFiles" / ("Build.bat" if platform == "Win64" else "Linux/Build.sh")
    version_file = engine / "Engine/Build/Build.version"
    if not build.is_file() or not version_file.is_file():
        return block("Unreal Engine installation missing: Build script and Build.version are required")
    try:
        version = json.loads(version_file.read_text(encoding="utf-8-sig"))
        if not isinstance(version, dict):
            raise ValueError("Build.version must be a JSON object")
    except (OSError, ValueError) as error:
        return block(f"Cannot read Unreal version: {error}")
    report["engineVersion"] = version
    if (version.get("MajorVersion"), version.get("MinorVersion")) != (5, 8):
        return block("Unreal Engine 5.8 is required for this validation; another version is not accepted")
    project = ROOT / "unreal/AnomaliaPrimeval.uproject"
    if not project.is_file():
        return block("AnomaliaPrimeval.uproject missing from checkout")
    report["compilation"] = "running"
    save()
    for target in ("AnomaliaPrimevalEditor", "AnomaliaPrimeval"):
        command = [str(build), target, platform, "Development", f"-Project={project}", "-WaitMutex", "-NoHotReloadFromIDE"]
        if platform == "Win64":
            # CALL avoids cmd.exe's special leading-quote handling for spaced engine paths.
            command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", "call", *command]
        log_path = output / f"{target}.log"
        try:
            with log_path.open("w", encoding="utf-8") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=build_timeout, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
            report["error"] = f"Native compilation timed out for {target}"
        except OSError as error:
            code = 127
            log_path.write_text(str(error), encoding="utf-8")
        report["targets"].append({"target": target, "exitCode": code, "log": str(log_path), "command": command})
        if code != 0:
            report["compilation"] = "failed"
            save()
            return 1
        save()
    report["compilation"] = "passed"
    report["status"] = "COMPILES"
    save()
    editor = engine / "Engine/Binaries" / platform / ("UnrealEditor-Cmd.exe" if platform == "Win64" else "UnrealEditor")
    if create_world or run_tests:
        if not editor.is_file():
            return block("Native targets compiled but the Unreal Editor executable is missing")

    if create_world:
        world_report = output / ("first-world-" + uuid.uuid4().hex + ".json")
        log_path = output / (world_report.stem + ".log")
        report["worldGeneration"] = "running"
        report["worldReport"] = str(world_report)
        save()
        environment = dict(os.environ, ANOMALIA_WORLD_REPORT=str(world_report))
        command = [str(editor), str(project),
                   f"-ExecutePythonScript={ROOT / 'scripts/ue5/create-first-world.py'}",
                   "-unattended", "-nop4", "-nosplash", "-NullRHI", f"-abslog={log_path}"]
        try:
            with log_path.with_suffix(".process.log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        env=environment, timeout=900, check=False)
            data = json.loads(world_report.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("Invalid first-world execution report")
            map_file = ROOT / "unreal/Content/Maps/ANOMALIA_FirstTest.umap"
            if (result.returncode != 0 or data.get("status") not in
                ("umap_created_needs_ue_play_test", "already_exists_not_modified") or
                data.get("mapPackage") != MAP_PACKAGE or not map_file.is_file() or map_file.stat().st_size < 1024):
                raise ValueError("Editor did not produce the expected real FirstTest map")
            report["worldGeneration"] = "passed"
            report["mapFile"] = str(map_file)
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            report["worldGeneration"] = "failed"
            report["error"] = str(error)
            save()
            return 1
        save()

    if run_tests:
        export = output / ("automation-" + uuid.uuid4().hex)
        export.mkdir()
        report["nativeTests"] = "running"
        report["automationReport"] = str(export)
        save()
        command = [str(editor), str(project)]
        if create_world:
            command.append(MAP_PACKAGE)
        # Quit must be triggered by the automation queue completing, not a queued ExecCmds Quit.
        command += ["-unattended", "-nopause", "-nosound", "-NullRHI",
                    "-ExecCmds=Automation RunTests Anomalia.Native.",
                    "-TestExit=Automation Test Queue Empty",
                    f"-ReportExportPath={export}", f"-abslog={export / 'editor.log'}"]
        try:
            expected = expected_native_tests()
            report["expectedNativeTests"] = sorted(expected)
            with (export / "process.log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=900, check=False)
            report["nativeTestExitCode"] = result.returncode
            data = json.loads((export / "index.json").read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("Native test report must be a JSON object")
            rows = data.get("tests", [])
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise ValueError("Invalid native test report")
            passed = {row.get("fullTestPath") for row in rows if row.get("state") == "Success"}
            if result.returncode != 0 or not expected.issubset(passed) or any(row.get("state") != "Success" for row in rows):
                raise ValueError("Missing, incomplete or failed native tests")
            report["nativeTests"] = "passed"
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            report["nativeTests"] = "failed"
            report["error"] = str(error)
            save()
            return 1
        save()
    print("Native builds passed. Game execution and playable world remain unverified.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", type=Path, default=os.environ.get("UE_ROOT"))
    parser.add_argument("--output", type=Path, default=ROOT / "unreal/Saved/BuildValidation")
    parser.add_argument("--run-tests", action="store_true", help="Launch UE automation after compilation")
    parser.add_argument("--create-first-world", action="store_true", help="Generate the real FirstTest .umap with UE Editor")
    parser.add_argument("--build-timeout", type=int, default=7200)
    args = parser.parse_args()
    if args.build_timeout < 1:
        parser.error("--build-timeout must be positive")
    raise SystemExit(validate(args.engine_root or Path("/__UNREAL_ENGINE_NOT_CONFIGURED__"), args.output,
                             args.run_tests, args.create_first_world, args.build_timeout))
