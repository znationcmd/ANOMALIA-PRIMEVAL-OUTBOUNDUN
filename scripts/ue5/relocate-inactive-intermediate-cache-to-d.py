"""Relocate inactive archived Unreal Intermediate cache with full verification and a junction."""
import os,pathlib,stat,json,hashlib,shutil,subprocess,uuid,time
SOURCE=pathlib.Path(r"C:\ANOMALIA_MISSION_ARCHIVE_m41798670858\unreal\Intermediate")
CACHE_ROOT=pathlib.Path(r"D:\ANOMALIAZ\03_Caches_Unreal")
PROTECTED={".uasset",".umap",".fbx",".glb",".gltf",".blend",".sav",".uproject"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def ident(st):return [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns]
def snapshot(root):
 root=pathlib.Path(root)
 if getattr(root.lstat(),"st_file_attributes",0)&0x400 or root.is_symlink():raise ValueError("Reparse source root; leave it intact")
 result={}
 for base,dirs,names in os.walk(root,followlinks=False):
  for name in dirs:
   p=pathlib.Path(base)/name
   if getattr(p.lstat(),"st_file_attributes",0)&0x400 or p.is_symlink():raise ValueError("Reparse directory inside cache")
  for name in names:
   p=pathlib.Path(base)/name;s=p.lstat()
   if not stat.S_ISREG(s.st_mode) or p.is_symlink() or getattr(s,"st_file_attributes",0)&0x400:raise ValueError("Non-regular file in cache")
   if p.suffix.lower() in PROTECTED:raise ValueError("Protected content unexpectedly present in Intermediate")
   if s.st_nlink!=1:raise ValueError("Shared file; moving this cache would not reclaim expected space")
   result[str(p.relative_to(root))]={"identity":ident(s),"bytes":s.st_size}
 return result
def verified_copy(root,dest,manifest):
 root=pathlib.Path(root);dest=pathlib.Path(dest)
 if dest.exists():raise FileExistsError("Never overwrite an existing cache destination")
 dest.mkdir(parents=True)
 for rel,row in manifest.items():
  source=root/rel;target=dest/rel
  if ident(source.stat())!=row["identity"]:raise RuntimeError("Source changed before copy")
  expected=sha(source)
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
  if sha(target)!=expected or ident(source.stat())!=row["identity"]:raise RuntimeError("Cache copy mismatch; original preserved")
  row["sha256"]=expected
 fresh=snapshot(root)
 if {k:v["identity"] for k,v in fresh.items()}!={k:v["identity"] for k,v in manifest.items()}:raise RuntimeError("Source tree changed; original preserved")
def active_build_processes():
 command="Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -match '^(UnrealEditor|UnrealEditor-Cmd|UnrealBuildTool|ShaderCompileWorker|cl|link|MSBuild)$'} | ForEach-Object {$_.ProcessName}"
 output=subprocess.check_output(["powershell.exe","-NoProfile","-NonInteractive","-Command",command],text=True)
 return [x.strip() for x in output.splitlines() if x.strip()]
def create_junction(source,target):
 def quote(s):return "'"+str(s).replace("'","''")+"'"
 command="$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path "+quote(source)+" -Target "+quote(target)+" | Out-Null"
 subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",command],check=True)
def main():
 if os.name!="nt":raise RuntimeError("This operation is Windows-only")
 if active_build_processes():raise RuntimeError("Unreal or compiler active; cache left in place")
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 persistent=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CSpaceRecovery");persistent.mkdir(parents=True,exist_ok=True)
 report={"source":str(SOURCE),"CFreeBefore":shutil.disk_usage("C:/").free,"DFreeBefore":shutil.disk_usage("D:/").free,"gameContentModified":0,"sourceCodeModified":0,"saveFilesModified":0,"driveCacheModified":0,"originalCacheContentsPreserved":True}
 if not SOURCE.is_dir():raise RuntimeError("Approved archived Intermediate cache not present")
 if getattr(SOURCE.lstat(),"st_file_attributes",0)&0x400:
  report.update({"state":"ALREADY_REDIRECTED_NO_CHANGE","target":str(SOURCE.resolve())})
  (out/"c-space-recovery-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print("C_SPACE_RECOVERY "+json.dumps(report),flush=True);return
 manifest=snapshot(SOURCE);total=sum(r["bytes"] for r in manifest.values())
 if not total:raise RuntimeError("No cache bytes to relocate")
 if shutil.disk_usage("D:/").free<total+6*1024**3:raise RuntimeError("Preserve 6 GiB D reserve; relocation not started")
 run=os.environ["GITHUB_RUN_ID"];target=CACHE_ROOT/("Archived_Intermediate_"+run);CACHE_ROOT.mkdir(parents=True,exist_ok=True)
 report.update({"target":str(target),"files":len(manifest),"cacheBytes":total,"state":"COPYING_ORIGINAL_INTACT"})
 verified_copy(SOURCE,target,manifest)
 durable=persistent/("intermediate-relocation-"+run+".json")
 durable.write_text(json.dumps({"source":str(SOURCE),"target":str(target),"files":manifest},indent=2),encoding="utf-8")
 if active_build_processes():raise RuntimeError("Build started during copy; original cache preserved")
 stash=SOURCE.with_name("Intermediate_verified_move_"+uuid.uuid4().hex[:12])
 os.rename(SOURCE,stash)
 try:
  create_junction(SOURCE,target)
  if not SOURCE.is_dir() or not os.path.samefile(SOURCE,target):raise RuntimeError("Junction verification failed")
  for rel,row in manifest.items():
   if (SOURCE/rel).stat().st_size!=row["bytes"] or ident((stash/rel).stat())!=row["identity"]:raise RuntimeError("Final cache path validation failed")
 except BaseException:
  if SOURCE.exists() and getattr(SOURCE.lstat(),"st_file_attributes",0)&0x400:os.rmdir(SOURCE)
  if not SOURCE.exists():os.rename(stash,SOURCE)
  raise
 # Every byte in this inactive generated cache is verified at target; original paths now resolve there.
 try:
  for rel,row in manifest.items():
   p=stash/rel
   if ident(p.stat())!=row["identity"]:raise RuntimeError("Retained cache entry changed; stop releasing old copy")
   p.unlink()
  for base,dirs,names in os.walk(stash,topdown=False):
   pathlib.Path(base).rmdir()
  report["state"]="VERIFIED_CACHE_RELOCATED_PATH_PRESERVED"
 except Exception as error:
  report["state"]="VERIFIED_TARGET_ACTIVE_OLD_STASH_PARTLY_RETAINED";report["retainedStash"]=str(stash);report["cleanupError"]=str(error)
 report.update({"CFreeAfter":shutil.disk_usage("C:/").free,"DFreeAfter":shutil.disk_usage("D:/").free,"junctionVerified":True})
 report["measuredCFreeDelta"]=report["CFreeAfter"]-report["CFreeBefore"]
 (persistent/("recovery-summary-"+run+".json")).write_text(json.dumps(report,indent=2),encoding="utf-8")
 (out/"c-space-recovery-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("C_SPACE_RECOVERY "+json.dumps(report),flush=True)
if __name__=="__main__":main()
