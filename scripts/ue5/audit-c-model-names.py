"""Read model source files on C:, without copying or modifying them."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import stat
import time
import unicodedata
import zipfile

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


def hash_stream(stream, deadline):
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(2**20), b""):
        if time.monotonic() >= deadline:
            raise TimeoutError("Time limit reached")
        digest.update(block)
    return digest.hexdigest()


def content_hash(path, before, deadline):
    with path.open("rb") as stream:
        digest = hash_stream(stream, deadline)
    after = path.stat()
    if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
        raise OSError("File changed while being read")
    return digest


def zip_model_hashes(path, deadline):
    with zipfile.ZipFile(path) as archive:
        members = [
            item for item in archive.infolist()
            if not item.is_dir() and Path(item.filename).suffix.lower() in MODEL
        ]
        if sum(item.file_size for item in members) > 512 * 2**20 or len(members) > 512:
            raise ValueError("Archive model payload exceeds read-only verification budget")
        models = []
        for item in members:
            with archive.open(item) as stream:
                models.append({"member": item.filename, "sha256": hash_stream(stream, deadline)})
        return models


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
                stem = re.sub(r" \(\d+\)$", "", path.stem)
                name_key = unicodedata.normalize("NFC", stem + path.suffix).casefold()
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
            for path, info, row in group:
                if path.suffix.lower() != ".zip" or row["sha256"] is None:
                    continue
                try:
                    row["zipModels"] = zip_model_hashes(path, deadline)
                    after = path.stat()
                    if (info.st_size, info.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        del row["zipModels"]
                        raise OSError("Archive changed while being read")
                except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
                    errors.append(f"{path}: {exc}")
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
        log_entry = {"name": entry["name"], "files": []}
        for row in entry["files"]:
            log_row = {key: row[key] for key in ("path", "bytes", "sha256", "recent")}
            if "zipModels" in row:
                log_row["zipModelCount"] = len(row["zipModels"])
                log_row["zipModelHashes"] = sorted(m["sha256"] for m in row["zipModels"][:20])
                log_row["zipModelExamples"] = [m["member"] for m in row["zipModels"][:5]]
            log_entry["files"].append(log_row)
        print(json.dumps(log_entry, ensure_ascii=True), flush=True)
    for entry in identical[:35]:
        print(json.dumps({"identicalName": entry["name"], "paths": [row["path"] for row in entry["files"]]}, ensure_ascii=True), flush=True)
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
