"""Reproduce RACCONIA-VARKOVIA 16x16 km UE5 import-ready staging data.

Real source ZIP is provided by the game author; do NOT publish copyrighted
source GLBs to this repo. Existing maps or source archives never overwritten.
Requirements: Python 3.11, Pillow, numpy, trimesh.

python scripts/ue5/worldgen/prepare_racconia_ue5_v2.py \
  --kit /separate/RACCONIA_VARKOVIA_16x16_29_LIEUX_UE5_SOURCE.zip \
  --out /separate/NEW_RACCONIA_V2_STAGING

This is not a native .umap or cooked/gameplay level; UE5 import still required.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

SOURCE="Data/RacconiaVarkovia_Map.json"
HEIGHT="Terrain/RACCONIA_VARKOVIA_1025_R16.png"
SITE_MODELS=(
 "BIG_CITY_CONTAMINE","SPD","RAVENFALL","SAINT_VEYR","VEYRHOLM",
 "SECTEUR_ZERO","SAINT_MORVAN","VARKOV","VALDRIS","DRAKOV","NEXUS",
 "HELIX","ACADEMIE_VARKOV","SANCTUAIRE_VALDRIS","BLACKWOOD","ZARNOV",
 "RAVENSKA","MOROZOV","KARZHAN","VALTERIA","NEREIDE","LEVIATHAN",
 "OMEGA","LIANSKAR","KARSEN","NOCTIS","KROVAK","VOLSKAYA",
 "EXPRESS_NOCTURNE")
ROOT=Path(__file__).resolve().parents[3]


def decode_metres(u16:float)->float:
    """Source data are 5.12 R16 values / metre; UE Landscape Z must be 2500cm."""
    return (float(u16)-32768.)/5.12


def euclidean_site_km_to_ue_cm(x:float,y:float)->list[float]:
    # Southwest-origin 16 km map. NOTE SKARVIK has different Y convention.
    return [round((x-8)*100000.,2),round((y-8)*100000.,2)]


def resample_height(src, count=1009):
    """Bilinear 1025 R16 -> 1009 UE valid Landscape resolution, ends identical."""
    import numpy as np
    a=np.asarray(src,dtype=np.uint16)
    if a.shape!=(1025,1025):
        raise ValueError("Expected ORIGINAL 1025x1025 R16 PNG")
    if count!=1009:
        raise ValueError("Only approved 8x8 Landscape component layout")
    axis=np.linspace(0,1024,count)
    low=np.floor(axis).astype(np.int32)
    high=np.minimum(low+1,1024)
    w=(axis-low).astype(np.float64)
    af=a.astype(np.float64)
    first=af[:,low]*(1-w)+af[:,high]*w
    out=first[low,:]*(1-w)[:,None]+first[high,:]*w[:,None]
    return np.rint(out).clip(0,65535).astype("<u2")


def create(kit:Path,output:Path)->dict:
    from PIL import Image
    import numpy as np
    import trimesh
    kit=kit.expanduser().resolve()
    output=output.expanduser().resolve()
    if output==ROOT or ROOT in output.parents or output==kit or kit in output.parents:
        raise ValueError("Output must be in a NEW directory OUTSIDE the source project")
    if output.exists():
        raise FileExistsError("Never overwrite stage or existing user map")
    with zipfile.ZipFile(kit) as z:
        names=set(z.namelist())
        if not {SOURCE,HEIGHT,"Terrain/LandMask_1025.png"}<=names:
            raise ValueError("Missing ORIGINAL Racconia terrain/metadata")
        doc=json.loads(z.read(SOURCE).decode("utf-8-sig"))
        if (doc.get("map")!="RACCONIA-VARKOVIA" or
                doc.get("landscapeWidthKm")!=16 or
                doc.get("landscapeHeightKm")!=16 or
                len(doc.get("sites",[]))!=29 or len(doc.get("roads",[]))!=33):
            raise ValueError("Unexpected source: expected 29 original sites, 33 routes")
        if sum(r["type"]=="liaison_maritime" for r in doc["roads"])!=5:
            raise ValueError("Five maritime routes must stay marine routes")
        models=sorted(n for n in names if n.startswith("Models/") and n.endswith(".glb"))
        if len(models)!=29:
            raise ValueError("Original models must number exactly 29")
        im=Image.open(io.BytesIO(z.read(HEIGHT)))
        if im.size!=(1025,1025):
            raise ValueError("Wrong input height PNG size")
        source_pixels=np.asarray(im,dtype=np.uint16)
        if len(set(s["id"] for s in doc["sites"]))!=29:
            raise ValueError("Duplicate original settlement IDs")
        # Check that the true source PNG altitude matches stored original sites.
        deviation=[]
        for s in doc["sites"]:
            x,y=s["x_km"],s["y_km"]
            if not (0<=x<=16 and 0<=y<=16):
                raise ValueError("Source site is outside map bounds")
            px=round(x/16*1024);py=round(y/16*1024)
            deviation.append(abs(decode_metres(source_pixels[py,px])-s["ground_elevation_m"]))
        if max(deviation)>3:
            raise ValueError("Heightmap Z scale/orientation does not match original sites")
        height=resample_height(source_pixels)
        # Imported GLB meshes are LOW-FIDELITY blockouts; flatten their existing
        # transforms and convert metres to UE OBJ vertex centimetres.
        pending=[]
        for site,modelid in zip(doc["sites"],SITE_MODELS):
            matches=[n for n in models if n.startswith("Models/SM_"+modelid+"_")]
            if len(matches)!=1:
                raise ValueError("Unmatched original GLB for "+site["id"])
            sc=trimesh.load(io.BytesIO(z.read(matches[0])),file_type="glb",force="scene")
            mesh=sc.to_geometry()
            if len(mesh.vertices)==0 or len(mesh.faces)==0:
                raise ValueError("Empty source blockout")
            mesh.vertices*=100.
            obj=trimesh.exchange.obj.export_obj(mesh,include_normals=True,
                    include_color=False)
            pending.append((site,matches[0],modelid,obj,mesh))
        output.mkdir(parents=True,exist_ok=False)
        (output/"Terrain").mkdir()
        (output/"Models_OBJ_UE5_CM").mkdir()
        (output/"Data").mkdir()
        (output/"Terrain/RACCONIA_VARKOVIA_1009x1009.r16").write_bytes(height.tobytes())
        records=[]
        with (output/"Data/29_site_meshes.csv").open("w",encoding="utf-8-sig",newline="") as f:
            writer=csv.writer(f);writer.writerow(("siteId","siteName","objFile",
                     "actorXcm","actorYcm","actorZcm","state"))
            for site,glb,modelid,obj,mesh in pending:
                fn="RACCONIA_"+site["id"]+"_"+modelid+".obj"
                (output/"Models_OBJ_UE5_CM"/fn).write_text(obj,encoding="utf-8")
                x,y=euclidean_site_km_to_ue_cm(site["x_km"],site["y_km"])
                records.append({"id":site["id"],"name":site["name"],"source":glb,
                  "obj":fn,"locationUECm":[x,y,round(site["ground_elevation_m"]*100.,2)],
                  "triangles":len(mesh.faces),"readyForUEImport":True,
                  "importedIntoUE":False})
                writer.writerow((site["id"],site["name"],fn,x,y,
                    round(site["ground_elevation_m"]*100.,2),"IMPORT_REQUIRED"))
        with (output/"Data/33_road_waypoints.csv").open("w",encoding="utf-8-sig",newline="") as f:
            writer=csv.writer(f);writer.writerow(("roadId","class","waypoint",
                       "xUEcm","yUEcm","zUEcm","state"))
            for road in doc["roads"]:
                for idx,(x,y,z) in enumerate(road["points_xyz_m"]):
                    uex,uey=euclidean_site_km_to_ue_cm(x,y)
                    writer.writerow((road["id"],road["type"],idx,uex,uey,
                         round(z*100.,2),"MARITIME" if road["type"]=="liaison_maritime"
                         else "DESIGN_ONLY_NOT_PAVED"))
        report={
         "world":"RACCONIA-VARKOVIA","extentKm":[16,16],
         "sourceSHA256":hashlib.sha256(kit.read_bytes()).hexdigest(),
         "originalHeightPNGSize":[1025,1025],"importR16Size":[1009,1009],
         "layoutComponents":[8,8],"quadsPerSection":63,"sectionsPerComponent":[2,2],
         "scaleCm":{"x":1600000/1008,"y":1600000/1008,"z":2500},
         "originalGuideZ100Incorrect":True,"sourceUnitsPerMetre":5.12,
         "seaLevelU16":32768,"heightMapYDirection":"positive source Y; check UE flip",
         "originalSiteHeightMaxAbsoluteErrorMetres":round(max(deviation),3),
         "sites":records,"roadCount":33,"marineRoadCount":5,
         "modelCount":29,"triangles":sum(x["triangles"] for x in records),
         "noNativeUELevel":True,"notPlayable":True,"originalsNeverOverwritten":True
        }
        (output/"Data/import-manifest.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kit",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    report=create(args.kit,args.out)
    print(json.dumps({k:v for k,v in report.items() if k!="sites"},
        ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
