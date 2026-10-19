#!/usr/bin/env python3
"""Non-destructive ANOMALIA config migration from Three.js to Unreal Engine 5.

Copies original config files into Unreal/Config/Anomalia/Legacy.
Never removes or overwrites files; conflicts are reported for manual merge.
This migrates configuration DATA, not playable levels or game logic.
"""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "config"
TARGET = ROOT / "unreal" / "Config" / "Anomalia" / "Legacy"

def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"Source configuration not found: {SOURCE}")
    TARGET.mkdir(parents=True, exist_ok=True)
    result = {"copied": [], "unchanged": [], "conflicts": [], "source": "public/config",
              "destination": "unreal/Config/Anomalia/Legacy"}
    for source in sorted(SOURCE.iterdir()):
        if not source.is_file() or source.name.startswith("."):
            continue
        destination = TARGET / source.name
        if destination.exists():
            result["unchanged" if checksum(source) == checksum(destination) else "conflicts"].append(source.name)
            continue
        shutil.copy2(source, destination)
        result["copied"].append(source.name)
    report = ROOT / "unreal" / "migration-report.json"
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["conflicts"]:
        print("Conflicts were not overwritten. Review them manually.")

if __name__ == "__main__":
    main()
