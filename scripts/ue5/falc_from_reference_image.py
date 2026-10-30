"""Build F.A.L.C RAW16 from the user's OWN F.A.L.C illustrated reference.
This is a SYNTHETIC relief estimate, NOT a DEM; never loads DRAZOVIA.
Python deps: numpy, opencv-python-headless.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import cv2
import numpy as np

SIDE_KM=26.5
AXIS=2017
TILE_AXIS=1009
SEA_CODE=32768
CODES_PER_METRE=16
MASSIFS=[
 (.34,.110,.140,.063,1090),(.69,.126,.112,.051,1080),
 (.19,.244,.058,.085,470),(.300,.309,.055,.076,660),
 (.472,.235,.095,.078,690),(.613,.339,.055,.069,510),
 (.477,.461,.069,.066,560),(.633,.457,.075,.067,890),
 (.460,.743,.076,.110,500),(.205,.862,.090,.080,880),
 (.868,.745,.080,.065,340),(.774,.875,.077,.063,1110),
]

def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for piece in iter(lambda:handle.read(1<<20),b""):
            digest.update(piece)
    return digest.hexdigest()

def sea_mask_from_illustration(bgr:np.ndarray)->np.ndarray:
    hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV)
    blue=((hsv[:,:,0]>=86)&(hsv[:,:,0]<=114)&
          (hsv[:,:,1]>=55)&
          (bgr[:,:,0].astype("float32")>=bgr[:,:,2].astype("float32")*1.05))
    return cv2.medianBlur(blue.astype("uint8")*255,5)>127

def smooth_noise(rng:np.random.Generator, nodes:int)->np.ndarray:
    return cv2.resize(rng.normal(0,1,(nodes,nodes)).astype("float32"),
                      (AXIS,AXIS),interpolation=cv2.INTER_CUBIC)

def build(image:Path, output:Path)->dict:
    if not image.is_file(): raise FileNotFoundError(image)
    if output.exists(): raise FileExistsError("Refuse to overwrite FALC outputs")
    original=cv2.imread(str(image),cv2.IMREAD_COLOR)
    if original is None or min(original.shape[:2])<512 or abs(original.shape[0]-original.shape[1])>2:
        raise ValueError("Expected full-resolution square FALC illustrated image")
    sea=cv2.resize(sea_mask_from_illustration(original).astype("uint8"),
                   (AXIS,AXIS),interpolation=cv2.INTER_NEAREST)>0
    land=(~sea).astype("uint8")
    onshore=cv2.distanceTransform(land,cv2.DIST_L2,5)
    offshore=cv2.distanceTransform(sea.astype("uint8"),cv2.DIST_L2,5)
    height=7+np.minimum(onshore*1.8,190)-np.minimum(offshore*1.7,360)
    yy,xx=np.ogrid[:AXIS,:AXIS]
    xf=xx/(AXIS-1)
    yf=yy/(AXIS-1)
    mountains=np.zeros((AXIS,AXIS),dtype=np.float32)
    for cx,cy,sx,sy,metres in MASSIFS:
        mountains+=metres*np.exp(-2*((xf-cx)**2/sx**2+(yf-cy)**2/sy**2)).astype("float32")
    rng=np.random.default_rng(26052026)
    coarse=smooth_noise(rng,25)
    mid=smooth_noise(rng,77)
    fine=smooth_noise(rng,240)
    ridges=mountains*(1+0.10*coarse+0.07*mid+0.023*fine)
    height=np.where(land>0,height+np.maximum(0,ridges)+
                    np.maximum(0,26*coarse+8*mid),
                    -2.5-np.minimum(offshore*1.7,360)).astype("float32")
    height[land>0]=np.maximum(2,height[land>0])
    height[sea]=np.minimum(-1,height[sea])
    encoded=np.clip(np.rint(SEA_CODE+height*CODES_PER_METRE),0,65535).astype("<u2")
    if not np.array_equal(encoded>SEA_CODE,land.astype("bool")):
        raise AssertionError("Reference coastline changed")
    output.mkdir(parents=True,exist_ok=False)
    master=output/"FALC_26_5KM_MASTER_2017.r16"
    encoded.tofile(master)
    tiles=[]
    for row in range(2):
        for col in range(2):
            tile=encoded[row*1008:row*1008+TILE_AXIS,
                         col*1008:col*1008+TILE_AXIS]
            dest=output/f"FALC_x{col:02d}_y{row:02d}.r16"
            tile.tofile(dest)
            tiles.append({"filename":dest.name,"sha256":sha256(dest),
                          "bytes":dest.stat().st_size})
    for row in range(2):
        a=np.fromfile(output/f"FALC_x00_y{row:02d}.r16",dtype="<u2").reshape(1009,1009)
        b=np.fromfile(output/f"FALC_x01_y{row:02d}.r16",dtype="<u2").reshape(1009,1009)
        if not np.array_equal(a[:,-1],b[:,0]): raise AssertionError("E/W seam")
    for col in range(2):
        a=np.fromfile(output/f"FALC_x{col:02d}_y00.r16",dtype="<u2").reshape(1009,1009)
        b=np.fromfile(output/f"FALC_x{col:02d}_y01.r16",dtype="<u2").reshape(1009,1009)
        if not np.array_equal(a[-1,:],b[0,:]): raise AssertionError("N/S seam")
    cv2.imwrite(str(output/"FALC_LAND_MASK_2017.png"),land*255)
    cv2.imwrite(str(output/"FALC_SEA_MASK_2017.png"),sea.astype("uint8")*255)
    cv2.imwrite(str(output/"FALC_ELEVATION_PREVIEW.png"),
                cv2.normalize(height,None,0,255,cv2.NORM_MINMAX).astype("uint8"))
    land_km2=float(np.count_nonzero(land))/land.size*SIDE_KM**2
    report={
        "mapId":"falc-v1","displayName":"F.A.L.C",
        "unrealPackage":"/Game/Maps/PRIGIMALIA_FALC",
        "source":"user-provided-FALC-illustrated-image",
        "referenceImageFilename":image.name,"referenceImageSha256":sha256(image),
        "referencePixels":[original.shape[1],original.shape[0]],
        "worldSideKm":SIDE_KM,"totalKm2":SIDE_KM**2,
        "targetLandKm2":500.,"targetWaterKm2":202.25,
        "derivedLandKm2":round(land_km2,2),
        "derivedWaterKm2":round(SIDE_KM**2-land_km2,2),
        "preserveSourceCoastlineNotAreaQuota":True,
        "masterR16":master.name,"masterSha256":sha256(master),
        "masterAxis":AXIS,"tileAxis":TILE_AXIS,"tiles":tiles,
        "xyScaleCm":SIDE_KM*100000/(AXIS-1),"zScaleCm":800,
        "realAltitudeDEM":False,"terrainHeightsSynthetic":True,
        "nativeUmapBuilt":False,"playtestPassed":False,
        "drazoviaReadOrModified":False,
        "notes":"Visual coasts extracted from colours; shore mask and guessed mountain altitudes need artist/UE5 validation."
    }
    (output/"FALC_IMPORT_MANIFEST.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--image",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    print(json.dumps(build(a.image,a.output),ensure_ascii=False,indent=2))
