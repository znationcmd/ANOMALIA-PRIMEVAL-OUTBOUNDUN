"""One guarded native pass for the existing 48x48 km Inhabited v2 world.

Composes existing backed-up Unreal authoring tools. Does not create a new map,
rename a package, modify the installed game, or touch player saves.
Without --apply the command only prints the planned operations.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "unreal/Content/Maps/ANOMALIA_Inhabited_v2.umap"
PROJECT = ROOT / "unreal/AnomaliaZPrigimalia.uproject"


def commands(engine_root: Path, output: Path):
    python = engine_root / "Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
    scripts = ROOT / "scripts/ue5"
    return [
        ("residential-upgrade", [str(python), str(scripts / "run-residential-upgrade.py"),
                                  "--engine-root", str(engine_root), "--output", str(output / "residential-upgrade")]),
        ("residential-audit", [str(python), str(scripts / "run-residential-audit.py"),
                                "--engine-root", str(engine_root), "--output", str(output / "residential-audit")]),
        ("urban-greenery", [str(python), str(scripts / "run-urban-greenery.py"),
                             "--engine-root", str(engine_root), "--output", str(output / "urban-greenery"),
                             "--house-audit", str(output / "residential-audit/residential-audit.json")]),
        ("real-gpu-review", [str(python), str(scripts / "run-visual-capture.py"),
                              "--engine-root", str(engine_root), "--output", str(output / "visual"), "--inhabited"]),
    ]


def preflight(engine_root: Path):
    if os.name != "nt":
        raise RuntimeError("Native realism requires the authorised Windows UE5.8 runner")
    if not PROJECT.is_file() or not WORLD.is_file():
        raise RuntimeError("Preserved project and original Inhabited v2 world required in isolated checkout")
    project_dir = (ROOT / "unreal").resolve()
    protected_dir = Path("D:/ANOMALIA/unreal").resolve()
    if project_dir == protected_dir:
        raise RuntimeError("Refusing to modify original D:/ANOMALIA")
    if not (engine_root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe").is_file():
        raise RuntimeError("Installed Unreal Engine executable required")
    if not (engine_root / "Engine/Binaries/ThirdParty/Python3/Win64/python.exe").is_file():
        raise RuntimeError("Unreal Python executable required")
    if not os.environ.get("GITHUB_SHA"):
        raise RuntimeError("Fresh commit provenance required")
    # Guard running editors outside Actions even though the workflow uses a
    # non-cancelling native-host concurrency lock.
    check = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "$names=@('UnrealEditor','UnrealEditor-Cmd','AnomaliaPrimeval','AnomaliaZPrigimalia'); "
         "$active=@(Get-Process -Name $names -ErrorAction SilentlyContinue); "
         "if($active.Count -gt 0){exit 3}"],
        check=False, capture_output=True, text=True,
    )
    if check.returncode:
        raise RuntimeError("Unreal/game process already active or process guard unavailable")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Run native authoring, backups and GPU review")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    steps = commands(args.engine_root.resolve(), output)
    if not args.apply:
        print(json.dumps({"state": "DRY_RUN_NO_FILES_MODIFIED",
                          "world": "/Game/Maps/ANOMALIA_Inhabited_v2",
                          "phases": [name for name, _ in steps]}, indent=2))
        return 0
    preflight(args.engine_root.resolve())
    if output.exists():
        raise RuntimeError("New untouched output directory required to preserve existing evidence")
    output.mkdir(parents=True)
    receipt = {"state": "FAILED", "world": "/Game/Maps/ANOMALIA_Inhabited_v2",
               "sourceCommit": os.environ["GITHUB_SHA"], "phases": [],
               "originalUnrealWorldPreserved": True, "gameInstallationModified": False}
    try:
        for name, command in steps:
            log = output / (name + ".log")
            with log.open("x", encoding="utf-8") as target:
                run = subprocess.run(command, cwd=ROOT, stdout=target,
                                     stderr=subprocess.STDOUT, check=False, timeout=3600)
            receipt["phases"].append({"name": name, "exitCode": run.returncode, "log": str(log)})
            if run.returncode:
                raise RuntimeError("Native phase failed: " + name + "; do not publish or install")
        receipt["state"] = "AUTHORED_AND_GPU_REVIEW_RAN_NOT_GAMEPLAY_CERTIFIED"
    except Exception as error:
        receipt["error"] = str(error)
        raise
    finally:
        (output / "realism-pass.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                  encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
