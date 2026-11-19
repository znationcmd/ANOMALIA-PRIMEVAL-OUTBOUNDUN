"""Release only two old, regenerable PCH cache files from the archived validation build."""
import os,pathlib,json,stat,subprocess,shutil,uuid
ROOT=pathlib.Path(r"D:\ANOMALIAZ\03_Caches_Unreal\Archived_Intermediate_42349128791")
ORIGINAL=pathlib.Path(r"C:\ANOMALIA_MISSION_ARCHIVE_m41798670858\unreal\Intermediate")
RECEIPT=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CSpaceRecovery\intermediate-relocation-42349128791.json")
FILES=[
 r"Build\Win64\x64\AnomaliaZPrigimaliaEditor\Development\UnrealEd\SharedPCH.UnrealEd.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_6.h.pch",
 r"Build\Win64\x64\AnomaliaZPrigimalia\Development\Engine\SharedPCH.Engine.Project.ValApi.ValExpApi.Cpp20.InclOrderUnreal5_6.h.pch"
]
def release_pch(path,root,expected):
 path=pathlib.Path(path);root=pathlib.Path(root)
 if path.suffix.lower()!=".pch" or not path.resolve().is_relative_to(root.resolve()):raise ValueError("Only approved PCH cache entries")
 st=path.lstat()
 if not stat.S_ISREG(st.st_mode) or path.is_symlink() or getattr(st,"st_file_attributes",0)&0x400 or st.st_nlink!=1:raise ValueError("Linked or nonregular cache entry preserved")
 if st.st_size!=expected["bytes"] or st.st_mtime_ns!=expected["identity"][3]:raise ValueError("Changed cache preserved")
 identity=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 pending=path.with_name(".generated-pch-release-"+uuid.uuid4().hex)
 os.rename(path,pending)
 try:
  now=pending.stat()
  if (now.st_dev,now.st_ino,now.st_size,now.st_mtime_ns)!=identity:raise RuntimeError("Cache entry changed during release")
  pending.unlink()
 except BaseException:
  if pending.exists() and not path.exists():os.rename(pending,path)
  raise
 return st.st_size
def main():
 command="Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -match '^(UnrealEditor|UnrealEditor-Cmd|UnrealBuildTool|ShaderCompileWorker|cl|link|MSBuild)$'} | ForEach-Object {$_.ProcessName}"
 if subprocess.check_output(["powershell.exe","-NoProfile","-NonInteractive","-Command",command],text=True).strip():raise RuntimeError("Compiler or editor active; generated caches preserved")
 data=json.loads(RECEIPT.read_text(encoding="utf-8"))
 if data["target"]!=str(ROOT) or not os.path.samefile(ROOT,ORIGINAL):raise RuntimeError("Approved archived-cache path changed")
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 persistent=RECEIPT.parent
 report={"DFreeBefore":shutil.disk_usage("D:/").free,"CFreeBefore":shutil.disk_usage("C:/").free,"releasedFiles":[],"errors":[],"gameAssetsModified":0,"sourceCodeModified":0,"saveFilesModified":0,"rebuildMethod":"Unreal Build Tool regenerates these precompiled headers from preserved engine and project source"}
 journal=persistent/("generated-pch-cleanup-"+os.environ["GITHUB_RUN_ID"]+".jsonl")
 with journal.open("x",encoding="utf-8") as ledger:
  for rel in FILES:
   path=ROOT/rel
   if not path.exists():continue
   try:
    row=data["files"][rel]
    ledger.write(json.dumps({"path":str(path),"bytes":row["bytes"],"state":"REGENERABLE_PCH_PREPARED"})+"\n");ledger.flush();os.fsync(ledger.fileno())
    size=release_pch(path,ROOT,row)
    item={"path":str(path),"bytes":size,"state":"REGENERABLE_PCH_RELEASED"};report["releasedFiles"].append(item)
    ledger.write(json.dumps(item)+"\n");ledger.flush();os.fsync(ledger.fileno())
   except Exception as e:report["errors"].append({"path":str(path),"error":str(e)})
 report["DFreeAfter"]=shutil.disk_usage("D:/").free;report["CFreeAfter"]=shutil.disk_usage("C:/").free
 report["measuredDFreeDelta"]=report["DFreeAfter"]-report["DFreeBefore"]
 (out/"generated-pch-cleanup-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 (persistent/("generated-pch-cleanup-summary-"+os.environ["GITHUB_RUN_ID"]+".json")).write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("GENERATED_PCH_CLEANUP "+json.dumps(report),flush=True)
if __name__=="__main__":main()
