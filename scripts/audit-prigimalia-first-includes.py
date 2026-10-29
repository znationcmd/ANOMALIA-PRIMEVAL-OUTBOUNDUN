#!/usr/bin/env python3
"""Audit Unreal first-header includes after renaming the native C++ module."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]/"unreal"/"Source"/"AnomaliaZPrigimalia"
mismatches=[]
for cpp in sorted(root.rglob("*.cpp")):
    header=cpp.with_suffix(".h")
    if not header.exists():
        continue
    body=cpp.read_text(encoding="utf-8")
    match=re.search(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]",body,re.MULTILINE)
    if not match or Path(match.group(1)).name!=header.name:
        mismatches.append((str(cpp.relative_to(root)), header.name, match.group(1) if match else "MISSING"))
print("C++ files needing own header first: "+str(len(mismatches)))
for path,expected,actual in mismatches:
    print(f"  {path}: expected {expected}, currently {actual}")
if mismatches:
    raise SystemExit(1)
