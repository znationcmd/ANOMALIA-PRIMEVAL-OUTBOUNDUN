"""Delete only ZIPs whose complete contents still exist byte-for-byte after extraction."""
import pathlib,zipfile,hashlib,json,os,time,stat,shutil
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
OUT=pathlib.Path(os.environ["ZIP_CLEANUP_OUT"])
def sha_file(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
 return h.hexdigest()
def verify_complete(source,folder):
 rows=[];seen=set();root=folder.resolve()
 with zipfile.ZipFile(source) as z:
  for m in z.infolist():
   p=pathlib.PurePosixPath(m.filename.replace("\\","/"))
   if m.is_dir():continue
   if p.is_absolute() or ".." in p.parts or any(":" in s for s in p.parts):raise ValueError("Unsafe source path; archive retained")
   if str(p).casefold() in seen:raise ValueError("Ambiguous archive paths; retained")
   seen.add(str(p).casefold())
   if m.flag_bits&1 or stat.S_IFMT(m.external_attr>>16)==stat.S_IFLNK:raise ValueError("Encrypted or linked member; retained")
   target=folder.joinpath(*p.parts)
   if not target.resolve().is_relative_to(root) or not target.is_file() or target.stat().st_size!=m.file_size:raise ValueError("Missing, excluded or incomplete extracted member: "+str(p))
   h=hashlib.sha256()
   with z.open(m) as f:
    for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
   digest=h.hexdigest()
   if sha_file(target)!=digest:raise ValueError("Extracted member differs: "+str(p))
   rows.append({"path":str(p),"bytes":m.file_size,"sha256":digest})
 if not rows:raise ValueError("Empty ZIP retained")
 return rows
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 ledger=PROJECT/"Saved/ImportReceipts/AllResources20261107/archive-receipts.jsonl"
 report={"deletedArchives":0,"deletedArchiveBytes":0,"retained":[],"errors":[],"modelsDeleted":0,"mapsDeleted":0,"files":[],"freeBefore":{d:shutil.disk_usage(d+":/").free for d in ["C","D"]}}
 started=time.monotonic()
 for line in ledger.open(encoding="utf-8"):
  if time.monotonic()-started>45*60:report["timeBudgetReached"]=True;break
  row=json.loads(line);source=pathlib.Path(row.get("source",""));folder=pathlib.Path(row.get("folder",""))
  if row.get("state")!="VERIFIED_EXTRACTED" or source.suffix.lower()!=".zip" or not source.is_file():continue
  try:
   before=source.stat()
   if getattr(before,"st_file_attributes",0)&(0x400|0x1000|0x400000):raise ValueError("Linked or cloud-only archive retained")
   if source.resolve().is_relative_to(folder.resolve()):raise ValueError("Archive overlaps retained extraction")
   if sha_file(source)!=row["archiveSHA256"]:raise ValueError("Source checksum changed")
   members=verify_complete(source,folder)
   after=source.stat()
   if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError("Source changed during verification")
   if sha_file(source)!=row["archiveSHA256"]:raise ValueError("Source content changed")
   receipt={"state":"COMPLETE_EXTRACTION_REVERIFIED_BEFORE_ZIP_REMOVAL","source":str(source),"archiveSHA256":row["archiveSHA256"],"folder":str(folder),"archiveBytes":after.st_size,"files":members}
   # Persist complete recovery/provenance before deleting only the verified archive.
   reference=source.with_name(source.name+".extracted.json")
   if reference.exists():raise ValueError("Existing cleanup reference retained for review")
   with reference.open("x",encoding="utf-8") as f:json.dump(receipt,f);f.flush();os.fsync(f.fileno())
   source.unlink()
   report["deletedArchives"]+=1;report["deletedArchiveBytes"]+=after.st_size
   report["files"].append({"source":str(source),"bytes":after.st_size,"folder":str(folder),"members":len(members)})
  except Exception as exc:report["retained"].append({"source":str(source),"reason":str(exc)})
  report["freeNow"]={d:shutil.disk_usage(d+":/").free for d in ["C","D"]}
  (OUT/"verified-zip-cleanup.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
  print("VERIFIED_ZIP_CLEANUP "+json.dumps({k:report[k] for k in ["deletedArchives","deletedArchiveBytes","modelsDeleted","mapsDeleted","freeNow"]}),flush=True)
 (OUT/"verified-zip-cleanup.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if __name__=="__main__":main()
