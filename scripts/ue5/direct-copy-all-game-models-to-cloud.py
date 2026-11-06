"""Copy existing game resources directly to Drive, preserving folders and originals."""
import os,pathlib,json,time,hashlib,sqlite3,uuid,shutil
EXT={".uasset",".umap",".uexp",".ubulk",".uptnl",".fbx",".glb",".gltf",".obj",".blend",".abc",".usd",".usdz",".usda",".usdc",".3ds",".stl",".dae",".zip",".7z",".rar",".png",".jpg",".jpeg",".tga",".bmp",".tif",".tiff",".dds",".exr",".hdr",".psd",".wav",".ogg",".flac",".mp3",".bin",".mtl",".uproject",".uplugin"}
SKIP={".git",".tmp.driveupload","deriveddatacache"}
def permitted(raw,all_files=False):
 p=pathlib.PureWindowsPath(raw)
 return p.drive.casefold() in {"c:","d:"} and not any(x.casefold() in SKIP for x in p.parts) and (all_files or p.suffix.casefold() in EXT)
def target_relative(raw):
 p=pathlib.PureWindowsPath(raw)
 if not permitted(raw,True):raise ValueError("Only approved local C/D game-resource paths")
 return pathlib.Path(p.drive[0].upper(),*p.parts[1:])
def io_path(p):
 raw=os.path.abspath(str(p))
 return pathlib.Path("\\\\?\\"+raw) if os.name=="nt" and not raw.startswith("\\\\?\\") else pathlib.Path(raw)
def signature(st):
 return [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns]
def copy_once(source,target):
 source=pathlib.Path(source);target=pathlib.Path(target)
 before=source.stat()
 if target.exists():raise FileExistsError("Existing destination preserved")
 target.parent.mkdir(parents=True,exist_ok=True)
 temp=target.with_name("upload_"+uuid.uuid4().hex[:16]+".partial")
 h=hashlib.sha256();written=0
 try:
  with source.open("rb") as src,temp.open("xb") as dst:
   while True:
    block=src.read(4*1024*1024)
    if not block:break
    dst.write(block);h.update(block);written+=len(block)
  if signature(before)!=signature(source.stat()) or written!=before.st_size:
   raise RuntimeError("Source changed during transfer; original retained")
  os.rename(temp,target)
 except BaseException:
  if temp.exists():temp.unlink()
  raise
 return signature(before),h.hexdigest(),written
def make_plan(persistent,out):
 items={}
 def add(raw,all_files=False):
  if permitted(raw,all_files):
   p=str(pathlib.PureWindowsPath(raw));items.setdefault(p.casefold(),p)
 for name in ["plan/source-packages.jsonl","inventory/new-source-files.jsonl"]:
  p=out/name
  if not p.is_file():raise RuntimeError("Required prior inventory missing")
  for line in p.open(encoding="utf-8-sig"):
   try:
    row=json.loads(line);raw=row.get("source",row.get("path"))
    if raw:add(raw)
    for side in row.get("sidecars",[]):add(side["source"])
   except (ValueError,KeyError,TypeError):continue
 data=json.loads((out/"plan/bulk-import-summary.json").read_text(encoding="utf-8-sig"))
 for row in data.get("rawSources",[]):add(row["path"])
 roots=[r"D:\ANOMALIA\FabImports",r"C:\sketchfab",r"D:\ANOMALIA\sketchfab",r"D:\ANOMALIA\SketchfabExtracted",r"D:\ANOMALIA\StorageRecovery",r"D:\ANOMALIA\unreal\Content",r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\CitySample_5.8\data"]
 for root in roots:
  if not pathlib.Path(root).is_dir():continue
  for base,dirs,names in os.walk(root,followlinks=False):
   dirs[:]=[d for d in dirs if d.casefold() not in SKIP and not (getattr((pathlib.Path(base)/d).lstat(),"st_file_attributes",0)&0x400)]
   for name in names:add(str(pathlib.Path(base)/name),True)
 ordered=sorted(items.values(),key=lambda x:(0 if "citysample" in x.casefold() else 1,x.casefold()))
 tmp=persistent/"direct-source-plan.tmp"
 with tmp.open("w",encoding="utf-8") as f:
  for p in ordered:f.write(json.dumps({"path":p})+"\n")
 os.replace(tmp,persistent/"direct-source-plan.jsonl")
 return len(ordered)
def main():
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 persistent=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CloudTransfer\Direct20261106");persistent.mkdir(parents=True,exist_ok=True)
 dest=pathlib.Path(r"H:\Mon Drive\ANOMALIAZ\02_Modeles_3D\Transfert_Direct_20261106")
 summary={"state":"PREPARING","batch":os.environ.get("GITHUB_RUN_ID"),"mode":"DIRECT_FOLDER_COPY_DUPLICATES_ACCEPTED","cloudFolderId":"1a9GemSBLXFkNlw4n_mhm8O4OC8SLhQra","originalFilesDeleted":0,"originalFilesModified":0,"remoteServerVerificationPending":True,"newFilesWrittenToDriveClient":0,"newBytesWrittenToDriveClient":0,"resumedUnchangedPaths":0,"missingSourcePaths":0,"deferred":0,"errors":[]}
 last_save=0
 def save():
  nonlocal last_save
  summary["reportedAtUTC"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
  (persistent/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
  (out/"direct-transfer-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
  try:
   if dest.is_dir():
    temp=dest/("progress_"+uuid.uuid4().hex[:12]+".tmp")
    temp.write_text(json.dumps(summary,indent=2),encoding="utf-8");os.replace(temp,dest/"direct-transfer-progress.json")
  except OSError:pass
  last_save=time.monotonic()
 if (persistent/"summary.json").exists():
  previous=json.loads((persistent/"summary.json").read_text(encoding="utf-8"))
  if previous.get("state")=="ALL_LOCAL_COPIES_WRITTEN_SERVER_VERIFICATION_PENDING":
   summary.update(previous);summary["state"]="ALL_LOCAL_COPIES_WRITTEN_SERVER_VERIFICATION_PENDING";save();return
 save()
 for _ in range(12):
  if dest.is_dir():break
  time.sleep(5)
 if not dest.is_dir():raise RuntimeError("Connector-created cloud folder unavailable; originals retained")
 plan=persistent/"direct-source-plan.jsonl"
 if not plan.exists():summary["plannedSourcePaths"]=make_plan(persistent,out)
 db=sqlite3.connect(persistent/"written-paths.sqlite3")
 db.execute("CREATE TABLE IF NOT EXISTS copied(path TEXT PRIMARY KEY, signature TEXT, cloudPath TEXT, sha256 TEXT, bytes INTEGER)")
 db.commit()
 deadline=time.monotonic()+285*60
 summary["state"]="COPYING_CITY_SAMPLE_FIRST";save()
 processed=0
 with (persistent/"direct-copy-receipts.jsonl").open("a",encoding="utf-8") as journal:
  for line in plan.open(encoding="utf-8"):
   if time.monotonic()>deadline:summary["state"]="BATCH_TIME_LIMIT_AUTOMATIC_RESUME";break
   raw=json.loads(line)["path"];source=io_path(raw);key=raw.casefold()
   try:
    if not source.is_file():summary["missingSourcePaths"]+=1;continue
    st=source.stat()
    if getattr(st,"st_file_attributes",0)&(0x1000|0x400000):summary["deferred"]+=1;continue
    sig=signature(st);prior=db.execute("SELECT signature,cloudPath FROM copied WHERE path=?",(key,)).fetchone()
    if prior and json.loads(prior[0])==sig:
     existing=io_path(prior[1])
     if existing.is_file() and existing.stat().st_size==st.st_size:
      summary["resumedUnchangedPaths"]+=1;continue
    free=shutil.disk_usage("C:/").free
    if free<st.st_size+768*1024**2 or shutil.disk_usage("H:/").free<st.st_size+256*1024**2:
     summary["deferred"]+=1;continue
    relative=target_relative(raw);plain_target=dest/relative
    if io_path(plain_target).exists():plain_target=dest/"Versions"/(os.environ["GITHUB_RUN_ID"]+"_"+uuid.uuid4().hex[:8])/relative
    target=io_path(plain_target)
    sig,digest,size=copy_once(source,target)
    receipt={"source":raw,"cloudPath":str(plain_target),"bytes":size,"sha256":digest,"sourceSignature":sig,"state":"DIRECT_CLIENT_COPY_COMPLETE_SERVER_VERIFICATION_PENDING"}
    journal.write(json.dumps(receipt)+"\n");journal.flush()
    db.execute("INSERT OR REPLACE INTO copied VALUES(?,?,?,?,?)",(key,json.dumps(sig),str(plain_target),digest,size));db.commit()
    summary["newFilesWrittenToDriveClient"]+=1;summary["newBytesWrittenToDriveClient"]+=size
   except Exception as e:
    if len(summary["errors"])<100:summary["errors"].append({"path":raw,"error":str(e)})
   finally:
    processed+=1
    if time.monotonic()-last_save>=15:
     summary["sourcePathsProcessedThisBatch"]=processed
     row=db.execute("SELECT COUNT(*),COALESCE(SUM(bytes),0) FROM copied").fetchone()
     summary["totalSourcePathsWritten"]=row[0];summary["totalLogicalBytesWritten"]=row[1];save()
  else:
   summary["state"]="ALL_LOCAL_COPIES_WRITTEN_SERVER_VERIFICATION_PENDING" if not summary["deferred"] and not summary["errors"] and not summary["missingSourcePaths"] else "PARTIAL_AUTOMATIC_RESUME_REQUIRED"
 row=db.execute("SELECT COUNT(*),COALESCE(SUM(bytes),0) FROM copied").fetchone();db.close()
 summary["totalSourcePathsWritten"]=row[0];summary["totalLogicalBytesWritten"]=row[1];summary["sourcePathsProcessedThisBatch"]=processed;save()
 print("DIRECT_TRANSFER_RESULT "+json.dumps(summary),flush=True)
if __name__=="__main__":main()
