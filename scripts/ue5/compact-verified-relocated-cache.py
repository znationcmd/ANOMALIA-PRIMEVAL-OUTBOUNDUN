"""Compress only the already relocated compilation cache; verify all original hashes."""
import pathlib,os,json,shutil,subprocess,hashlib
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def main():
 target=pathlib.Path(r"D:\ANOMALIAZ\03_Caches_Unreal\Archived_Intermediate_42349128791")
 original=pathlib.Path(r"C:\ANOMALIA_MISSION_ARCHIVE_m41798670858\unreal\Intermediate")
 receipt=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CSpaceRecovery\intermediate-relocation-42349128791.json")
 data=json.loads(receipt.read_text(encoding="utf-8"))
 if str(target)!=data["target"] or not target.is_dir() or not os.path.samefile(original,target):raise RuntimeError("Approved cache junction or receipt changed")
 before=shutil.disk_usage("D:/").free
 result=subprocess.run(["compact.exe","/C","/S:"+str(target),"/A","/I","/Q"],capture_output=True,text=True)
 for rel,row in data["files"].items():
  if sha(target/rel)!=row["sha256"]:raise RuntimeError("Cache content mismatch after compression")
 report={"target":str(target),"filesHashVerified":len(data["files"]),"compactExitCode":result.returncode,"DFreeBefore":before,"DFreeAfter":shutil.disk_usage("D:/").free,"CFreeAfter":shutil.disk_usage("C:/").free,"gameContentModified":0,"saveFilesModified":0,"junctionVerified":os.path.samefile(original,target)}
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"])
 (out/"cache-compression-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("VERIFIED_CACHE_COMPRESSION "+json.dumps(report),flush=True)
if __name__=="__main__":main()
