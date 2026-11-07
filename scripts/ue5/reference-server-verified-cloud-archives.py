"""Retain ZIP paths as cloud references only after independent remote verification."""
import pathlib,hashlib,os,json,uuid,shutil
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for b in iter(lambda:stream.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def reference_verified_archive(source,cloud,expected,size,allowed_root):
 source=pathlib.Path(source);cloud=pathlib.Path(cloud);root=pathlib.Path(allowed_root).resolve()
 if source.parent.resolve()!=root or source.suffix.lower()!=".zip":raise ValueError("Only approved original ZIP source folder is eligible")
 if source.is_symlink():return "ALREADY_REFERENCED"
 before=source.stat()
 if before.st_nlink!=1:return "SHARED_LOCAL_ARCHIVE_PRESERVED"
 if source.name!=cloud.name or not cloud.is_file() or cloud.stat().st_size!=size:raise ValueError("Cloud path unavailable or changed")
 if before.st_size!=size or digest(source)!=expected:raise ValueError("Local original differs; preserve it")
 temp=source.with_name(".cloud-reference-"+uuid.uuid4().hex)
 try:
  os.symlink(str(cloud),str(temp))
  if not temp.is_symlink():raise RuntimeError("Windows did not create a real symbolic link")
  current=source.stat()
  if (current.st_ino,current.st_size,current.st_mtime_ns)!=(before.st_ino,before.st_size,before.st_mtime_ns):raise RuntimeError("Source changed; original retained")
  os.replace(temp,source)
  if not source.is_symlink() or source.stat().st_size!=size:raise RuntimeError("Cloud reference validation failed; verified remote original retained")
  return "ZIP_PATH_RETAINED_AS_VERIFIED_CLOUD_REFERENCE"
 finally:
  if temp.is_symlink():temp.unlink() # Only our temporary reference.
def move_verified_cold_zip(source,cloud,expected,size,allowed_root,drive_id):
 source=pathlib.Path(source);cloud=pathlib.Path(cloud);root=pathlib.Path(allowed_root).resolve()
 if source.parent.resolve()!=root or source.suffix.lower()!=".zip" or source.is_symlink():raise ValueError("Only approved cold ZIP is movable")
 before=source.stat()
 if before.st_nlink!=1:return "SHARED_LOCAL_ARCHIVE_PRESERVED"
 if source.name!=cloud.name or not cloud.is_file() or cloud.stat().st_size!=size:raise ValueError("Verified cloud destination changed")
 if before.st_size!=size or digest(source)!=expected:raise ValueError("Changed local original preserved")
 reference=source.with_name(source.name+".cloud.json")
 data={"originalPath":str(source),"cloudPath":str(cloud),"sha256":expected,"bytes":size,"driveFileId":drive_id,"serverChecksumVerified":True}
 if reference.exists():
  if json.loads(reference.read_text(encoding="utf-8"))!=data:raise ValueError("Existing cloud reference differs")
 else:
  with reference.open("x",encoding="utf-8") as f:json.dump(data,f);f.flush();os.fsync(f.fileno())
 pending=source.with_name(".verified-cloud-move-"+uuid.uuid4().hex+".zip")
 os.rename(source,pending)
 try:
  moved=pending.stat()
  if (moved.st_ino,moved.st_size,moved.st_mtime_ns)!=(before.st_ino,before.st_size,before.st_mtime_ns) or digest(pending)!=expected:
   raise RuntimeError("Source changed during move; do not release local data")
  pending.unlink() # Completes a verified move to cloud; never an Unreal package or save.
 except Exception:
  if pending.exists() and not source.exists():os.rename(pending,source)
  raise
 return "VERIFIED_ZIP_MOVED_TO_CLOUD_REFERENCE_RETAINED"
def main():
 expected_root=pathlib.Path(r"C:\sketchfab")
 approved_roots=[expected_root,pathlib.Path(r"D:\ANOMALIA\sketchfab")]
 cloud_root=pathlib.Path(r"H:\Mon Drive\ANOMALIAZ\02_Modeles_3D")
 manifest=json.loads((pathlib.Path(__file__).with_name("verified-cloud-archive-offload-20261105.json")).read_text(encoding="utf-8"))
 if os.environ.get("CLOUD_OFFLOAD_INCLUDE_D")=="1":
  manifest["archives"] += [{**a,"source":str(approved_roots[1]/pathlib.Path(a["source"]).name)} for a in list(manifest["archives"])]
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 journal=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CloudTransfer\20261105\verified-archive-offload.jsonl")
 journal.parent.mkdir(parents=True,exist_ok=True)
 report={"nativeAssetsModified":0,"saveFilesModified":0,"archivePathsRetained":True,"sourceContentsRetainedOnDrive":True,"CFreeBefore":shutil.disk_usage("C:/").free,"DFreeBefore":shutil.disk_usage("D:/").free,"archives":[]}
 for row in manifest["archives"]:
  result=dict(row)
  try:
   source_path=pathlib.Path(row["source"])
   matches=[root for root in approved_roots if source_path.parent.resolve()==root.resolve()]
   if not matches:raise ValueError("Unapproved archive source root; preserve original")
   expected_root=matches[0]
   if not row["remoteServerSHA256Verified"]:raise ValueError("Missing independent server checksum verification")
   if not pathlib.Path(row["cloudPath"]).resolve().is_relative_to(cloud_root.resolve()):raise ValueError("Unexpected cloud account folder")
   with journal.open("a",encoding="utf-8") as f:
    f.write(json.dumps({**row,"state":"VERIFIED_OFFLOAD_PREPARED"})+"\n");f.flush();os.fsync(f.fileno())
   # Durable import catalogue precedes any move of a verified cold archive.
   catalog_path=pathlib.Path(r"D:\ANOMALIA\unreal\SourceAssets\ExternalResources")/("original-source-catalog-cloud-offload-"+os.environ["GITHUB_RUN_ID"]+".json")
   catalog_path.parent.mkdir(parents=True,exist_ok=True)
   catalog={"mode":"REFERENCE_ORIGINALS_NO_PAYLOAD_COPY","files":[{"source":a["source"],"importSource":a["cloudPath"],"bytes":a["bytes"],"sha256":a["sha256"],"state":"ORIGINAL_SOURCE_REFERENCED_NO_COPY"} for a in manifest["archives"]]}
   with catalog_path.open("w",encoding="utf-8") as f:json.dump(catalog,f,indent=2);f.flush();os.fsync(f.fileno())
   if digest(pathlib.Path(row["cloudPath"]))!=row["sha256"]:raise ValueError("Cloud contents changed since independent server verification")
   try:
    result["state"]=reference_verified_archive(row["source"],row["cloudPath"],row["sha256"],row["bytes"],expected_root)
   except OSError as error:
    if getattr(error,"winerror",None)!=1314:raise
    result["state"]=move_verified_cold_zip(row["source"],row["cloudPath"],row["sha256"],row["bytes"],expected_root,row["driveFileId"])
    report["archivePathsRetained"]=False

  except Exception as e:result["state"]="ORIGINAL_PRESERVED";result["error"]=str(e)
  report["archives"].append(result)
  with journal.open("a",encoding="utf-8") as f:f.write(json.dumps(result)+"\n");f.flush()
 report["DFreeAfter"]=shutil.disk_usage("D:/").free
 report["measuredDFreeDelta"]=report["DFreeAfter"]-report["DFreeBefore"]
 report["CFreeAfter"]=shutil.disk_usage("C:/").free
 report["measuredCFreeDelta"]=report["CFreeAfter"]-report["CFreeBefore"]
 report["resumeReserveAvailable"]=report["CFreeAfter"]>=2*1024**3
 (out/"verified-archive-offload.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("VERIFIED_ARCHIVE_OFFLOAD "+json.dumps(report),flush=True)
if __name__=="__main__":main()
