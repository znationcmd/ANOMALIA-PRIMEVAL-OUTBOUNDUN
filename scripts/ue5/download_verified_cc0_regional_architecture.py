#!/usr/bin/env python3
"""Download only officially served, MD5-verified CC0 architectural FBX and 1K textures.

Never scrape Sketchfab, bypass account access, download proprietary Fab content,
or falsely classify generic building facades as Indian/Arabic/etc houses.
One standalone source pack per Poly Haven asset id. No asset edits.
"""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,sys,time,urllib.request,urllib.parse
from datetime import datetime,timezone

POLY_API="https://api.polyhaven.com/files/"
LICENSE="https://polyhaven.com/license"
MAX_TOTAL=280_000_000
MODEL_PACKS={
 "modular_urban_apartments_facade":{
  "use":"realistic_generic_urban_facade_for_moscovie_or_major_cities",
  "isCompleteHouse":False,"isCultureSpecificHouse":False,
 },
 "modular_factory_facade":{
  "use":"realistic_industrial_facade_for_russian_german_and_postapocalyptic_districts",
  "isCompleteHouse":False,"isCultureSpecificHouse":False,
 },
 "modular_fort_01":{
  "use":"realistic_historic_masonry_facade_modules_for_towns",
  "isCompleteHouse":False,"isCultureSpecificHouse":False,
 },
 "chinese_cabinet":{
  "use":"genuine_Chinese_interior_furniture_in_east_asian_buildings",
  "isCompleteHouse":False,"isCultureSpecificHouse":False,
 },
 "carved_wooden_elephant":{
  "use":"decorative_indian_interior_or_market_prop_only",
  "isCompleteHouse":False,"isCultureSpecificHouse":False,
 },
}
HEADERS={"User-Agent":"Anomalia-Prigimalia-Open-CC0-Importer/1.0"}
def fetch_json(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
def safe_path(root,name):
    rel=pathlib.PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("Unsafe model path "+name)
    target=(root/pathlib.Path(*rel.parts)).resolve()
    if root.resolve() not in target.parents:
        raise ValueError("Path escaping source output")
    return target
def file_metadata(part):
    if not isinstance(part,dict):raise ValueError("Bad official asset metadata")
    url=part.get("url","")
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!="https" or parsed.netloc!="dl.polyhaven.org":
        raise ValueError("Untrusted/nonofficial model CDN "+url[:120])
    md5=part.get("md5","").lower()
    size=int(part.get("size",0))
    if len(md5)!=32 or not all(c in "0123456789abcdef" for c in md5):
        raise ValueError("Missing official MD5 checksum")
    if not 0<size<150_000_000:
        raise ValueError("Unexpected individual file size")
    return url,md5,size
def checked_download(part,destination):
    url,md5,size=file_metadata(part)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if destination.stat().st_size!=size or hashlib.md5(destination.read_bytes()).hexdigest()!=md5:
            raise RuntimeError("Existing source asset differs; refusal to replace: "+str(destination))
        return "EXISTING_IDENTICAL"
    temp=destination.with_name(destination.name+".download")
    if temp.exists():
        raise RuntimeError("Unverified partial download already exists; preserve it: "+str(temp))
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers=HEADERS)
            h=hashlib.md5()
            count=0
            with urllib.request.urlopen(req,timeout=80) as remote,open(temp,"xb") as local:
                while True:
                    buf=remote.read(1024*1024)
                    if not buf:break
                    local.write(buf);h.update(buf);count+=len(buf)
                    if count>size+8192:raise RuntimeError("Unbounded source data")
            if count!=size or h.hexdigest()!=md5:
                raise RuntimeError("Source package checksum mismatch")
            os.replace(temp,destination)
            return "DOWNLOADED_MD5_VERIFIED"
        except Exception:
            if temp.exists():temp.unlink()
            if attempt==2:raise
            time.sleep(2+attempt)
    raise RuntimeError("Download failed")
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output",required=True)
    args=a.parse_args()
    out=pathlib.Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=True)
    planned=[]
    for slug,note in MODEL_PACKS.items():
        files=fetch_json(POLY_API+slug)
        info=files.get("fbx",{}).get("1k",{}).get("fbx",{})
        if not info.get("url") or not info.get("include"):
            raise RuntimeError("Official source pack lacks usable 1K FBX bundle for "+slug)
        listed=[(slug+"/model/"+slug+".fbx",info)]
        for key,value in sorted(info.get("include",{}).items()):
            listed.append((slug+"/"+key,value))
        planned.append({"id":slug,"files":listed,"note":note})
    total=sum(file_metadata(info)[2] for p in planned for _,info in p["files"])
    if total>MAX_TOTAL:raise RuntimeError("Total source download too large: "+str(total))
    report={"source":"Poly Haven Official API","license":"CC0 1.0",
        "licenseUrl":LICENSE,"commercialUsePermitted":True,
        "polyhavenAssetCount":len(planned),"bytesPlanned":total,
        "realism":"PBR_realistic_generic_structures_and_genuine_props",
        "regionalCompleteHousesInstalled":False,
        "originalUserAssetsOverwritten":0,"models":[]}
    for p in planned:
        rows=[]
        for rel,item in p["files"]:
            target=safe_path(out,rel)
            state=checked_download(item,target)
            _,md5,size=file_metadata(item)
            rows.append({"relativePath":rel,"bytes":size,"md5":md5,"status":state})
            print("ANOMALIA_CC0_VERIFIED_FILE "+json.dumps({"asset":p["id"],"path":rel,"bytes":size,"status":state}),flush=True)
        report["models"].append({"id":p["id"],"origin":"https://polyhaven.com/a/"+p["id"],
           "intendedUse":p["note"]["use"],
           "isCompleteHouse":p["note"]["isCompleteHouse"],
           "isCultureSpecificHouse":p["note"]["isCultureSpecificHouse"],
           "files":rows})
    report["bytesVerified"]=sum(v["bytes"] for p in report["models"] for v in p["files"])
    (out/"CC0_SOURCE_PROVENANCE.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ANOMALIA_CC0_ARCHITECTURE_DOWNLOADS_VERIFIED "+json.dumps({"models":len(planned),"bytes":report["bytesVerified"],"source":LICENSE}),flush=True)
if __name__=="__main__":main()
