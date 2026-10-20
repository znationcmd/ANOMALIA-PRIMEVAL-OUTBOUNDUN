#!/usr/bin/env python3
"""Non-destructive migration of ANOMALIA config templates into a UE5 staging area.

Usage: python unreal/Scripts/export_legacy_configs.py [repository-root] [output-directory]
Copies original JSON/XML/INI/CFG/TXT templates unchanged, validates JSON and records SHA256.
Does NOT import 3D geometry, saves, or game logic. Does NOT overwrite an existing output.
"""
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / "unreal" / "MigrationStaging"
SOURCE = ROOT / "public" / "config"
SUFFIXES = {".json", ".xml", ".ini", ".cfg", ".txt"}
def main():
    if not SOURCE.is_dir():
        raise SystemExit(f"Missing source directory: {SOURCE}")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for src in sorted(SOURCE.iterdir()):
        if not src.is_file() or src.suffix.lower() not in SUFFIXES:
            continue
        data = src.read_bytes()
        if src.suffix.lower() == ".json":
            json.loads(data.decode("utf-8"))
        target = OUT / src.name
        if target.exists():
            if target.read_bytes() != data:
                raise SystemExit(f"Refusing to overwrite changed file: {target}")
        else:
            shutil.copyfile(src, target)
        manifest.append({"file": src.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    target = OUT / "migration-manifest.json"
    payload = json.dumps({"source": "ANOMALIA JavaScript prototype", "files": manifest}, ensure_ascii=False, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != payload:
        raise SystemExit("Refusing to overwrite a changed migration manifest")
    if not target.exists():
        target.write_text(payload, encoding="utf-8")
    print(f"Copied/verified {len(manifest)} templates into {OUT}; original files unchanged.")

if __name__ == "__main__":
    main()
