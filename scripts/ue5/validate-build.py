"""Run native UBT builds; never treat source checks as an Unreal compilation."""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def validate(engine: Path, output: Path, run_tests: bool = False, require_loot_tests: bool = False) -> int:
    output.mkdir(parents=True, exist_ok=True)
    report = {"startedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "compilation": "not_run", "execution": "not_run", "worldPlayable": "not_verified",
              "targets": [], "engineRoot": str(engine)}
    report_file = output / "report.json"
    def save():
        report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    save()
    platform = "Win64" if sys.platform == "win32" else "Linux"
    build = engine / "Engine/Build/BatchFiles" / ("Build.bat" if platform == "Win64" else "Linux/Build.sh")
    version_file = engine / "Engine/Build/Build.version"
    if not build.is_file() or not version_file.is_file():
        report["error"] = "Unreal Engine installation missing: Build script and Build.version are required"
        save()
        print(report["error"], file=sys.stderr)
        return 2
    version = json.loads(version_file.read_text(encoding="utf-8"))
    report["engineVersion"] = version
    if version.get("MajorVersion") != 5:
        report["error"] = "Unreal Engine 5 is required"
        save()
        return 2
    import runpy
    try:
        runpy.run_path(str(ROOT / "scripts/ue5/stage-runtime-data.py"))["stage"](ROOT)
    except (OSError, ValueError) as error:
        report["error"] = f"Runtime data staging failed: {error}"
        save()
        return 2
    project = ROOT / "unreal/AnomaliaPrimeval.uproject"
    report["compilation"] = "running"
    save()
    for target in ("AnomaliaPrimevalEditor", "AnomaliaPrimeval"):
        command = [str(build), target, platform, "Development", f"-Project={project}", "-WaitMutex", "-NoHotReloadFromIDE"]
        # cmd.exe is required for a Windows batch file; paths remain separate arguments.
        if platform == "Win64":
            command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", *command]
        log_path = output / f"{target}.log"
        try:
            with log_path.open("w", encoding="utf-8") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
            code = result.returncode
        except OSError as error:
            code = 127
            log_path.write_text(str(error), encoding="utf-8")
        report["targets"].append({"target": target, "exitCode": code, "log": str(log_path)})
        if code != 0:
            report["compilation"] = "failed"
            save()
            return 1
        save()
    report["compilation"] = "passed"
    save()
    if run_tests:
        editor = engine / "Engine/Binaries" / platform / ("UnrealEditor-Cmd.exe" if platform == "Win64" else "UnrealEditor")
        # Unique export folder prevents accepting results left over from an earlier run.
        import uuid
        export = (output / ("automation-" + uuid.uuid4().hex)).resolve()
        export.mkdir(parents=True)
        report["nativeTests"] = "running"
        report["automationReport"] = str(export)
        save()
        command = [str(editor), str(project), "-unattended", "-nopause", "-nosound", "-NullRHI",
                   "-ExecCmds=Automation RunTests Anomalia.Native.; Quit",
                   f"-ReportExportPath={export}", f"-abslog={export / 'editor.log'}"]
        try:
            with (export / "process.log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=900, check=False)
            report["nativeTestExitCode"] = result.returncode
            data = json.loads((export / "index.json").read_text(encoding="utf-8-sig"))
            rows = data.get("tests", [])
            expected = {"Anomalia.Native.VehicleCatalog", "Anomalia.Native.ProfileIsolation", "Anomalia.Native.TransportDynamics"}
            if require_loot_tests:
                expected.update({"Anomalia.Native.LootCatalog", "Anomalia.Native.LootTransactions", "Anomalia.Native.LootJournalRecovery", "Anomalia.Native.RPBankTransactions"})
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
    parser.add_argument("--run-tests", action="store_true", help="Launch native UE automation tests after compilation")
    parser.add_argument("--require-loot-tests", action="store_true", help="Require all native loot tests, never accept an older automation report")
    args = parser.parse_args()
    # Use an explicit missing path to record the failed preflight rather than accidentally using cwd.
    raise SystemExit(validate(args.engine_root or Path("/__UNREAL_ENGINE_NOT_CONFIGURED__"), args.output, args.run_tests, args.require_loot_tests))
