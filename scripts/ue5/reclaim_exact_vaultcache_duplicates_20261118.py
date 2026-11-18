"""Remove only VaultCache assets whose complete SHA256 equals an independent
already-imported native Unreal asset at the same relative Content path.

All game originals and other VaultCache files stay untouched.
Every VaultCache file removed gets a durable restoration receipt.
"""
import os,pathlib,json,hashlib,time,stat,shutil,uuid,datetime,subprocess
VAULT=pathlib.Path(r"D:\ANOMALIA\FabImports\VaultCache")
GAME=pathlib.Path(r"D:\ANOMALIA\unreal\Content")
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
SAMPLE=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample\CitySample.uproject")
OUT=pathlib.Path(os.environ["VAULT_RECLAIM_OUT"])
MAX_BYTES=3*1024**3
MAX_FILES=65
MIN_SIZE=16*1024**2
MIN_D_FREE=5*1024**3
MAX_SECONDS=40*60
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha256(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
def safe_stat(p,root):
 if p.is_symlink():return None
 if not p.is_relative_to(root):return None
 st=p.lstat()
 if not stat.S_ISREG(st.st_mode) or (getattr(st,"st_file_attributes",0)&0x400):return None
 return st
def active_engine():
 r=subprocess.run(["tasklist.exe","/FO","CSV","/NH"],capture_output=True,text=True,timeout=30)
 if r.returncode:raise RuntimeError("Cannot verify process inactivity")
 return any('"'+n+'"' in r.stdout.lower() for n in (
 "unrealeditor.exe","unrealeditor-cmd.exe","unrealbuildtool.exe",
 "shadercompileworker.exe","anomaliprimeval.exe"))
if not (PROJECT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file() or not SAMPLE.is_file():
 raise RuntimeError("Game map or original City Sample missing - abort")
if active_engine():raise RuntimeError("Unreal/game process active; no VaultCache files will be removed")
if shutil.disk_usage("D:/").free<MIN_D_FREE:raise RuntimeError("D disk reserve too low")
if not VAULT.is_dir() or VAULT.is_symlink():raise RuntimeError("VaultCache unavailable")
OUT.mkdir(parents=True,exist_ok=True)
persist=PROJECT/"Saved/CloudTransfer"/"VerifiedVaultCacheDuplicates"
persist.mkdir(parents=True,exist_ok=True)
run=os.environ.get("GITHUB_RUN_ID",uuid.uuid4().hex)
journal=persist/("reclaim-vaultcache-"+run+".jsonl")
report={"state":"SCANNING","startUTC":now(),"sourceScope":str(VAULT),"gameCopyScope":str(GAME),
  "filesRemovedFromVaultCache":0,"bytesOfVerifiedCacheRemoved":0,"gameAssetsDeleted":0,
  "citySampleOriginalFilesDeleted":0,"mapFilesModified":0,"saveFilesDeleted":0,"errors":[],
  "freeDBefore":shutil.disk_usage("D:/").free,"verifiedMatchesScanned":0,"differentContentPreserved":0,
  "skippedOtherFiles":0,"restorationJournal":str(journal)}
candidates=[]
for base,dirs,names in os.walk(VAULT,followlinks=False):
 parent=pathlib.Path(base)
 dirs[:]=[d for d in dirs if not (getattr((parent/d).lstat(),"st_file_attributes",0)&0x400)]
 for name in names:
  p=parent/name
  try:
   s=safe_stat(p,VAULT)
   if s is None or p.suffix.lower() not in (".uasset",".umap") or s.st_nlink!=1 or s.st_size<MIN_SIZE:
    continue
   if time.time()-s.st_mtime<7*86400:continue
   rel=p.relative_to(VAULT);parts=rel.parts
   indexes=[i for i,x in enumerate(parts[:-1]) if x.casefold()=="content"]
   if not indexes:continue
   suffix=pathlib.Path(*parts[indexes[-1]+1:])
   peer=GAME/suffix
   if not peer.is_file():continue
   o=safe_stat(peer,GAME)
   if o is None or o.st_size!=s.st_size:continue
   if (s.st_dev,s.st_ino)==(o.st_dev,o.st_ino):continue
   candidates.append((p,peer,s.st_size))
  except OSError:continue
candidates.sort(key=lambda x:x[2],reverse=True)
report["candidateFiles"]=len(candidates)
report["candidateBytes"]=sum(x[2] for x in candidates)
report["state"]="VERIFYING_AND_RELEASING"
started=time.monotonic()
with journal.open("x",encoding="utf-8") as j:
 for src,peer,size in candidates:
  if report["bytesOfVerifiedCacheRemoved"]+size>MAX_BYTES:continue
  if report["filesRemovedFromVaultCache"]>=MAX_FILES or time.monotonic()-started>MAX_SECONDS:
   report["state"]="PARTIAL_LIMIT_STOP";break
  if shutil.disk_usage("D:/").free<MIN_D_FREE:
   report["state"]="LOW_DISK_RESERVE_STOP";break
  pending=None
  try:
   before=safe_stat(src,VAULT)
   other=safe_stat(peer,GAME)
   if before is None or other is None or before.st_size!=other.st_size or before.st_nlink!=1:continue
   sourceHash=sha256(src);peerHash=sha256(peer)
   report["verifiedMatchesScanned"]+=1
   if sourceHash!=peerHash:
    report["differentContentPreserved"]+=1
    continue
   if identity(before)!=identity(src.stat()) or identity(other)!=identity(peer.stat()):
    raise RuntimeError("Either game or VaultCache source changed during hashing")
   evidence={"vaultcacheRemoved":str(src),"gameCopyRetained":str(peer),
      "logicalBytes":before.st_size,"sha256":sourceHash,"status":"PREPARED","restore":"copy gameCopyRetained to vaultcacheRemoved",
      "dateUTC":now()}
   j.write(json.dumps(evidence)+"\n");j.flush();os.fsync(j.fileno())
   pending=src.with_name(".cache-duplicate-"+uuid.uuid4().hex+src.suffix)
   os.rename(src,pending)
   current=pending.stat()
   if identity(before)!=identity(current) or identity(other)!=identity(peer.stat()):
    raise RuntimeError("File metadata changed after rename")
   # The SHA-verified game copy is still present. Remove only separate VaultCache inode.
   pending.unlink();pending=None
   report["filesRemovedFromVaultCache"]+=1
   report["bytesOfVerifiedCacheRemoved"]+=size
   j.write(json.dumps({**evidence,"status":"VERIFIED_VAULTCACHE_COPY_REMOVED_GAME_COPY_RETAINED"})+"\n");j.flush();os.fsync(j.fileno())
   if report["filesRemovedFromVaultCache"]<=12 or report["filesRemovedFromVaultCache"]%10==0:
    print("VERIFIED_VAULT_CACHE_RELEASED "+json.dumps({"files":report["filesRemovedFromVaultCache"],"bytes":report["bytesOfVerifiedCacheRemoved"],"latestSize":size}),flush=True)
  except Exception as e:
   if pending and pending.exists() and not src.exists():
    try:os.rename(pending,src)
    except OSError:pass
   if len(report["errors"])<25:report["errors"].append({"file":str(src),"error":str(e)})
if report["state"]=="VERIFYING_AND_RELEASING":report["state"]="SAFE_BATCH_FINISHED"
report["finishedUTC"]=now()
report["freeDAfter"]=shutil.disk_usage("D:/").free
report["actualDBytesRecovered"]=report["freeDAfter"]-report["freeDBefore"]
report["gameMapStillPresent"]=(PROJECT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file()
report["citySampleOriginalStillPresent"]=SAMPLE.is_file()
(OUT/"vault-cache-verified-reclaim-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("VAULT_CACHE_VERIFIED_RECLAIM_RESULT "+json.dumps(report),flush=True)
