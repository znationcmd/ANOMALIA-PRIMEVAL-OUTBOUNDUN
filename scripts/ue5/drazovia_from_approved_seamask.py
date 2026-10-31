"""Reproduce the user's approved DRAZOVIA 48km synthetic RAW16 from a lossless 709x728 water-line mask.
Not an original DEM. Do not run against production .umaps or save directories.
The source mask is extracted from the user's supplied iZurvive illustration.
"""
import argparse,base64,brotli,hashlib
from pathlib import Path
import cv2
import numpy as np
SIZE=3025
SOURCE_SHA="704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c"
PEAKS=(
(.175,.165,.102,.092,470),(.385,.075,.074,.050,370),
(.535,.112,.082,.084,450),(.890,.130,.095,.095,520),
(.670,.305,.074,.100,490),(.770,.320,.067,.100,310),
(.550,.512,.087,.093,660),(.400,.550,.061,.092,370),
(.115,.594,.100,.096,470),(.320,.705,.099,.095,890),
(.145,.800,.065,.093,680),(.522,.875,.073,.083,480),
(.837,.852,.109,.096,920),(.877,.703,.078,.067,580))
def noise(rng,n):
    return cv2.resize(rng.standard_normal((n,n),dtype=np.float32),
                      (SIZE,SIZE),interpolation=cv2.INTER_CUBIC)
def build(mask_path, out):
    if out.exists(): raise FileExistsError("Refusing to overwrite R16")
    payload=brotli.decompress(base64.b85decode(mask_path.read_text().strip()))
    assert len(payload)==(728*709+7)//8, "Invalid approved coastline mask length"
    old=np.unpackbits(np.frombuffer(payload,dtype=np.uint8))[:728*709].reshape(728,709)
    water=cv2.resize(old.astype(np.float32),(SIZE,SIZE),interpolation=cv2.INTER_LINEAR)>.5
    coastland=cv2.distanceTransform((~water).astype(np.uint8),cv2.DIST_L2,5)
    coastsea=cv2.distanceTransform(water.astype(np.uint8),cv2.DIST_L2,5)
    rng=np.random.default_rng(482026)
    coarse=noise(rng,19)
    mids=noise(rng,55)
    fine=noise(rng,147)
    y,x=np.ogrid[0:SIZE,0:SIZE]
    x=x.astype(np.float32)/(SIZE-1)
    y=y.astype(np.float32)/(SIZE-1)
    peaks=np.zeros((SIZE,SIZE),dtype=np.float32)
    for cx,cy,wx,wy,z in PEAKS:
        ell=(x-cx)**2/(wx*wx)+(y-cy)**2/(wy*wy)
        peaks+=z*np.exp(-1.45*ell).astype(np.float32)
    variation=np.clip(0.22*coarse+0.11*mids+0.055*fine,-.38,.65)
    high=peaks*0.68*(1+variation)
    low=11+np.minimum(coastland*0.9,220)+np.clip(21*coarse+8*mids,-30,45)
    h=np.where(water,-4-np.minimum(coastsea*0.75,240),
               np.maximum(4,low+np.maximum(0,high))).astype(np.float32)
    raw=np.clip(np.rint(32768+h*16),0,65535).astype("<u2")
    assert np.array_equal(raw>32768,~water)
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=out.with_suffix(".r16.part")
    try:
        raw.tofile(temp)
        digest=hashlib.sha256(temp.read_bytes()).hexdigest()
        if digest!=SOURCE_SHA:
            raise RuntimeError(f"Reconstruction SHA mismatch: {digest} != {SOURCE_SHA}")
        assert temp.stat().st_size==3025*3025*2
        temp.rename(out)
    finally:
        temp.unlink(missing_ok=True)
    print("DRAZOVIA_APPROVED_R16_GENERATED",digest,str(out))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mask",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    build(args.mask,args.output)
