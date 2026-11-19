"""Lossless compress cold raw FBX/OBJ/BLEND models in existing VaultCache.
The file bytes and project/game paths are preserved; no file deletion or offload.
"""
import pathlib,os,json,time,hashlib,shutil,subprocess,datetime,stat
ROOT=pathlib.Path(r"D:\ANOMALIA\FabImports\VaultCache")
GAME=pathlib.Path(r"D:\ANOMALIA\unreal\Content\Maps\ANOMALIA_Archipelago_v2.umap")
OUT=pathlib.Path(os.environ["VAULT_COMPACT_OUT"])
CANDIDATE_EXT={".fbx",".obj",".blend"}
MAX_LOGICAL=2*1024**3
MIN_BYTES=12*1024**2
MAX_FILES=25
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def active():
 t=subprocess.run(["tasklist.exe","/FO","CSV","/NH"],capture_output=True,text=True,timeout=30)
 if t.returncode:raise RuntimeError("Can't establish process inactivity")
 return any('"'+n+'"' in t.stdout.lower() for n in (
 "unrealeditor.exe","unrealeditor-cmd.exe","unrealbuildtool.exe","shadercompileworker.exe","anomaliprimeval.exe"))
if not GAME.is_file():raise RuntimeError("Protected game map absent")
if not ROOT.is_dir() or ROOT.is_symlink():raise RuntimeError("VaultCache unavailable")
if active():raise RuntimeError("UE process active; abort compression")
if shutil.disk_usage("D:/").free<6*1024**3:raise RuntimeError("Low D space, abort")
OUT.mkdir(parents=True,exist_ok=True)
candidates=[]
for base,dirs,names in os.walk(ROOT,followlinks=False):
 parent=pathlib.Path(base)
 dirs[:]=[d for d in dirs if not (getattr((parent/d).lstat(),"st_file_attributes",0)&0x400)]
 for name in names:
  p=parent/name
  try:
   st=p.lstat()
   attr=getattr(st,"st_file_attributes",0)
   if p.suffix.lower() not in CANDIDATE_EXT or st.st_size<MIN_BYTES or (attr&0xC00):continue
   if st.st_nlink!=1 or time.time()-st.st_mtime<7*86400 or not stat.S_ISREG(st.st_mode):continue
   candidates.append((p,st.st_size))
  except OSError:pass
candidates.sort(key=lambda x:x[1],reverse=True)
report={"state":"COMPRESSING_LOSSLESS","readonlyOriginalGame":True,"deletedFiles":0,"sourceFilesModifiedContent":0,
  "totalCandidateFiles":len(candidates),"logicalBytesTreated":0,"compressedFiles":0,"bytesFreedMeasured":0,
  "files":[],"startUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "freeDBefore":shutil.disk_usage("D:/").free}
poor=0
for p,size in candidates:
 if report["compressedFiles"]>=MAX_FILES or report["logicalBytesTreated"]+size>MAX_LOGICAL:continue
 if time.time()-pathlib.Path(__file__).stat().st_mtime>3600:break
 if shutil.disk_usage("D:/").free<5*1024**3:break
 try:
  initial=p.stat()
  beforeHash=sha(p)
  before=shutil.disk_usage("D:/").free
  cmd=subprocess.run([str(pathlib.Path(os.environ["SystemRoot"])/"System32/compact.exe"),"/C","/I","/F","/Q",str(p)],capture_output=True,text=True,timeout=180)
  afterStat=p.stat()
  afterHash=sha(p)
  if (initial.st_size,initial.st_mtime_ns,beforeHash)!=(afterStat.st_size,afterStat.st_mtime_ns,afterHash):
   raise RuntimeError("Integrity mismatch after NTFS compression; stop to protect data")
  after=shutil.disk_usage("D:/").free
  if cmd.returncode:raise RuntimeError("compact.exe exit "+str(cmd.returncode))
  saved=after-before
  report["files"].append({"relative":str(p.relative_to(ROOT)),"logicalBytes":size,"savedBytes":saved,"sameSHA256":True})
  report["compressedFiles"]+=1
  report["logicalBytesTreated"]+=size
  report["bytesFreedMeasured"]+=saved
  print("VAULT_SOURCE_NTFS_COMPRESSION_FILE "+json.dumps(report["files"][-1]),flush=True)
  if saved<max(size//100,512*1024):poor+=1
  else:poor=0
  if poor>=3:report["state"]="STOPPED_LOW_COMPRESSION_BENEFIT";break
 except Exception as exc:
  report["state"]="STOPPED_SAFE_EXCEPTION"
  report["error"]=str(exc)
  break
report["finishedUTC"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
report["freeDAfter"]=shutil.disk_usage("D:/").free
report["actualDBeforeAfterDelta"]=report["freeDAfter"]-report["freeDBefore"]
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"vaultcache-raw-model-ntfs-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("VAULT_RAW_MODEL_LOSSLESS_RESULT "+json.dumps(report),flush=True)
