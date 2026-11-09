"""Read/validate the 20-world ANOMALIA'Z design catalog.

This intentionally does NOT modify Unreal levels, landscapes or game saves.
Use: python scripts/ue5/worldgen/validate_world_catalog.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT / "config" / "worldgen" / "worlds.json"


def validate_catalog(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("Expected world catalog schemaVersion 1")
    worlds = data.get("worlds")
    if not isinstance(worlds, list) or len(worlds) != 20:
        raise ValueError("Expected exactly 20 planned worlds")
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    missing_dimensions: list[str] = []
    total_area = 0.0

    for index, world in enumerate(worlds, start=1):
        if not isinstance(world, dict):
            raise ValueError(f"World {index} is not an object")
        ident, name = world.get("id"), world.get("name")
        if not isinstance(ident, str) or not ident or ident != ident.strip():
            raise ValueError(f"World {index} invalid id")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"World {index} invalid name")
        if ident in seen_ids or name in seen_names:
            raise ValueError(f"Duplicate world id or name: {ident}")
        seen_ids.add(ident)
        seen_names.add(name)
        if world.get("order") != index:
            raise ValueError(f"Invalid order for {ident}")
        area = world.get("areaKm2")
        if isinstance(area, bool) or not isinstance(area, (float, int)) or not math.isfinite(area) or area <= 0:
            raise ValueError(f"Invalid area for {ident}")
        total_area += area

        width, height = world.get("widthKm"), world.get("heightKm")
        if (width is None) != (height is None):
            raise ValueError(f"Only one dimension provided for {ident}")
        if width is None:
            missing_dimensions.append(name)
        else:
            for dimension in (width, height):
                if isinstance(dimension, bool) or not isinstance(dimension, (int, float)) or not math.isfinite(dimension) or dimension <= 0:
                    raise ValueError(f"Invalid dimensions for {ident}")
            if abs(width * height - area) > 0.011:
                raise ValueError(f"Dimensions do not match area for {ident}")
        land, sea = world.get("landFraction"), world.get("seaFraction")
        if (land is None) != (sea is None):
            raise ValueError(f"Land/sea fraction must be provided together for {ident}")
        if land is not None:
            if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and 0 <= x <= 1 for x in (land, sea)):
                raise ValueError(f"Invalid land/sea fraction for {ident}")
            if abs(land + sea - 1.0) > 1e-9:
                raise ValueError(f"Land/sea fractions do not add to one for {ident}")
        density = world.get("placementDensity")
        if density is not None and (isinstance(density, bool) or not isinstance(density, (int, float)) or not math.isfinite(density) or not 0 <= density <= 1):
            raise ValueError(f"Invalid placement density for {ident}")
        seed = world.get("seed")
        if seed is not None and (not isinstance(seed, str) or not seed):
            raise ValueError(f"Invalid seed for {ident}")
        if world.get("phase") != "planned":
            raise ValueError(f"Unexpected status for {ident}; not UE5-verified")

    if abs(total_area - 24340.18) > 0.011:
        raise ValueError(f"Unexpected total area: {total_area}")
    expected = next(x for x in worlds if x["id"] == "racconia-varkovia")
    if not (expected["areaKm2"] == 256 and expected["widthKm"] == 16
            and expected["heightKm"] == 16 and expected["seed"] == "ANOMALIA-2026"
            and expected["placementDensity"] == 0.65 and expected["landFraction"] == 0.65):
        raise ValueError("RACCONIA-VARKOVIA configuration mismatch")
    return {
        "worldCount": len(worlds),
        "totalAreaKm2": round(total_area, 2),
        "mapsWithoutConfirmedDimensions": missing_dimensions,
        "status": "design-registry-only; no playable UE5 levels generated",
    }


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    print(json.dumps(validate_catalog(catalog), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
