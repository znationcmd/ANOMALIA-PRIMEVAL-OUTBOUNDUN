"""Remove only byte-identical unused City Sample VaultCache duplicates; retain independent D originals."""
import pathlib,os,json,hashlib,time,shutil
SOURCE=pathlib.Path(r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\CitySample_5.8\data")
RETAINED=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample")
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
OUT=pathlib.Path(os.environ["CITY_DUPLICATE_OUT"])
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
 return h.hexdigest()
def identity(st):return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
def links_in(root):
 targets=[]
 if not root.is_dir():return targets
 for base,dirs,names in os.walk(root,followlinks=False):
  for name in list(dirs):
   p=pathlib.Path(base)/name
   if getattr(p.lstat(),"st_file_attributes",0)&0x400:
    targets.append(p.resolve());dirs.remove(name)
 return targets
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 report={"source":str(SOURCE),"retained":str(RETAINED),"state":"VERIFYING_LOCAL_INDEPENDENT_DUPLICATES","cloudCompleteVerified":False,"deletedFiles":0,"logicalBytesRemoved":0,"sharedLinkBytesRemoved":0,"missingOrDifferent":0,"protectedFiles":0,"errors":[],"freeBefore":{d:shutil.disk_usage(d+":/").free for d in ["C","D"]}}
 if not SOURCE.is_dir() or not RETAINED.is_dir():
  report["state"]="SOURCE_OR_RETAINED_ROOT_UNAVAILABLE";(OUT/"citysample-duplicate-cleanup.json").write_text(json.dumps(report,indent=2));return
 assert SOURCE.resolve().anchor.casefold()=="c:\\","Unexpected cache volume"
 assert not RETAINED.resolve().is_relative_to(SOURCE.resolve()),"Retained copy points into removable cache"
 protected=[]
 for root in [PROJECT,pathlib.Path(r"C:\ANOMALIA_MISSION_41801391717\unreal"),pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal")]:
  for name in ["Content","Plugins","Source"]:protected.extend(links_in(root/name))
 raw=PROJECT/"Saved/ImportReceipts/RawResume20261107/raw-preparation-manifest.json"
 if raw.exists():
  for row in json.loads(raw.read_text(encoding="utf-8"))["imports"]:
   for key in ["source","prepared"]:
    p=pathlib.Path(row.get(key,""))
    if p.is_file() and p.resolve().is_relative_to(SOURCE.resolve()):protected.append(p.resolve())
 report["protectedTargets"]=[str(p) for p in protected if p.is_relative_to(SOURCE.resolve()) or SOURCE.resolve().is_relative_to(p)]
 journal=OUT/"citysample-local-duplicate-removals.jsonl";started=time.monotonic()
 def checkpoint():
  report["freeNow"]={d:shutil.disk_usage(d+":/").free for d in ["C","D"]}
  (OUT/"citysample-duplicate-cleanup.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
  print("CITYSAMPLE_VERIFIED_DUPLICATES "+json.dumps({k:report[k] for k in ["deletedFiles","logicalBytesRemoved","protectedFiles","missingOrDifferent","freeNow"]}),flush=True)
 for base,dirs,names in os.walk(SOURCE,followlinks=False):
  dirs[:]=[d for d in dirs if not getattr((pathlib.Path(base)/d).lstat(),"st_file_attributes",0)&0x400]
  for name in names:
   if time.monotonic()-started>75*60:report["state"]="TIME_BUDGET_REACHED";checkpoint();return
   source=pathlib.Path(base)/name
   try:
    resolved=source.resolve()
    if any(resolved==p or resolved.is_relative_to(p) for p in protected):report["protectedFiles"]+=1;continue
    before=source.stat()
    if getattr(source.lstat(),"st_file_attributes",0)&0x400:report["protectedFiles"]+=1;continue
    peer=RETAINED/source.relative_to(SOURCE)
    if not peer.is_file() or peer.resolve().is_relative_to(SOURCE.resolve()) or os.path.samefile(source,peer):report["missingOrDifferent"]+=1;continue
    other=peer.stat()
    if getattr(other,"st_file_attributes",0)&(0x1000|0x400000) or before.st_size!=other.st_size:report["missingOrDifferent"]+=1;continue
    digest=sha(source)
    if sha(peer)!=digest:report["missingOrDifferent"]+=1;continue
    if identity(before)!=identity(source.stat()) or identity(other)!=identity(peer.stat()):raise RuntimeError("File changed during comparison; preserved")
    receipt={"sourceRemoved":str(source),"independentRetained":str(peer.resolve()),"sha256":digest,"bytes":before.st_size,"sourceLinkCount":before.st_nlink,"basis":"EXACT_LOCAL_COPY_NOT_UNVERIFIED_CLOUD"}
    with journal.open("a",encoding="utf-8") as f:f.write(json.dumps(receipt)+"\n");f.flush();os.fsync(f.fileno())
    source.unlink();report["deletedFiles"]+=1;report["logicalBytesRemoved"]+=before.st_size
    if before.st_nlink>1:report["sharedLinkBytesRemoved"]+=before.st_size
   except Exception as exc:
    if len(report["errors"])<100:report["errors"].append({"source":str(source),"error":str(exc)})
   if report["deletedFiles"] and report["deletedFiles"]%500==0:checkpoint()
 report["state"]="VERIFIED_LOCAL_DUPLICATES_REMOVED_OTHER_CONTENT_PRESERVED";checkpoint()
if __name__=="__main__":main()
