"""F.A.L.C — tenth independent map sourced from the user's CURRENT uploaded image.

Geography intent only; do not substitute an older DRAZOVIA screenshot or
change SKARVIK / DRAZOVIA levels. The user's fused image is the primary
visual reference for coastlines, rivers, islands and regional layout.
Native Landscape .umap, segmentation, licensed assets, roads, settlements,
collision, and gameplay need separate construction and verification.
"""
from __future__ import annotations
import json
from pathlib import Path

MAP_ID="falc-v1"
MAP_NAME="F.A.L.C"
LEVEL="/Game/Maps/PRIGIMALIA_FALC"
SIDE_KM=26.5
AREA_KM2=SIDE_KM*SIDE_KM
TARGET_LAND_KM2=500.
TARGET_WATER_KM2=AREA_KM2-TARGET_LAND_KM2

def world_plan():
    return {"schemaVersion":1,"mapId":MAP_ID,"displayName":MAP_NAME,
        "unrealPackage":LEVEL,"saveNamespace":MAP_ID,
        "worldSizeKm":[SIDE_KM,SIDE_KM],"totalKm2":AREA_KM2,
        "targetLandKm2":TARGET_LAND_KM2,"targetWaterKm2":TARGET_WATER_KM2,
        "landRatioTarget":round(TARGET_LAND_KM2/AREA_KM2,5),
        "waterRatioTarget":round(TARGET_WATER_KM2/AREA_KM2,5),
        "inputReference":"user-current-message-fused-topography-for-FALC",
        "referenceMustNotBeReplacedBy":"DRAZOVIA-topography",
        "geography":"exact region/costal arrangement must be reviewed against provided map",
        "nativeLandscapeCreated":False,
        "binaryR16GeneratedFromThisReference":False,
        "landWaterTargetsMeasuredAgainstSource":False,
        "drazoviaModified":False,"otherNineWorldsModified":False,
        "serverSelectable":False,
        "status":"SOURCE_IMAGE_SELECTED_NATIVE_TERRAIN_NOT_AUTHORED"}

if __name__=="__main__":print(json.dumps(world_plan(),indent=2,ensure_ascii=False))
