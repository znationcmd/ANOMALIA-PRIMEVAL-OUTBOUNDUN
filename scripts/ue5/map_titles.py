"""Validate stable public map names without modifying Unreal maps or save data."""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[2] / "public/config/anomalia-map-catalog.json"


def load_titles(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise ValueError("Unsupported map catalogue version")
    items = data.get("maps")
    if not isinstance(items, list) or len(items) != 2:
        raise ValueError("Expected two distinct 48 km worlds")
    if {item["id"] for item in items} != {"archipelago-v2", "inhabited-v2"}:
        raise ValueError("Map IDs must not change with public titles")
    for item in items:
        title = item["displayName"]
        if not isinstance(title, str) or not 2 <= len(title.strip()) <= 90:
            raise ValueError("Invalid public map title")
        if item["widthKm"] != 48 or item["heightKm"] != 48:
            raise ValueError("Unexpected world size")
        if item["saveNamespace"] != item["id"]:
            raise ValueError("Stable save namespace changed")
        if not item["originalUnrealPackage"].startswith("/Game/Maps/ANOMALIA_"):
            raise ValueError("Original map path changed")
    return {item["id"]: item["displayName"] for item in items}


if __name__ == "__main__":
    for identifier, title in load_titles().items():
        print(identifier + ": " + title)
