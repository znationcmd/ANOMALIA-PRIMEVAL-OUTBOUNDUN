"""F.A.L.C source-only heightfield conversion from the user's already-composed map.

Produces exactly one independent 26.5x26.5 km landscape, split into
four seam-identical 13.25x13.25 km quadrants. Source was an original,
synthetic 3025x3025 48km RAW16 reconstruction of the user's drawing.
No exact DEM, native Unreal map or third-party game terrain is claimed.

Requires numpy and opencv-python-headless for the offline conversion.
Never overwrites the DRAZOVIA source or existing F.A.L.C exports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import cv2

WORLD_ID="falc-v1"
PACKAGE="/Game/Maps/PRIGIMALIA_FALC"
SIDE_KM=26.5
TOTAL_KM2=SIDE_KM**2
TARGET_LAND_KM2=500.0
TARGET_WATER_KM2=TOTAL_KM2-TARGET_LAND_KM2
RAW_AXIS=2017
QUADRANT_AXIS=1009
QUADRANT_QUADS=1008
SOURCE_AXIS=3025
HEIGHT_CODE_ZERO=32768
HEIGHT_CODES_PER_METER=16
XY_SCALE_CM=(SIDE_KM*100000)/(RAW_AXIS-1)
Z_SCALE_CM=800

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(source:Path,output:Path)->dict:
    if not source.is_file() or source.stat().st_size!=SOURCE_AXIS*SOURCE_AXIS*2:
        raise ValueError("Need the original complete 3025x3025 synthetic R16 source")
    if output.exists():
        if any(output.iterdir()):
            raise FileExistsError("Never replace existing FALC output or any authored map")
    else:
        output.mkdir(parents=True,exist_ok=False)
    data=np.fromfile(source,dtype="<u2").reshape(SOURCE_AXIS,SOURCE_AXIS)
    # Resample the entire composed terrain once: crop the four tiles AFTER
    # encoding so borders are byte-identical, not independently generated.
    samples=(cv2.resize(data.astype(np.float32),(RAW_AXIS,RAW_AXIS),
        interpolation=cv2.INTER_AREA)-HEIGHT_CODE_ZERO)/HEIGHT_CODES_PER_METER
    samples=cv2.GaussianBlur(samples,(0,0),sigmaX=3.8,sigmaY=3.8)
    # Shift the datum to obtain ~500 km² emergent ground while preserving
    # the uploaded map's relative ridges and islands. No arbitrary ocean fill.
    sea_percentile=1.0-TARGET_LAND_KM2/TOTAL_KM2
    old_coast=float(np.quantile(samples,sea_percentile))
    samples-=old_coast
    encoded=np.clip(np.round(HEIGHT_CODE_ZERO+samples*HEIGHT_CODES_PER_METER),
         0,65535).astype("<u2")
    pixels_land=int(np.count_nonzero(encoded>HEIGHT_CODE_ZERO))
    land=TOTAL_KM2*pixels_land/(RAW_AXIS*RAW_AXIS)
    sea=TOTAL_KM2-land
    if abs(land-TARGET_LAND_KM2)>1.0:
        raise RuntimeError("Requested coastline and surface ratio not achieved")
    master=output/"FALC_26_5KM_MASTER_2017.r16"
    encoded.tofile(master)
    tiles=[]
    for row in range(2):
        for col in range(2):
            p=output/f"FALC_x{col:02d}_y{row:02d}.r16"
            t=encoded[row*QUADRANT_QUADS:row*QUADRANT_QUADS+QUADRANT_AXIS,
                      col*QUADRANT_QUADS:col*QUADRANT_QUADS+QUADRANT_AXIS]
            if t.shape!=(QUADRANT_AXIS,QUADRANT_AXIS):
                raise RuntimeError("Incorrect quarter RAW dimensions")
            t.tofile(p)
            tiles.append({"col":col,"row":row,"filename":p.name,
                          "bytes":p.stat().st_size,"sha256":sha(p)})
    # Check four exact adjacent shared-edge pairs.
    edges=0
    for row in range(2):
        for col in range(2):
            a=encoded[row*QUADRANT_QUADS:row*QUADRANT_QUADS+QUADRANT_AXIS,
                      col*QUADRANT_QUADS:col*QUADRANT_QUADS+QUADRANT_AXIS]
            if col<1:
                x=encoded[row*QUADRANT_QUADS:row*QUADRANT_QUADS+QUADRANT_AXIS,
                          QUADRANT_QUADS:QUADRANT_QUADS+QUADRANT_AXIS]
                if not np.array_equal(a[:,-1],x[:,0]):
                    raise RuntimeError("East shared edge mismatch")
                edges+=1
            if row<1:
                y=encoded[QUADRANT_QUADS:QUADRANT_QUADS+QUADRANT_AXIS,
                          col*QUADRANT_QUADS:col*QUADRANT_QUADS+QUADRANT_AXIS]
                if not np.array_equal(a[-1,:],y[0,:]):
                    raise RuntimeError("South shared edge mismatch")
                edges+=1
    if edges!=4:raise RuntimeError("Wrong shared edge count")
    manifest={
        "schemaVersion":1,"mapId":WORLD_ID,"displayName":"F.A.L.C",
        "unrealPackage":PACKAGE,"saveNamespace":WORLD_ID,
        "independentWorld":True,"worldSideKm":SIDE_KM,
        "worldAreaKm2":TOTAL_KM2,"landTargetKm2":TARGET_LAND_KM2,
        "waterTargetKm2":TARGET_WATER_KM2,
        "measuredLandKm2":round(land,3),"measuredSeaKm2":round(sea,3),
        "oldSeaDatumAdjustmentMetres":round(-old_coast,5),
        "verticesPerAxis":RAW_AXIS,"masterFile":master.name,
        "masterSha256":sha(master),"sourceSha256":sha(source),
        "quadrantGrid":[2,2],"quadrantSideKm":SIDE_KM/2,
        "samplesPerQuadrantAxis":QUADRANT_AXIS,
        "quadrantCount":4,"sharedEdgesVerified":edges,"quadrants":tiles,
        "xyScaleCm":XY_SCALE_CM,"zScaleCm":Z_SCALE_CM,
        "source":"User-fused DRAZOVIA composition adapted for separate F.A.L.C",
        "nativeUnrealImported":False,"playtestPassed":False,
        "drazoviaModified":False,"sourceAltitudesExact":False,
        "note":"Four quadrants of ONE provided composite; not four original DEM files."
    }
    with (output/"FALC_GENERATION_REPORT.json").open("x",encoding="utf-8") as handle:
        json.dump(manifest,handle,indent=2,ensure_ascii=False)
        handle.write("\n")
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=build(args.source,args.output)
    print(json.dumps({k:result[k] for k in
      ("mapId","worldAreaKm2","measuredLandKm2","measuredSeaKm2",
       "quadrantCount","sharedEdgesVerified","nativeUnrealImported")},indent=2))
