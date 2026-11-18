#!/usr/bin/env python3
"""Download genuine individual CC0 regional house GLBs from official open Innerscene.

Strict verification: original source page says CC0, official same-host direct
download URL; check binary GLB header, embedded JSON, and size; never bypass
authentication or replace user's existing files. These are architectural
models, not proof of photogrammetry or explorable interiors.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,struct,urllib.parse,urllib.request
from datetime import datetime,timezone
HOST="www.innerscene.com"
REGIONS={
 "korean_hanok":{
  "slug":"hanok-house-l-shaped-with-courtyard-and-stone-wall-4267797e",
  "label":"KIRYUMORI Korean hanok traditional home and courtyard",
  "region":"korean","category":"real-scale-regional-house"},
 "indian_modern_3bhk":{
  "slug":"3bhk-house-on-a-60-x-120-ft-plot-3d-model-163b8736",
  "label":"ARANYAPURA Indian residence 3BHK architectural home",
  "region":"indian","category":"real-scale-house"},
 "hawaiian_tropical_bungalow":{
  "slug":"bungalow-house-85d40048",
  "label":"MOKUPUNAWAI tropical single-storey bungalow (not specifically Hawaiian)",
  "region":"tropical","category":"real-scale-house"},
 "rural_nordic_house_candidate":{
  "slug":"two-storey-farmhouse-with-wraparound-porch-and-metal-roof-e7674089",
  "label":"Rural generic farmhouse for Nordic/country variants, not an authentic Norway house",
  "region":"temperate","category":"real-scale-house"}
}
HEADERS={"User-Agent":"ANOMALIA-Prigimalia-Authorized-CC0-Download/1.0"}
def load(url,limit):
    u=urllib.parse.urlparse(url)
    if u.scheme!="https" or u.hostname!=HOST:
        raise RuntimeError("Official house source host mismatch")
    request=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(request,timeout=65) as r:
        if r.url!=url and urllib.parse.urlparse(r.url).hostname!=HOST:
            raise RuntimeError("Official download redirected to host "+str(urllib.parse.urlparse(r.url).hostname))
        h=hashlib.sha256();chunks=[];total=0
        while True:
            b=r.read(1024*1024)
            if not b:break
            chunks.append(b);h.update(b);total+=len(b)
            if total>limit:raise RuntimeError("Unexpectedly large house source")
        return b"".join(chunks),h.hexdigest(),r.headers.get("Content-Type","")
def validate_glb(payload):
    if len(payload)<32 or payload[:4]!=b"glTF":
        raise RuntimeError("Source is not an authentic GLB binary")
    version,length=struct.unpack_from("<II",payload,4)
    if version!=2 or length!=len(payload):
        raise RuntimeError("GLB header length/version invalid")
    chunklen,chunktype=struct.unpack_from("<I4s",payload,12)
    if chunktype!=b"JSON" or chunklen<8 or chunklen>len(payload)-20:
        raise RuntimeError("GLB must contain a proper asset JSON chunk")
    doc=json.loads(payload[20:20+chunklen].decode("utf-8"))
    if str(doc.get("asset",{}).get("version",""))!="2.0":
        raise RuntimeError("GLB 2.0 metadata invalid")
    if not doc.get("meshes"):
        raise RuntimeError("Downloaded GLB contains no physical mesh")
    return {"meshCount":len(doc["meshes"]),
            "materialCount":len(doc.get("materials",[])),
            "nodeCount":len(doc.get("nodes",[])),
            "imageCount":len(doc.get("images",[]))}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    a=parser.parse_args()
    out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    results=[]
    for key,item in REGIONS.items():
        slug=item["slug"]
        page="https://"+HOST+"/tools/library/3d-parts/"+slug
        text,_,type_page=load(page,3*1024*1024)
        html=text.decode("utf-8","replace")
        if "CC0" not in html or ("/api/library/"+slug+"/download") not in html:
            raise RuntimeError("Public CC0 and direct downloadable GLB unavailable "+slug)
        direct="https://"+HOST+"/api/library/"+slug+"/download"
        payload,hash_,ctype=load(direct,25*1024*1024)
        info=validate_glb(payload)
        target=out/(key+".glb")
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()!=hash_:
                raise RuntimeError("Existing source differs; refuse overwrite "+str(target))
        else:
            with target.open("xb") as f:f.write(payload)
        if target.stat().st_size!=len(payload):
            raise RuntimeError("Stored binary size differs from downloaded GLB")
        result={"key":key,"label":item["label"],"region":item["region"],
                "category":item["category"],"sourcePage":page,
                "officialDownload":direct,"license":"CC0 1.0",
                "bytes":len(payload),"sha256":hash_,
                "sourceContentType":ctype,
                "glbVersion":"2.0","nativeUnrealStaticMeshImported":False,
                "completeInteriorsVerified":False,"gameplayPlaytested":False,**info}
        results.append(result)
        print("ANOMALIA_CC0_REGIONAL_REAL_HOUSE_DOWNLOADED "+json.dumps(result),flush=True)
    report={"state":"FOUR_REAL_SCALE_CC0_HOUSE_GLB_SOURCE_ASSETS_VERIFIED",
            "license":"CC0 1.0","source":"Innerscene public original model library",
            "modelCount":len(results),"regionalHouseStylesDownloaded":list(REGIONS),
            "originalUserAssetsOverwritten":0,"models":results}
    (out/"INNERSCENE_CC0_HOUSE_PROVENANCE.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ANOMALIA_CC0_REAL_HOUSES_DOWNLOAD_SUCCESS "+json.dumps({"count":len(results),"bytes":sum(r["bytes"] for r in results)}),flush=True)
if __name__=="__main__":main()
