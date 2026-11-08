"""Release only regenerable filesystem DDC cache files; never assets, Zen DB or project sources."""
import pathlib,os,json,shutil,time
OUT=pathlib.Path(os.environ["DDC_CLEANUP_OUT"])
ROOTS=[pathlib.Path(os.environ["LOCALAPPDATA"])/"UnrealEngine/Common/DerivedDataCache",pathlib.Path(r"C:\ANOMALIA_MISSION_41801391717\unreal\DerivedDataCache"),pathlib.Path(r"D:\ANOMALIA\unreal\DerivedDataCache")]
ALLOWED={".udd",".ddc",".ddp",".cache"}
def permitted(path,root):
 if path.suffix.lower() not in ALLOWED:return False
 if any(getattr(p.lstat(),"st_file_attributes",0)&0x400 for p in [root,*path.parents] if p.exists() and (p==root or root in p.parents)):return False
 return path.is_file() and not getattr(path.lstat(),"st_file_attributes",0)&0x400 and path.resolve().is_relative_to(root.resolve())
def main():
 OUT.mkdir(parents=True,exist_ok=True);report={"cacheFilesDeleted":0,"cacheBytesDeleted":0,"modelsDeleted":0,"mapsDeleted":0,"zenDatabaseDeleted":False,"errors":[],"freeBefore":{d:shutil.disk_usage(d+":/").free for d in ["C","D"]}}
 journal=OUT/"regenerable-ddc-deletions.jsonl"
 started=time.monotonic()
 for root in ROOTS:
  if not root.is_dir() or getattr(root.lstat(),"st_file_attributes",0)&0x400:continue
  for base,dirs,names in os.walk(root,followlinks=False):
   dirs[:]=[d for d in dirs if not getattr((pathlib.Path(base)/d).lstat(),"st_file_attributes",0)&0x400]
   for name in names:
    if time.monotonic()-started>15*60:break
    path=pathlib.Path(base)/name
    try:
     if not permitted(path,root):continue
     before=path.stat()
     with journal.open("a",encoding="utf-8") as f:f.write(json.dumps({"path":str(path),"bytes":before.st_size,"kind":"REGENERABLE_DDC_CACHE"})+"\n");f.flush();os.fsync(f.fileno())
     path.unlink();report["cacheFilesDeleted"]+=1;report["cacheBytesDeleted"]+=before.st_size
    except Exception as exc:report["errors"].append({"path":str(path),"error":str(exc)})
   report["freeNow"]={d:shutil.disk_usage(d+":/").free for d in ["C","D"]}
   (OUT/"regenerable-ddc-cleanup.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 report["freeNow"]={d:shutil.disk_usage(d+":/").free for d in ["C","D"]}
 (OUT/"regenerable-ddc-cleanup.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("GENERATED_DDC_CLEANUP "+json.dumps(report),flush=True)
if __name__=="__main__":main()
