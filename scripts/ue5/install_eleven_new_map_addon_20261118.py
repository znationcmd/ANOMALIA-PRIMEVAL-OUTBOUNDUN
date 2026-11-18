"""Add a *new* C++ Blueprint world generator to original D Unreal project.

Only creates three new source files; it never overwrites or edits prior
game source, assets, maps, worlds, or saves. Existing exact files are reused.
Original game sources stay preserved when build fails.
"""
import os,sys,json,hashlib,pathlib,datetime
ROOT=pathlib.Path(r"D:\ANOMALIA\unreal")
REPO=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(os.environ["ELEVEN_MAP_OUT"])
SOURCES=[
 "AnomaliaZPrigimaliaElevenWorldHeights.h",
 "AnomaliaZPrigimaliaElevenWorldLibrary.h",
 "AnomaliaZPrigimaliaElevenWorldLibrary.cpp"]
def sha(t):return hashlib.sha256(t.encode("utf-8")).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
if not (ROOT/"AnomaliaPrimeval.uproject").is_file():raise RuntimeError("Real game .uproject not found")
if not (ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():raise RuntimeError("Original game main map missing")
p=json.loads((ROOT/"AnomaliaPrimeval.uproject").read_text(encoding="utf-8-sig"))
module=p["Modules"][0]["Name"]
if module!="AnomaliaPrimeval":raise RuntimeError("Unknown module; no source modification")
dest=ROOT/"Source"/module/"World"
if not dest.is_dir():raise RuntimeError("Existing original World source path absent")
prepared=[]
for name in SOURCES:
 src=REPO/"unreal/Source/AnomaliaZPrigimalia/World"/name
 if not src.is_file():raise RuntimeError("GitHub source missing "+name)
 data=src.read_text(encoding="utf-8")
 targetname=name.replace("AnomaliaZPrigimalia",module)
 data=data.replace("AnomaliaZPrigimalia",module).replace("ANOMALIAZPRIGIMALIA","ANOMALIAPRIMEVAL")
 target=dest/targetname
 if target.exists():
  if not target.is_file() or target.read_text(encoding="utf-8")!=data:
   raise RuntimeError("Existing native source differs: "+str(target)+"; no changes made")
  state="EXISTING_IDENTICAL"
 else:state="PENDING_NEW_FILE"
 prepared.append({"name":targetname,"path":str(target),"source":str(src),"sha256":sha(data),"state":state,"data":data})
OUT.mkdir(parents=True,exist_ok=True)
manifest={"createdAtUTC":now(),"projectRoot":str(ROOT),"module":module,
 "state":"READY_TO_INSTALL_ADDONLY","deletedOriginalFiles":0,
 "changedExistingSourceFiles":0,"files":[{k:v for k,v in item.items() if k!="data"} for item in prepared]}
(OUT/"addon-install-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
for item in prepared:
 if item["state"]=="EXISTING_IDENTICAL":continue
 target=pathlib.Path(item["path"])
 # Atomic add only: never replace an existing original.
 with target.open("x",encoding="utf-8",newline="\n") as f:f.write(item["data"])
 item["state"]="ADDED"
manifest["state"]="ADDONLY_SOURCE_FILES_INSTALLED_NEEDS_UE_BUILD"
manifest["files"]=[{k:v for k,v in item.items() if k!="data"} for item in prepared]
manifest["sourceHashesVerified"]=all(sha(pathlib.Path(i["path"]).read_text(encoding="utf-8"))==i["sha256"] for i in prepared)
if not manifest["sourceHashesVerified"]:raise RuntimeError("Source integrity verification failed")
(OUT/"addon-install-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("ELEVEN_WORLD_ADDONLY_SOURCE_INSTALL "+json.dumps(manifest),flush=True)
