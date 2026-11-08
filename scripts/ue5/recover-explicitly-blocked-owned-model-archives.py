"""Recover explicitly blocked owned ZIP models; no repeated global audit, no source deletion."""
import os,pathlib,json,hashlib,zipfile,time,shutil,importlib.util
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
STATE=PROJECT/"Saved/ImportReceipts/AllResources20261107"
RAW=PROJECT/"Saved/ImportReceipts/RawResume20261107/raw-preparation-manifest.json"
OUT=pathlib.Path(os.environ["RECOVERY_OUT"])
def file_sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
 return h.hexdigest()
def canonical_rows(z,rows):
 unique={};digests={}
 for row in rows:
  key=row["path"].casefold()
  if key in unique:
   prev=unique[key]
   if (prev["size"],prev["crc"])!=(row["size"],row["crc"]):raise ValueError("Same Windows path has different contents")
   def member_sha(name):
    if name not in digests:
     h=hashlib.sha256()
     with z.open(name) as f:
      for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
     digests[name]=h.hexdigest()
    return digests[name]
   if member_sha(prev["zipName"])!=member_sha(row["zipName"]):raise ValueError("Conflicting duplicate member retained")
  else:unique[key]=row
 return list(unique.values())
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location("extract",pathlib.Path(__file__).with_name("extract-all-owned-game-assets.py"));ex=importlib.util.module_from_spec(spec);spec.loader.exec_module(ex)
 summary=json.loads((STATE/"summary.json").read_text(encoding="utf-8"))
 # Treat old memory/disk errors individually; do not rescan all operating-system files.
 candidates={r["archive"] for r in summary.get("blocked",[]) if r.get("archive","").lower().endswith(".zip")}
 report={"archivesRecovered":0,"newRawSources":0,"errors":[],"sources":[],"nativeRootsForReview":[],"originalsDeleted":0,"existingAssetsReplaced":0}
 started=time.monotonic()
 for source in sorted(candidates):
  if time.monotonic()-started>55*60:report["timeBudgetReached"]=True;break
  p=pathlib.Path(source)
  try:
   if not p.is_file():raise FileNotFoundError("Original not resident; retained inventory reference")
   before=p.stat();sha=file_sha(p)
   if getattr(before,"st_file_attributes",0)&(0x400|0x1000|0x400000):raise ValueError("Linked or cloud-only source retained")
   rows,blocked=ex.zip_members(p)
   if blocked:raise ValueError("Unsafe or encrypted members still require explicit path repair")
   with zipfile.ZipFile(p) as z:rows=canonical_rows(z,rows)
   required=sum(r["size"] for r in rows)
   roots=[(PROJECT/"SourceAssets/AllExtracted",12*1024**3),(pathlib.Path(r"C:\ANOMALIA_ResourceRecovery20261108"),8*1024**3)]
   root=None
   for candidate,reserve in roots:
    candidate.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(candidate).free>=required+reserve:root=candidate;break
   if root is None:raise ValueError("Neither disk has measured space for this archive and its reserve")
   folder=root/sha[:20]
   if folder.exists() and getattr(folder.lstat(),"st_file_attributes",0)&0x400:raise ValueError("Existing reparse output preserved")
   folder.mkdir(exist_ok=True);ex.extract_zip(p,folder,rows)
   after=p.stat()
   if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns) or file_sha(p)!=sha:raise ValueError("Original changed during recovery")
   # Read the newest manifest at every checkpoint; never replace another completed discovery batch.
   raw=json.loads(RAW.read_text(encoding="utf-8"));seen={x["sha256"] for x in raw["imports"]}
   added=0
   for row in rows:
    model=folder.joinpath(*pathlib.PurePosixPath(row["path"]).parts)
    if model.suffix.lower() in ex.MODELS:
     digest=file_sha(model)
     if digest not in seen:
      raw["imports"].append({"source":str(model),"prepared":str(model),"sha256":digest,"preparedSHA256":digest,"family":ex.model_family(model,sha),"animationOnly":False})
      seen.add(digest);added+=1
    if model.suffix.lower() in ex.NATIVE:
     parts=pathlib.PurePosixPath(row["path"]).parts
     index=next((i for i,v in enumerate(parts) if v.casefold()=="content"),None)
     if index is not None:
      native=str(folder.joinpath(*parts[:index+1]))
      if native not in report["nativeRootsForReview"]:report["nativeRootsForReview"].append(native)
   tmp=RAW.with_suffix(".recovery.tmp");tmp.write_text(json.dumps(raw,indent=2),encoding="utf-8");os.replace(tmp,RAW)
   receipt={"state":"VERIFIED_EXTRACTED","source":str(p),"archiveSHA256":sha,"folder":str(folder),"files":rows,"categories":ex.categories([r["path"] for r in rows])}
   with (STATE/"archive-receipts.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(receipt)+"\n");f.flush();os.fsync(f.fileno())
   report["archivesRecovered"]+=1;report["newRawSources"]+=added
   report["sources"].append({"source":str(p),"folder":str(folder),"newRawSources":added})
  except Exception as exc:report["errors"].append({"source":str(p),"reason":str(exc)})
  (OUT/"blocked-archive-recovery.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
  print("BLOCKED_ARCHIVE_RECOVERY "+json.dumps({k:report[k] for k in ["archivesRecovered","newRawSources","originalsDeleted"]}),flush=True)
 (OUT/"blocked-archive-recovery.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if __name__=="__main__":main()
