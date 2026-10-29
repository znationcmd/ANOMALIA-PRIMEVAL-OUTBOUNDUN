#!/usr/bin/env python3
"""Update public-facing legacy game titles without breaking Unreal object paths.

Usage:
  python scripts/rebrand-public-identity.py            # dry-run
  python scripts/rebrand-public-identity.py --apply    # apply to checkout

Does NOT rename C++ API names, .uproject file, /Game/Anomalia packages,
legacy save keys, Electron protocol/appId or the GitHub repository URL.
Those require an Unreal Editor migration and release compatibility checks.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".md",".txt",".js",".mjs",".cjs",".json",".ini",".yml",".yaml",".xml",
              ".html",".css",".py",".ps1",".cmd",".vbs",".csv",".cpp",".h",".cs",
              ".cfg",".uproject"}
REPLACEMENTS = (
    ("ANOMALIA <strong>PRIMEVAL</strong> OUTBOUNDUN", "ANOMALIA’Z <strong>PRIGIMALIA</strong>"),
    ("ANOMALIA <b>PRIMEVAL</b> OUTBOUNDUN", "ANOMALIA’Z <b>PRIGIMALIA</b>"),
    ("ANOMALIA PRIMEVAL OUTBOUNDUN", "ANOMALIA’Z PRIGIMALIA"),
    ("Anomalia Primeval Outboundun", "ANOMALIA’Z PRIGIMALIA"),
    ("ANOMALIA_PRIMEVAL_OUTBOUNDUN", "ANOMALIAZ_PRIGIMALIA"),
)
IGNORED = {".git","node_modules","dist","release","Saved","Intermediate","Binaries",
           ".venv","venv","DerivedDataCache","__pycache__"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args = parser.parse_args()
    changed=[]
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] == ".github" or path.resolve() == Path(__file__).resolve():
            continue  # GitHub workflow writes require extra permission; never mutate this script
        if any(part in IGNORED for part in relative.parts):
            continue
        if path.stat().st_size > 350_000:  # huge generated assets, never rewrite blindly
            continue
        try:
            original=path.read_text(encoding="utf-8")
        except (UnicodeError,OSError):
            continue
        updated=original
        for previous,replacement in REPLACEMENTS:
            updated=updated.replace(previous,replacement)
        if updated==original:
            continue
        changed.append(str(path.relative_to(ROOT)))
        if args.apply:
            path.write_text(updated,encoding="utf-8")
    print(("UPDATED" if args.apply else "WOULD UPDATE")+f" {len(changed)} text files")
    for path in changed:
        print(" - "+path)
    print("Legacy internal UE paths, historic GitHub URLs and save IDs intentionally preserved.")

if __name__=="__main__":
    main()
