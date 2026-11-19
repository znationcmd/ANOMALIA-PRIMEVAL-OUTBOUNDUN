"""Remove exact duplicate cold game archives; never edit native assets or saves."""
import os,pathlib,json,hashlib,stat,uuid,time,shutil
EXT={".zip",".7z",".rar"}
def digest(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def allowed(p,roots):
 p=pathlib.Path(p)
 try:
  if p.is_symlink() or p.suffix.lower() not in EXT:return False
  st=p.lstat()
  if not stat.S_ISREG(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:return False
  resolved=p.resolve()
  return any(resolved.is_relative_to(r.resolve()) for r in roots)
 except OSError:return False
def retire_duplicate(copy,canonical,expected,ledger):
 copy=pathlib.Path(copy);canonical=pathlib.Path(canonical)
 before=copy.stat();other=canonical.stat()
 if before.st_nlink!=1:return "SHARED_ARCHIVE_PRESERVED"
 if (before.st_dev,before.st_ino)==(other.st_dev,other.st_ino):return "SAME_PHYSICAL_FILE_PRESERVED"
 if before.st_size!=other.st_size or digest(copy)!=expected or digest(canonical)!=expected:raise ValueError("Files differ; preserve both")
 reference=copy.with_name(copy.name+".duplicate.json")
 data={"originalPath":str(copy),"retainedOriginalPath":str(canonical),"bytes":before.st_size,"sha256":expected,"reason":"EXACT_DUPLICATE_COLD_ARCHIVE","restore":"Copy retainedOriginalPath back to originalPath"}
 if reference.exists():
  if json.loads(reference.read_text(encoding="utf-8"))!=data:raise ValueError("Different existing restore reference")
 else:
  with reference.open("x",encoding="utf-8") as f:json.dump(data,f);f.flush();os.fsync(f.fileno())
 ledger.write(json.dumps({**data,"state":"PREPARED"})+"\n");ledger.flush();os.fsync(ledger.fileno())
 pending=copy.with_name(".verified-duplicate-"+uuid.uuid4().hex+copy.suffix)
 os.rename(copy,pending)
 try:
  now=pending.stat();retained=canonical.stat()
  if (now.st_ino,now.st_size,now.st_mtime_ns)!=(before.st_ino,before.st_size,before.st_mtime_ns):raise ValueError("Candidate changed")
  if (retained.st_ino,retained.st_size,retained.st_mtime_ns)!=(other.st_ino,other.st_size,other.st_mtime_ns):raise ValueError("Retained original changed")
  if digest(pending)!=expected or digest(canonical)!=expected:raise ValueError("Checksum changed")
  pending.unlink()
 except Exception:
  if pending.exists() and not copy.exists():os.rename(pending,copy)
  raise
 ledger.write(json.dumps({**data,"state":"DUPLICATE_RELEASED_ORIGINAL_RETAINED"})+"\n");ledger.flush();os.fsync(ledger.fileno())
 return "DUPLICATE_RELEASED_ORIGINAL_RETAINED"
def main():
 main=pathlib.Path(r"D:\ANOMALIA\unreal")
 roots=[pathlib.Path(r"C:\sketchfab"),pathlib.Path(r"D:\ANOMALIA\sketchfab"),pathlib.Path(r"D:\ANOMALIA\FabImports"),pathlib.Path(os.environ["LOCALAPPDATA"])/"Temp/FabLibrary"]
 persistent=main/"Saved/CloudTransfer/20261105";persistent.mkdir(parents=True,exist_ok=True)
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 groups={};seen=set()
 # Reuse existing checksummed resource receipts instead of rescanning personal disks.
 for line in (persistent/"resource-transfers.jsonl").open(encoding="utf-8"):
  try:
   r=json.loads(line);p=pathlib.Path(r["path"])
   key=str(p).casefold()
   if key in seen or not allowed(p,roots):continue
   seen.add(key);groups.setdefault(r["sha256"],[]).append(p)
  except (ValueError,KeyError,OSError):continue
 result={"archivesChecked":len(seen),"duplicateGroups":0,"duplicatesReleased":0,"logicalBytesReleased":0,"sharedFilesPreserved":0,"errors":[],"nativeAssetsModified":0,"saveFilesModified":0,"driveCacheModified":0,"originalRetainedPerGroup":True,"CFreeBefore":shutil.disk_usage("C:/").free,"DFreeBefore":shutil.disk_usage("D:/").free}
 deadline=time.monotonic()+20*60
 ledger_path=persistent/("duplicate-archive-cleanup-"+os.environ["GITHUB_RUN_ID"]+".jsonl")
 with ledger_path.open("x",encoding="utf-8") as ledger:
  for expected,paths in groups.items():
   if time.monotonic()>deadline:result["partialTimeLimit"]=True;break
   if len(paths)<2:continue
   result["duplicateGroups"]+=1
   # Keep an already shared archive first: removing its pathname would reclaim no bytes.
   paths.sort(key=lambda p:(p.stat().st_nlink==1,not str(p).lower().startswith("d:"),str(p).casefold()))
   canonical=paths[0]
   for p in paths[1:]:
    if time.monotonic()>deadline:result["partialTimeLimit"]=True;break
    try:
     if not allowed(p,roots) or not allowed(canonical,roots):raise ValueError("Source scope changed")
     size=p.stat().st_size
     state=retire_duplicate(p,canonical,expected,ledger)
     if state=="DUPLICATE_RELEASED_ORIGINAL_RETAINED":result["duplicatesReleased"]+=1;result["logicalBytesReleased"]+=size
     else:result["sharedFilesPreserved"]+=1
    except Exception as e:result["errors"].append({"path":str(p),"error":str(e)})
 shutil.copyfile(ledger_path,out/"duplicate-archive-cleanup.jsonl")
 result["CFreeAfter"]=shutil.disk_usage("C:/").free;result["DFreeAfter"]=shutil.disk_usage("D:/").free
 (out/"duplicate-archive-cleanup-summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
 print("DUPLICATE_ARCHIVE_CLEANUP "+json.dumps(result),flush=True)
if __name__=="__main__":main()
