"""Check all 400 deterministic 5km CHERNASKALUXRIA sources before native import.

Checks sizes and every seam byte-for-byte, preserves existing source hashes.
This is NOT proof of a 100km UE5 World, road network, or user-photo geometry.
"""
from pathlib import Path
import argparse, hashlib, json, sys
from generate_chernaskaluxria_tiles import (
    BASE_SAMPLES, EXPECTED_BYTES, check_shared_edges, tile_filename,
)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--terrain-dir",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    found=list(a.terrain_dir.glob("CHERNASKALUXRIA_x??_y??.r16"))
    if len(found)!=400:
        raise RuntimeError(f"Expected 400 original terrain sources, got {len(found)}")
    all_tiles=[]
    for row in range(20):
        for col in range(20):
            path=a.terrain_dir/tile_filename(col,row)
            if not path.is_file() or path.stat().st_size!=EXPECTED_BYTES:
                raise RuntimeError("Invalid tile source length: "+str(path))
            all_tiles.append({"name":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
            if row<19 or col<19:
                edges=check_shared_edges(a.terrain_dir,col,row)
                if edges and not all(edges.values()):
                    raise RuntimeError(f"Discontinuous shared edge at col={col} row={row}")
    proof={"status":"ALL_400_NATIVE_HEIGHTFIELD_INPUTS_CHECKED",
           "tileCount":400,"sizePerTile":EXPECTED_BYTES,
           "samplesPerAxis":BASE_SAMPLES,
           "horizontalAndVerticalSeamsChecked":True,
           "worldSizeKilometres":[100,100],"sourceIsProcedural":True,
           "nativeImported":False,"gameplayVerified":False,
           "tiles":all_tiles}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open("x",encoding="utf-8") as w:
        json.dump(proof,w,ensure_ascii=False,indent=2)
    print("CHERNASKALUXRIA_ALL_400_SOURCE_TILES_SEAMS_VERIFIED=true")

if __name__=="__main__":
    main()
