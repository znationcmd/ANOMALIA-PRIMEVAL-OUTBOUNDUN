"""Resume verified model inputs and extract remaining owned archives without overwriting originals."""
import os,pathlib,json,hashlib,zipfile,stat,shutil,time,re
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
OUT=pathlib.Path(os.environ["MISSION_RAW_OUT"])
STATE=PROJECT/"Saved/ImportReceipts/RawResume20261107"
STATE.mkdir(parents=True,exist_ok=True)
MANIFEST=STATE/"raw-preparation-manifest.json"
MODELS={".fbx",".glb",".gltf",".obj"}
SKIP={".git","intermediate","binaries","deriveddatacache",".tmp.driveupload","node_modules"}
assert (PROJECT/"AnomaliaPrimeval.uproject").is_file()
old=json.loads((OUT/"prior/raw-preparation-manifest.json").read_text(encoding="utf-8"))
data=json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else old
report={**data,"state":"PREPARING_REMAINING_SOURCES","deferred":[],"sourceFilesModified":0,"archivesDeleted":0}
report.setdefault("archiveReceipts",[])
seen={r["sha256"]:r["prepared"] for r in report["imports"]}
archives={r["sha256"]:r["source"] for r in report["archiveReceipts"]}
sources={r["path"].casefold():r["path"] for r in json.loads((OUT/"prior/plan/bulk-import-summary.json").read_text(encoding="utf-8"))["rawSources"]}
plan=PROJECT/"Saved/CloudTransfer/Direct20261106/direct-source-plan.jsonl"
if plan.exists():
 for line in plan.open(encoding="utf-8"):
  row=json.loads(line);p=pathlib.PureWindowsPath(row["path"])
  if p.suffix.lower() in MODELS|{".zip",".7z",".rar"} and not SKIP.intersection(x.lower() for x in p.parts):
   sources.setdefault(str(p).casefold(),str(p))
started=time.monotonic();summary={"priorPreparedModels":len(old["imports"]),"priorPreparedArchives":len(old["archiveReceipts"]),"newModels":0,"newArchives":0,"unsupportedArchives":[],"sourcePaths":len(sources)}
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
 return h.hexdigest()
def save():
 tmp=MANIFEST.with_suffix(".tmp")
 tmp.write_text(json.dumps(report,indent=2),encoding="utf-8");os.replace(tmp,MANIFEST)
 summary.update(preparedModels=len(report["imports"]),deferred=len(report["deferred"]),elapsedSeconds=time.monotonic()-started,freeBytes={d:shutil.disk_usage(d+":/").free for d in ["C","D"]})
 (OUT/"preparation-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
 print("EXTRACTION_PROGRESS "+json.dumps(summary),flush=True)
def add(p,family):
 sha=digest(p)
 if sha in seen:return
 seen[sha]=str(p)
 animation=p.suffix.lower()==".fbx" and bool(re.search(r"[/\\](?:animations?|motions?)[/\\]|[/\\]RM_|[/\\]IP_",str(p),re.I))
 report["imports"].append({"source":str(p),"prepared":str(p),"sha256":sha,"preparedSHA256":sha,"family":family,"animationOnly":animation})
 summary["newModels"]+=1
def safe_member(m):
 p=pathlib.PurePosixPath(m.filename.replace("\\","/"))
 if p.is_absolute() or ".." in p.parts or any(":" in s or s.endswith((" ",".")) for s in p.parts):raise ValueError("Unsafe archive path preserved")
 if stat.S_IFMT(m.external_attr>>16)==stat.S_IFLNK:raise ValueError("Archive symlink preserved")
 return p
if os.environ.get("PREPARE_EXISTING_ONLY")=="1":
 report["state"]="PRIOR_VERIFIED_INPUTS_RESTORED_FOR_NATIVE_RESUME";save();print("EXTRACTION_RESULT "+json.dumps(summary),flush=True)
 raise SystemExit(0)
for raw in sorted(sources.values(),key=lambda s:(pathlib.PureWindowsPath(s).suffix.lower()!=".zip",s.casefold())):
 if time.monotonic()-started>45*60:
  report["deferred"].append({"source":raw,"reason":"Preparation time budget; resume from durable receipts"});break
 p=pathlib.Path(raw)
 try:
  if not p.is_file():
   reference=p.with_name(p.name+".duplicate.json")
   if reference.is_file():
    ref=json.loads(reference.read_text(encoding="utf-8"));p=pathlib.Path(ref["retainedOriginalPath"])
    if not p.is_file() or digest(p)!=ref["sha256"]:raise ValueError("Retained archive verification failed")
   else:
    report["deferred"].append({"source":raw,"reason":"Missing local source; original path retained in inventory"});continue
  s=p.stat()
  if getattr(s,"st_file_attributes",0)&(0x1000|0x400000):raise ValueError("Source is not resident locally")
  if p.suffix.lower() in {".7z",".rar"}:
   summary["unsupportedArchives"].append(str(p));continue
  if p.suffix.lower()!=".zip":
   add(p,hashlib.sha256(str(p.parent).casefold().encode()).hexdigest());continue
  archive_hash=digest(p)
  if archive_hash in archives:continue
  with zipfile.ZipFile(p) as z:
   members=z.infolist()
   if not any(pathlib.PurePosixPath(m.filename).suffix.lower() in MODELS for m in members):continue
   validated=[(m,safe_member(m)) for m in members]
   chosen=[(m,pure) for m,pure in validated if not m.is_dir() and pure.suffix.lower() not in {".exe",".dll",".py",".ps1",".bat",".cmd",".com",".scr",".msi"}]
   if any(m.flag_bits&1 for m,_ in chosen):raise ValueError("Encrypted archive requires its owner's password")
   paths=[str(pure).casefold() for _,pure in chosen]
   if len(paths)!=len(set(paths)):raise ValueError("Archive contains conflicting case-insensitive paths; preserved")
   needed=sum(m.file_size for m,_ in chosen)
   root=pathlib.Path(r"D:\ANOMALIA\unreal\SourceAssets\Prepared3D20261107")
   if shutil.disk_usage("D:/").free<needed+12*1024**3:raise ValueError("Extraction deferred to preserve 12 GiB on D")
   root.mkdir(parents=True,exist_ok=True);folder=root/archive_hash
   folder.mkdir(exist_ok=True)
   complete=folder/"extraction-receipt.json"
   if complete.exists():
    receipt=json.loads(complete.read_text(encoding="utf-8"))
    if receipt.get("archiveSHA256")!=archive_hash:raise ValueError("Existing extraction owner mismatch")
   extracted=[]
   for m,pure in chosen:
    dst=folder.joinpath(*pure.parts)
    if not dst.parent.resolve().is_relative_to(folder.resolve()):raise ValueError("Extracted path crosses an external link")
    if dst.exists() and getattr(dst.lstat(),"st_file_attributes",0)&0x400:raise ValueError("Existing extraction reparse point preserved")
    if dst.exists():
     if not dst.is_file() or dst.stat().st_size!=m.file_size:raise ValueError("Existing extracted file differs; no overwrite")
     import zlib
     crc=0
     with dst.open("rb") as f:
      for b in iter(lambda:f.read(4*1024**2),b""):crc=zlib.crc32(b,crc)
     if crc&0xffffffff!=m.CRC:raise ValueError("Existing extraction CRC differs; no overwrite")
    else:
     dst.parent.mkdir(parents=True,exist_ok=True)
     with z.open(m) as src,dst.open("xb") as target:shutil.copyfileobj(src,target,4*1024**2)
    if pure.suffix.lower() in MODELS:extracted.append(dst)
   after=p.stat()
   if (s.st_size,s.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or digest(p)!=archive_hash:raise ValueError("Archive changed during extraction")
   complete.write_text(json.dumps({"archive":str(p),"archiveSHA256":archive_hash,"files":len(chosen),"models":len(extracted),"originalPreserved":True}),encoding="utf-8")
   family=hashlib.sha256(archive_hash.encode()).hexdigest()
   for model in extracted:add(model,family)
   archives[archive_hash]=str(p)
   report["archiveReceipts"].append({"source":str(p),"sha256":archive_hash,"models":len(extracted),"sourceUnchanged":True})
   summary["newArchives"]+=1
  save()
 except Exception as exc:report["deferred"].append({"source":raw,"reason":str(exc)})
report["imports"].sort(key=lambda r:(r.get("animationOnly",False),r["source"].casefold()))
report["state"]="LOCAL_INPUTS_PREPARED_WITH_EXPLICIT_DEFERRED" if report["deferred"] or summary["unsupportedArchives"] else "ALL_INVENTORIED_SUPPORTED_INPUTS_PREPARED"
save()
print("EXTRACTION_RESULT "+json.dumps(summary),flush=True)
