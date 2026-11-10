"""Prepare REAL RACCONIA 16 x 16 km source ZIP as import-grade UE5 Landscape.

Fixes a real 25x vertical Z scale mismatch: the original 1025x1025 PNG
matches 29 source site elevations only when Unreal Landscape Z scale is 2500 cm,
not the 100 cm recorded in the original metadata. Source pixels begin SOUTH;
new 1009x1009 RAW16 is NORTH-up and supports 8x8 Landscape components (126 quads
per component). No map, D: source, or .umap overwritten.

Usage:
  python scripts/ue5/worldgen/prepare_racconia_import_grade.py \
    --kit RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip \
    --output /tmp/RACCONIA_NEW_STAGING
Requires Pillow; output must be a new directory outside this Git checkout.
This exports *source*, not a native Unreal Landscape, road or playable level.
"""
from __future__ import annotations
import argparse
from array import array
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
SIZE=1009
SEA=32768
Z_SCALE=2500.0
SOURCE_PNG="Terrain/RACCONIA_VARKOVIA_1025_R16.png"
SOURCE_JSON="Data/RacconiaVarkovia_Map.json"


def elevation(value:float)->float:
    return (value-SEA)*Z_SCALE/12800.0


def bilinear(im:Image.Image,x_km:float,y_km:float)->float:
    # The ORIGINAL raster row 0 is south, not north.
    x=min(im.width-1,max(0.,x_km*(im.width-1)/16))
    y=min(im.height-1,max(0.,y_km*(im.height-1)/16))
    i,j=int(x),int(y)
    u,v=x-i,y-j
    next_i=min(i+1,im.width-1);next_j=min(j+1,im.height-1)
    return ((1-u)*(1-v)*im.getpixel((i,j))+
            u*(1-v)*im.getpixel((next_i,j))+
            (1-u)*v*im.getpixel((i,next_j))+
            u*v*im.getpixel((next_i,next_j)))


def build(kit:Path,output:Path)->dict:
    kit=kit.expanduser().resolve()
    output=output.expanduser().resolve()
    if output==ROOT or ROOT in output.parents or output==kit or kit in output.parents:
        raise ValueError("Cannot write into originals")
    if output.exists():raise FileExistsError("Never overwrite existing import data")
    with zipfile.ZipFile(kit) as src:
        files=set(src.namelist())
        if SOURCE_PNG not in files or SOURCE_JSON not in files:
            raise ValueError("Missing original terrain and map")
        rawsource=src.read(SOURCE_PNG)
        catalog=json.loads(src.read(SOURCE_JSON).decode("utf-8-sig"))
        if (catalog.get("map")!="RACCONIA-VARKOVIA" or
            catalog.get("landscapeWidthKm")!=16 or
            catalog.get("landscapeHeightKm")!=16 or
            catalog.get("origin")!="southwest" or catalog.get("unit")!="km" or
            len(catalog.get("sites",[]))!=29 or len(catalog.get("roads",[]))!=33):
            raise ValueError("This is not the approved 16km/29-sites/33-roads source")
        if sum(r.get("type")=="liaison_maritime" for r in catalog["roads"])!=5:
            raise ValueError("Do not reclassify five water routes as asphalt")
        im=Image.open(io.BytesIO(rawsource))
        if im.size!=(1025,1025) or not im.mode.startswith("I"):
            raise ValueError("Expected original 1025x1025 gray 16-bit PNG")
        im.load()
        errors=[]
        for site in catalog["sites"]:
            x,y=site["x_km"],site["y_km"]
            if not (0<=x<=16 and 0<=y<=16):
                raise ValueError("Out-of-bounds site")
            actual=elevation(bilinear(im,x,y))
            errors.append(abs(actual-site["ground_elevation_m"]))
        if max(errors)>1.2:
            raise ValueError("Heightmap/source site elevations do not agree at Z=2500")
        resized=im.convert("I").resize((SIZE,SIZE),Image.Resampling.BILINEAR)
        north=resized.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        result=array("H",(max(0,min(65535,int(round(v))))
                          for v in north.get_flattened_data()))
        if sys.byteorder!="little":result.byteswap()
        r16=result.tobytes()
        if len(r16)!=SIZE*SIZE*2:raise ValueError("Invalid 1009 RAW16 length")
        overview=Image.frombytes("I;16",(SIZE,SIZE),r16)
        output.mkdir(parents=True,exist_ok=False)
        (output/"RACCONIA_16KM_1009_NORTH_UP.r16").write_bytes(r16)
        overview.save(output/"RACCONIA_16KM_1009_NORTH_UP.png")
        with (output/"racconia-29-sites.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f);w.writerow(["id","name","x_cm","y_cm","z_cm"])
            for s in catalog["sites"]:
                w.writerow([s["id"],s["name"],round((s["x_km"]-8)*100000,2),
                    round((s["y_km"]-8)*100000,2),round(s["ground_elevation_m"]*100,2)])
        with (output/"racconia-33-source-road-points.csv").open(
          "w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f)
            w.writerow(["road","type","point","x_cm","y_cm","terrain_z_cm","class"])
            for r in catalog["roads"]:
                for i,p in enumerate(r["points_km"]):
                    x,y=p[:2]
                    h=elevation(bilinear(im,x,y))
                    w.writerow([r["id"],r["type"],i,round((x-8)*100000,2),
                        round((y-8)*100000,2),round(h*100,2),
                        "MARITIME_NO_ASPHALT" if r["type"]=="liaison_maritime" else
                        "NEEDS_NATIVE_SLOPE_COLLISION_SURVEY"])
        report={
            "world":"RACCONIA-VARKOVIA","widthKm":16,"heightKm":16,
            "originalHeightmap":"1025 16-bit grayscale PNG, south-up",
            "importHeightmap":"1009 16-bit grayscale R16, north-up",
            "unrealLandscape":{"components":[8,8],"quadsPerSection":63,
                "sectionsPerComponent":[2,2],
                "scaleCm":[1600000/1008,1600000/1008,Z_SCALE],
                "locationCm":[-800000,-800000,0],"seaLevelU16":SEA},
            "originalTerrainSha256":hashlib.sha256(rawsource).hexdigest(),
            "correctedRaw16Sha256":hashlib.sha256(r16).hexdigest(),
            "originalSites":29,"originalRoutes":33,"landRoutes":28,"maritimeRoutes":5,
            "maxSiteHeightDifferenceMetres":round(max(errors),3),
            "nativeUnrealLevelCreated":False,"roadMeshesBuilt":False,
            "modelsImported":False,"sourceFilesOverwritten":False
        }
        (output/"racconia-unreal-import-manifest.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(build(args.kit,args.output),ensure_ascii=False,indent=2))
