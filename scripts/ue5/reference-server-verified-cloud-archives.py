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
def main():
 expected_root=pathlib.Path(r"C:\sketchfab")
 cloud_root=pathlib.Path(r"H:\Mon Drive\ANOMALIAZ\02_Modeles_3D")
 manifest=json.loads((pathlib.Path(__file__).with_name("verified-cloud-archive-offload-20261105.json")).read_text(encoding="utf-8"))
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 journal=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CloudTransfer\20261105\verified-archive-offload.jsonl")
 journal.parent.mkdir(parents=True,exist_ok=True)
 report={"nativeAssetsModified":0,"saveFilesModified":0,"archivePathsRetained":True,"sourceContentsRetainedOnDrive":True,"CFreeBefore":shutil.disk_usage("C:/").free,"archives":[]}
 for row in manifest["archives"]:
  result=dict(row)
  try:
   if not row["remoteServerSHA256Verified"]:raise ValueError("Missing independent server checksum verification")
   if not pathlib.Path(row["cloudPath"]).resolve().is_relative_to(cloud_root.resolve()):raise ValueError("Unexpected cloud account folder")
   with journal.open("a",encoding="utf-8") as f:
    f.write(json.dumps({**row,"state":"VERIFIED_OFFLOAD_PREPARED"})+"\n");f.flush();os.fsync(f.fileno())
   result["state"]=reference_verified_archive(row["source"],row["cloudPath"],row["sha256"],row["bytes"],expected_root)
  except Exception as e:result["state"]="ORIGINAL_PRESERVED";result["error"]=str(e)
  report["archives"].append(result)
  with journal.open("a",encoding="utf-8") as f:f.write(json.dumps(result)+"\n");f.flush()
 report["CFreeAfter"]=shutil.disk_usage("C:/").free
 report["measuredCFreeDelta"]=report["CFreeAfter"]-report["CFreeBefore"]
 report["resumeReserveAvailable"]=report["CFreeAfter"]>=2*1024**3
 (out/"verified-archive-offload.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("VERIFIED_ARCHIVE_OFFLOAD "+json.dumps(report),flush=True)
if __name__=="__main__":main()
