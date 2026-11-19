"""Release only inactive legacy .udd cache files; preserve game content and Zen storage."""
import os,pathlib,stat,time,json,shutil
def eligible(path,cutoff):
 st=path.lstat()
 return (path.suffix.lower()==".udd" and stat.S_ISREG(st.st_mode)
         and not (getattr(st,"st_file_attributes",0)&0x400)
         and st.st_nlink==1 and st.st_mtime<cutoff)
def main():
 import subprocess
 active=subprocess.check_output(["tasklist.exe","/FO","CSV","/NH"],text=True).lower()
 if any(name in active for name in ["unrealeditor.exe","unrealeditor-cmd.exe","unrealbuildtool.exe","shadercompileworker.exe"]):
  raise RuntimeError("Unreal process active; cache left intact")
 root=pathlib.Path(os.environ["LOCALAPPDATA"])/"UnrealEngine/Common/DerivedDataCache"
 rootstat=root.lstat()
 if root.is_symlink() or getattr(rootstat,"st_file_attributes",0)&0x400:
  raise RuntimeError("Cache root reparse point; no cleanup")
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"])
 receipt=out/"legacy-ddc-cleanup.jsonl"
 persistent=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CloudTransfer\20261105")
 persistent.mkdir(parents=True,exist_ok=True)
 cutoff=time.time()-3600
 before=shutil.disk_usage("C:/").free;released=0;count=0
 with (persistent/("legacy-ddc-cleanup-"+os.environ["GITHUB_RUN_ID"]+".jsonl")).open("x",encoding="utf-8") as journal:
  for base,dirs,names in os.walk(root,followlinks=False):
   dirs[:]=[d for d in dirs if not ((pathlib.Path(base)/d).lstat().st_file_attributes&0x400)]
   for name in names:
    p=pathlib.Path(base)/name
    if not eligible(p,cutoff):continue
    st=p.lstat()
    prepared={"path":str(p),"bytes":st.st_size,"mtime_ns":st.st_mtime_ns,"state":"REGENERABLE_UDD_PREPARED"}
    journal.write(json.dumps(prepared)+"\n");journal.flush()
    if not eligible(p,cutoff) or p.lstat().st_mtime_ns!=st.st_mtime_ns:continue
    try:p.unlink()
    except OSError:continue
    released+=st.st_size;count+=1
    journal.write(json.dumps({"path":str(p),"state":"REGENERABLE_UDD_RELEASED"})+"\n");journal.flush()
  journalname=journal.name
 shutil.copyfile(journalname,receipt)
 result={"cacheRoot":str(root),"filesReleased":count,"logicalBytesReleased":released,"CFreeBefore":before,"CFreeAfter":shutil.disk_usage("C:/").free,"gameAssetsModified":0,"saveFilesModified":0,"zenStorageModified":0,"rebuildRequiredOnNextUse":True}
 (out/"legacy-ddc-cleanup-summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
 print("LEGACY_DDC_RESULT "+json.dumps(result),flush=True)
if __name__=="__main__":main()
