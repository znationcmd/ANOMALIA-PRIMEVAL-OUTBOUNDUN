"""Validate stable public map names without modifying Unreal maps or save data."""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[2] / "public/config/anomalia-map-catalog.json"


def load_titles(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise ValueError("Unsupported map catalogue version")
    items = data.get("maps")
    if not isinstance(items, list) or len(items) != 8:
        raise ValueError("Expected eight independent worlds")
    if {item["id"] for item in items} != {"archipelago-v2", "inhabited-v2", "karskov-v1", "vorgrad-v1", "nemoris-v1", "drakheim-v1", "solynacalyra-v1", "nexavarkhos-v1"}:
        raise ValueError("Map IDs must not change with public titles")
    for item in items:
        title = item["displayName"]
        if not isinstance(title, str) or not 2 <= len(title.strip()) <= 90:
            raise ValueError("Invalid public map title")
        expected_size = {"archipelago-v2": 48, "inhabited-v2": 48,
                         "karskov-v1": 30, "vorgrad-v1": 30,
                         "nemoris-v1": 20, "drakheim-v1": 20,
                         "solynacalyra-v1": 15, "nexavarkhos-v1": 10}[item["id"]]
        if item["widthKm"] != expected_size or item["heightKm"] != expected_size:
            raise ValueError("Unexpected world size")
        if item["saveNamespace"] != item["id"]:
            raise ValueError("Stable save namespace changed")
        if not item["originalUnrealPackage"].startswith(("/Game/Maps/ANOMALIA_", "/Game/Maps/PRIGIMALIA_")):
            raise ValueError("Original map path changed")
    return {item["id"]: item["displayName"] for item in items}


if __name__ == "__main__":
    for identifier, title in load_titles().items():
        print(identifier + ": " + title)
