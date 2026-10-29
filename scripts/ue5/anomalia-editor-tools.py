#!/usr/bin/env python3
"""ANOMALIA’Z PRIGIMALIA Editor/Tools data-only CLI for offline server layout and mod scaffolds.

This is not a live multiplayer editor or a cross-platform mod publisher.
It writes ONLY Saved/Servers/<server-id>/Editor/world.json and refuses invalid scopes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import tempfile

ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
OBJECT_TYPES = frozenset((
    "bed", "table", "chair", "sofa", "wardrobe", "kitchen", "lamp",
    "cow", "chicken", "beehive", "doghouse", "barn", "fence", "tractor_shed",
))
MAX_PLACEMENTS = 256
MAX_FILE_BYTES = 262_144
MAX_COORD_CM = 2_400_000


def valid_id(value: str) -> str:
    if not isinstance(value, str) or ID.fullmatch(value) is None:
        raise ValueError("Identifier must be 1–64 ASCII letters, digits, '-' or '_'")
    return value


def world_path(saved_root: Path, server_id: str) -> Path:
    sid = valid_id(server_id)
    base = (saved_root.resolve() / "Servers" / sid).resolve()
    path = (base / "Editor" / "world.json").resolve()
    if not path.is_relative_to(base):
        raise ValueError("Symlink or path escapes the server's private directory")
    return path


def validate(data: dict, server_id: str) -> dict:
    if not isinstance(data, dict) or data.get("schemaVersion") != 1 or data.get("serverId") != server_id:
        raise ValueError("World file schema or server scope mismatch")
    rows = data.get("placements")
    if not isinstance(rows, list) or len(rows) > MAX_PLACEMENTS:
        raise ValueError("Invalid or excessive placement count")
    ids = set()
    for obj in rows:
        if not isinstance(obj, dict) or set(obj) != {"id", "type", "x", "y", "z", "yaw"}:
            raise ValueError("Placement fields must match the approved schema")
        oid = valid_id(obj["id"])
        if oid in ids:
            raise ValueError("Duplicate placement ID")
        ids.add(oid)
        if obj["type"] not in OBJECT_TYPES:
            raise ValueError("Unknown/unapproved placeable type")
        for key in ("x", "y", "z", "yaw"):
            number = obj[key]
            if type(number) not in (float, int) or not math.isfinite(number):
                raise ValueError("Non-finite or non-numeric coordinate")
            if abs(number) > (360 if key == "yaw" else MAX_COORD_CM):
                raise ValueError("Placement outside the bounds")
    return data


def read_world(saved_root: Path, server_id: str) -> dict:
    path = world_path(saved_root, server_id)
    if not path.exists():
        return {"schemaVersion": 1, "serverId": server_id, "placements": []}
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Existing layout exceeds maximum size; will not overwrite it")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Existing world layout is invalid; preserving original") from error
    return validate(data, server_id)


def save_world(saved_root: Path, server_id: str, data: dict) -> Path:
    validate(data, server_id)
    output = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(output) > MAX_FILE_BYTES:
        raise ValueError("World layout too large")
    path = world_path(saved_root, server_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Recheck after directory creation to reject a newly introduced symlink.
    if world_path(saved_root, server_id) != path:
        raise ValueError("Server path changed while preparing layout")
    fd, temp = tempfile.mkstemp(prefix=".world-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return path


def add_object(saved_root: Path, server_id: str, object_id: str,
               object_type: str, x: float, y: float, z: float, yaw: float) -> Path:
    data = read_world(saved_root, server_id)
    data["placements"].append({
        "id": valid_id(object_id), "type": object_type,
        "x": x, "y": y, "z": z, "yaw": yaw,
    })
    return save_world(saved_root, server_id, data)


def remove_object(saved_root: Path, server_id: str, object_id: str) -> Path:
    data = read_world(saved_root, server_id)
    valid_id(object_id)
    old_length = len(data["placements"])
    data["placements"] = [p for p in data["placements"] if p["id"] != object_id]
    if len(data["placements"]) == old_length:
        raise ValueError("Object ID not found; no changes")
    return save_world(saved_root, server_id, data)


def mod_template(mod_root: Path, mod_id: str) -> Path:
    valid_id(mod_id)
    root = mod_root.resolve()
    target = (root / mod_id).resolve()
    if not target.is_relative_to(root) or target.exists():
        raise ValueError("Mod directory already exists or escapes selected root")
    target.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schemaVersion": 1,
        "id": mod_id,
        "title": mod_id.replace("_", " ").title(),
        "version": "0.1.0",
        "contentType": "data-only",
        "platforms": ["pc"],
        "files": ["objects.json"],
    }
    (target / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (target / "objects.json").write_text('{"schemaVersion": 1, "objects": []}\n', encoding="utf-8")
    return target


def lint_mod(mod_dir: Path) -> dict:
    base = mod_dir.resolve()
    manifest_path = base / "mod.json"
    if not manifest_path.is_file() or manifest_path.stat().st_size > 32768:
        raise ValueError("Missing or oversized mod.json")
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (m.get("schemaVersion") != 1 or m.get("contentType") != "data-only" or
            not isinstance(m.get("title"), str) or len(m["title"]) > 96 or
            not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", m.get("version", ""))):
        raise ValueError("Invalid safe data-only manifest")
    valid_id(m.get("id"))
    if m.get("platforms") != ["pc"]:
        raise ValueError("Console cross-play is not approved; PC data-only only for now")
    files = m.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= 64 or len(set(files)) != len(files):
        raise ValueError("Bad content list")
    for filename in files:
        if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.json", filename):
            raise ValueError("Only flat, data-only JSON files are supported")
        path = (base / filename).resolve()
        if not path.is_relative_to(base) or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("Missing, untrusted or oversized content file")
        json.loads(path.read_text(encoding="utf-8"))
    return m


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--saved-root", type=Path, default=Path("unreal/Saved"))
    p.add_argument("--server-id", default="personal_1")
    sub = p.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("id")
    add.add_argument("type", choices=sorted(OBJECT_TYPES))
    for name in ("x", "y", "z", "yaw"):
        add.add_argument(name, type=float)
    rm = sub.add_parser("remove")
    rm.add_argument("id")
    sub.add_parser("list")
    new = sub.add_parser("new-mod")
    new.add_argument("id")
    new.add_argument("--mods-root", type=Path, default=Path("mods"))
    lint = sub.add_parser("lint-mod")
    lint.add_argument("folder", type=Path)
    args = p.parse_args()
    if args.action == "new-mod":
        print(mod_template(args.mods_root, args.id))
    elif args.action == "lint-mod":
        print(json.dumps(lint_mod(args.folder), indent=2))
    else:
        valid_id(args.server_id)
        if args.action == "add":
            print(add_object(args.saved_root, args.server_id, args.id,
                             args.type, args.x, args.y, args.z, args.yaw))
        elif args.action == "remove":
            print(remove_object(args.saved_root, args.server_id, args.id))
        else:
            print(json.dumps(read_world(args.saved_root, args.server_id), indent=2))


if __name__ == "__main__":
    main()
