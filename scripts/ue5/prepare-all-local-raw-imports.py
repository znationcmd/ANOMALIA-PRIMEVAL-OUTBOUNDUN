"""Prepare deduplicated local model inputs from the existing inventory, preserving archives."""
import os,pathlib,json,hashlib,zipfile,re,shutil,collections
out=pathlib.Path(os.environ["MISSION_RAW_OUT"])
inventory=json.loads((out/"plan/bulk-import-summary.json").read_text(encoding="utf-8"))
project=pathlib.Path(r"D:\ANOMALIA\unreal")
# New C/CMD resources stay at their verified original paths instead of being copied to D.
catalogs=project/"SourceAssets"/"ExternalResources"
known_paths={str(pathlib.Path(row["path"])).casefold() for row in inventory["rawSources"]}
source_catalogs=[]
if catalogs.exists():
    for catalog in sorted(catalogs.glob("original-source-catalog-*.json"),key=lambda p:p.stat().st_mtime_ns):
        data=json.loads(catalog.read_text(encoding="utf-8-sig"))
        if data.get("mode")!="REFERENCE_ORIGINALS_NO_PAYLOAD_COPY":continue
        source_catalogs.append(str(catalog))
        for row in data.get("files",[]):
            if row.get("state")!="ORIGINAL_SOURCE_REFERENCED_NO_COPY":continue
            path=pathlib.Path(row["importSource"]);key=str(path).casefold()
            if path.suffix.casefold() not in {".fbx",".glb",".gltf",".obj",".zip"} or key in known_paths:continue
            inventory["rawSources"].append({"path":str(path),"sourceCatalog":str(catalog)})
            known_paths.add(key)
store=pathlib.Path(r"C:\AZRI")/os.environ["GITHUB_RUN_ID"]
store.mkdir(parents=True,exist_ok=False)
(store/"owner.json").write_text(json.dumps({"project":str(project),"purpose":"Local raw import inputs and newly created resource output"}),encoding="utf-8")
content=store/"resources";content.mkdir()
namespace="/Game/Anomalia/LocalResources/B_"+os.environ["GITHUB_RUN_ID"]
target=project/"Content/Anomalia/LocalResources"/("B_"+os.environ["GITHUB_RUN_ID"])
if target.exists():raise RuntimeError("Preserve existing LocalResources directory; choose its verified owner before importing")
target.parent.mkdir(parents=True,exist_ok=True)
import subprocess
env=os.environ.copy();env["ANOMALIA_RAW_LINK"]=str(target);env["ANOMALIA_RAW_BACKING"]=str(content)
subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command","$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:ANOMALIA_RAW_LINK -Value $env:ANOMALIA_RAW_BACKING | Out-Null"],env=env,check=True,capture_output=True)
existing_hashes=set();skeletal_hashes=set()
index=out/"registered/registered-source-import-data.jsonl"
if index.is_file():
    for line in index.read_text(encoding="utf-8").splitlines():
        row=json.loads(line)
        value=row.get("tags",{}).get("SourceFile","")
        hashes={v.lower() for v in re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])",value)}
        existing_hashes.update(hashes)
        if row.get("class")=="SkeletalMesh":skeletal_hashes.update(hashes)
report={"state":"PREPARING","sourcePlanRun":41842801517,"imports":[],"alreadyRegistered":[],"duplicates":[],"deferred":[],"archiveReceipts":[],"sourceFilesModified":0,"outputNamespace":namespace,"outputBacking":str(content)}
seen={};seen_archives={}
report["originalSourceCatalogs"]=source_catalogs
def save():
    (out/"raw-preparation-manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("RAW_PREP imports="+str(len(report["imports"]))+" registered="+str(len(report["alreadyRegistered"]))+" deferred="+str(len(report["deferred"])),flush=True)
def family(path,archive=None):
    text=str(path).replace("\\","/")
    found=re.search(r"([0-9a-fA-F]{8})-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",text)
    if found:key=found.group(1).lower()
    elif "/FabImports/" in text:key=text.split("/FabImports/",1)[1].split("/")[0].lower()
    else:key=archive or str(path.parent).casefold()
    variant=re.search(r"(FbxUE[45]|Fbx3DSmax|FbxMaya|FbxBlender|FbxUnity|FbxC4D)",text,re.I)
    if variant:key+="|"+variant.group(1).lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
def add(path,archive=None):
    stat=path.stat()
    if getattr(stat,"st_file_attributes",0)&(0x1000|0x400000):
        report["deferred"].append({"source":str(path),"reason":"Source is not resident locally"});return
    h=hashlib.sha256();m=hashlib.md5()
    with path.open("rb") as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk);m.update(chunk)
    sha=h.hexdigest();md5=m.hexdigest()
    if sha in seen:report["duplicates"].append({"source":str(path),"sameAs":seen[sha]});return
    seen[sha]=str(path)
    if md5 in existing_hashes and md5 not in skeletal_hashes:
        report["alreadyRegistered"].append({"source":str(path),"sha256":sha,"sourceMD5":md5});return
    animation=path.suffix.casefold()==".fbx" and bool(re.search(r"[/\\](?:animations?|motions?)[/\\]|[/\\]RM_|[/\\]IP_",str(path),re.I))
    report["imports"].append({"source":str(path),"prepared":str(path),"sha256":sha,"preparedSHA256":sha,"sourceMD5":md5,"family":family(path,archive),"animationOnly":animation})
save()
for source in inventory["rawSources"]:
    path=pathlib.Path(source["path"])
    if not path.is_file():report["deferred"].append({"source":str(path),"reason":"Source no longer exists"});continue
    if path.suffix.casefold()!=".zip":
        add(path);save();continue
    try:
        with zipfile.ZipFile(path) as archive:
            members=archive.infolist()
            if not any(pathlib.PurePosixPath(m.filename).suffix.casefold() in {".fbx",".glb",".gltf",".obj"} for m in members):continue
            archive_digest=hashlib.sha256()
            with path.open("rb") as inp:
                while chunk:=inp.read(1024*1024):archive_digest.update(chunk)
            archive_hash=archive_digest.hexdigest()
            if archive_hash in seen_archives:
                report["duplicates"].append({"source":str(path),"sameAs":seen_archives[archive_hash],"reason":"Identical complete archive; no second extraction"});continue
            total=sum(m.file_size for m in members if not m.is_dir())
            if total>2*1024**3 or shutil.disk_usage(store).free<total+6*1024**3:
                report["deferred"].append({"source":str(path),"reason":"Archive extraction exceeds bounded disk reserve","uncompressedBytes":total});continue
            folder=store/"inputs"/archive_hash[:20];folder.mkdir(parents=True,exist_ok=True)
            extracted=[]
            for member in members:
                pure=pathlib.PurePosixPath(member.filename.replace("\\","/"))
                if pure.is_absolute() or ".." in pure.parts or any(":" in p for p in pure.parts):raise RuntimeError("Archive path escapes its input directory")
                if (member.external_attr>>16)&0o170000==0o120000:raise RuntimeError("Archive contains a symbolic link")
                if member.is_dir():continue
                if pure.suffix.casefold() in {".exe",".dll",".py",".ps1",".bat",".cmd"}:continue
                destination=folder.joinpath(*pure.parts);destination.parent.mkdir(parents=True,exist_ok=True)
                if destination.exists():
                    if destination.stat().st_size!=member.file_size:raise RuntimeError("Preserve differing extracted input")
                else:
                    with archive.open(member) as inp,destination.open("xb") as dst:shutil.copyfileobj(inp,dst)
                if pure.suffix.casefold() in {".fbx",".glb",".gltf",".obj"}:extracted.append(destination)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==archive_hash
            seen_archives[archive_hash]=str(path)
            report["archiveReceipts"].append({"source":str(path),"sha256":archive_hash,"models":len(extracted),"sourceUnchanged":True})
            for model in extracted:add(model,archive_hash)
    except Exception as exc:report["deferred"].append({"source":str(path),"reason":str(exc)})
    save()
# Models and UE-ready exports precede standalone motion files.
report["imports"].sort(key=lambda row:(row["animationOnly"],0 if "FbxUE5" in row["source"] else 1,row["source"].casefold()))
report["state"]="VERIFIED_LOCAL_INPUTS_PREPARED"
save()
print(json.dumps({k:len(report[k]) for k in ["imports","alreadyRegistered","duplicates","deferred"]}),flush=True)
