"""Read model source files on C:, without copying or modifying them."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import unicodedata

MODEL = {".fbx", ".glb", ".gltf", ".obj", ".blend", ".dae", ".usd", ".usda", ".usdc", ".usdz", ".stl", ".uasset"}
ARCHIVE = {".zip", ".7z", ".rar"}
MINUTES = 12


def unavailable(info):
    flags = getattr(info, "st_file_attributes", 0)
    return bool(flags & (stat.FILE_ATTRIBUTE_REPARSE_POINT | stat.FILE_ATTRIBUTE_OFFLINE))


def sources(root, extensions, errors, recursive=True):
    for base, folders, names in os.walk(root, followlinks=False, onerror=lambda e: errors.append(str(e))):
        visible = []
        for folder in folders if recursive else []:
            child = Path(base, folder)
            try:
                if not folder.startswith(".") and not child.is_symlink() and not unavailable(child.lstat()):
                    visible.append(folder)
            except OSError as exc:
                errors.append(str(exc))
        folders[:] = sorted(visible)
        for name in sorted(names):
            path = Path(base, name)
            if path.suffix.lower() in extensions:
                yield path


def read_metadata(path):
    info = path.lstat()
    if path.is_symlink() or unavailable(info) or not stat.S_ISREG(info.st_mode):
        return None
    return info


def content_hash(path, before, deadline):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            if time.monotonic() >= deadline:
                raise TimeoutError("Time limit reached")
            digest.update(block)
    after = path.stat()
    if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
        raise OSError("File changed while being read")
    return digest.hexdigest()


def audit(roots, downloads, out):
    out.mkdir(parents=True, exist_ok=True)
    errors = []
    checked = []
    skipped_roots = []
    names = defaultdict(list)
    visited = set()
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    deadline = time.monotonic() + MINUTES * 60
    inventory = []

    for root, extensions, recursive in [
        *((path, MODEL | ARCHIVE, True) for path in roots),
        *((path, MODEL, False) for path in downloads),
    ]:
        try:
            info = root.lstat()
            if root.is_symlink() or unavailable(info) or not stat.S_ISDIR(info.st_mode):
                skipped_roots.append(str(root))
                continue
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(str(exc))
            continue
        checked.append(str(root))
        for path in sources(root, extensions, errors, recursive):
            path_key = os.path.normcase(os.path.abspath(path))
            if path_key in visited:
                continue
            visited.add(path_key)
            try:
                info = read_metadata(path)
                if info is None:
                    continue
                row = {
                    "path": str(path),
                    "bytes": info.st_size,
                    "modifiedUtc": datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),
                    "recent": max(info.st_mtime, getattr(info, "st_birthtime", info.st_ctime)) >= recent_cutoff.timestamp(),
                    "sha256": None,
                }
                inventory.append(row)
                name_key = unicodedata.normalize("NFC", path.name).casefold()
                names[name_key].append((path, info, row))
            except OSError as exc:
                errors.append(str(exc))

    different = []
    identical = []
    unresolved = []
    # Prioritize recently added sources and small files so a partial report is useful.
    ordered = sorted(names.items(), key=lambda item: (
        not any(r["recent"] for _, _, r in item[1]), sum(r["bytes"] for _, _, r in item[1])
    ))
    for key, group in ordered:
        if len(group) < 2:
            continue
        for path, info, row in group:
            if time.monotonic() >= deadline:
                break
            try:
                row["sha256"] = content_hash(path, info, deadline)
            except OSError as exc:
                errors.append(f"{path}: {exc}")
        hashes = defaultdict(list)
        for _, _, row in group:
            if row["sha256"] is not None:
                hashes[row["sha256"]].append(row)
        entry = {"name": key, "files": [row for _, _, row in group]}
        if len(hashes) > 1:
            different.append(entry)
        if any(row["sha256"] is None for row in entry["files"]):
            unresolved.append(entry)
        identical.extend({"name": key, "files": rows} for rows in hashes.values() if len(rows) > 1)

    summary = {
        "checkedRoots": checked,
        "skippedReparseOrOfflineRoots": skipped_roots,
        "filesFound": len(inventory),
        "recentFilesFound": sum(row["recent"] for row in inventory),
        "sameNameDifferentContents": len(different),
        "sameNameIdenticalBytes": len(identical),
        "sameNameUnresolved": len(unresolved),
        "errors": len(errors),
    }
    report = {
        **summary,
        "files": inventory,
        "different": different,
        "identical": identical,
        "unresolved": unresolved,
        "scanErrors": errors,
    }
    (out / "C-model-inventory.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True), flush=True)
    # Keep logs small. Full groups, including hashes and locations, are in the report.
    for entry in different[:35]:
        print(json.dumps(entry, ensure_ascii=True), flush=True)
    return bool(checked)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    downloads = Path(r"C:\Users\utilisateur\Downloads")
    roots = [Path(path) for path in (r"C:\sketchfab", r"C:\SketchfabExtracted", r"C:\ANOMALIA", r"C:\ANOMALIAZ", r"C:\FabImports")]
    if downloads.is_dir() and not downloads.is_symlink() and not unavailable(downloads.lstat()):
        roots.extend(path for path in downloads.iterdir() if path.name.casefold().startswith(("cmd", "anomalia", "sketchfab")))
        download_roots = [downloads]
    else:
        download_roots = []
    return 0 if audit(roots, download_roots, args.out) else 2


if __name__ == "__main__":
    raise SystemExit(main())
