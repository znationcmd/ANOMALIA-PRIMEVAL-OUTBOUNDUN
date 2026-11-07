"""Copy existing game resources directly to Drive, preserving folders and originals."""
import os,pathlib,json,time,hashlib,sqlite3,uuid,shutil,threading,stat,itertools
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
EXT={".uasset",".umap",".uexp",".ubulk",".uptnl",".fbx",".glb",".gltf",".obj",".blend",".abc",".usd",".usdz",".usda",".usdc",".3ds",".stl",".dae",".zip",".7z",".rar",".png",".jpg",".jpeg",".tga",".bmp",".tif",".tiff",".dds",".exr",".hdr",".psd",".wav",".ogg",".flac",".mp3",".bin",".mtl",".uproject",".uplugin"}
SKIP={".git",".tmp.driveupload","deriveddatacache"}
def permitted(raw,all_files=False):
 p=pathlib.PureWindowsPath(raw)
 return p.drive.casefold() in {"c:","d:"} and not any(x.casefold() in SKIP for x in p.parts) and (all_files or p.suffix.casefold() in EXT)
def target_relative(raw):
 p=pathlib.PureWindowsPath(raw)
 if not permitted(raw,True):raise ValueError("Only approved local C/D game-resource paths")
 return pathlib.Path(p.drive[0].upper(),*p.parts[1:])
def io_path(p):
 raw=os.path.abspath(str(p))
 return pathlib.Path("\\\\?\\"+raw) if os.name=="nt" and not raw.startswith("\\\\?\\") else pathlib.Path(raw)
def signature(st):
 return [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns]
_parents=set()
_parent_lock=threading.Lock()
def ensure_parent(parent):
 key=str(parent).casefold()
 with _parent_lock:
  if key not in _parents:
   parent.mkdir(parents=True,exist_ok=True);_parents.add(key)
def copy_once(source,target):
 source=pathlib.Path(source);target=pathlib.Path(target)
 before=source.stat()
 if target.exists():raise FileExistsError("Existing destination preserved")
 ensure_parent(target.parent)
 temp=target.with_name("upload_"+uuid.uuid4().hex[:16]+".partial")
 h=hashlib.sha256();written=0
 try:
  with source.open("rb") as src,temp.open("xb") as dst:
   while True:
    block=src.read(4*1024*1024)
    if not block:break
    dst.write(block);h.update(block);written+=len(block)
  if signature(before)!=signature(source.stat()) or written!=before.st_size:
   raise RuntimeError("Source changed during transfer; original retained")
  os.rename(temp,target)
 except BaseException:
  if temp.exists():temp.unlink()
  raise
 return signature(before),h.hexdigest(),written
def make_plan(persistent,out):
 items={}
 def add(raw,all_files=False):
  if permitted(raw,all_files):
   p=str(pathlib.PureWindowsPath(raw));items.setdefault(p.casefold(),p)
 for name in ["plan/source-packages.jsonl","inventory/new-source-files.jsonl"]:
  p=out/name
  if not p.is_file():raise RuntimeError("Required prior inventory missing")
  for line in p.open(encoding="utf-8-sig"):
   try:
    row=json.loads(line);raw=row.get("source",row.get("path"))
    if raw:add(raw)
    for side in row.get("sidecars",[]):add(side["source"])
   except (ValueError,KeyError,TypeError):continue
 data=json.loads((out/"plan/bulk-import-summary.json").read_text(encoding="utf-8-sig"))
 for row in data.get("rawSources",[]):add(row["path"])
 roots=[r"D:\ANOMALIA\FabImports",r"C:\sketchfab",r"D:\ANOMALIA\sketchfab",r"D:\ANOMALIA\SketchfabExtracted",r"D:\ANOMALIA\StorageRecovery",r"D:\ANOMALIA\unreal\Content",r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\CitySample_5.8\data"]
 for root in roots:
  if not pathlib.Path(root).is_dir():continue
  for base,dirs,names in os.walk(root,followlinks=False):
   dirs[:]=[d for d in dirs if d.casefold() not in SKIP and not (getattr((pathlib.Path(base)/d).lstat(),"st_file_attributes",0)&0x400)]
   for name in names:add(str(pathlib.Path(base)/name),True)
 ordered=sorted(items.values(),key=lambda x:(0 if "citysample" in x.casefold() else 1,x.casefold()))
 tmp=persistent/"direct-source-plan.tmp"
 with tmp.open("w",encoding="utf-8") as f:
  for p in ordered:f.write(json.dumps({"path":p})+"\n")
 os.replace(tmp,persistent/"direct-source-plan.jsonl")
 return len(ordered)

def client_copy_benchmark(samples,dest):
 """Compare identical small-file payloads with one and four local copy workers."""
 selected=[(raw,size) for raw,size in samples if size<=1024**2][:24]
 if len(selected)<8:return {"workers":1,"reason":"Too few representative small files"}
 result={"sampleFiles":len(selected),"sampleBytes":sum(size for _,size in selected),"measuresDriveClientWritesNotRemoteUpload":True}
 for workers in [1,4]:
  root=dest/"_TransferBenchmark"/(os.environ.get("GITHUB_RUN_ID","local")+"_"+str(workers)+"_"+uuid.uuid4().hex[:8])
  started=time.monotonic()
  with ThreadPoolExecutor(max_workers=workers) as executor:
   futures=[executor.submit(copy_once,io_path(raw),io_path(root/(str(i)+pathlib.PureWindowsPath(raw).suffix))) for i,(raw,_) in enumerate(selected)]
   for future in futures:future.result()
  result["seconds"+str(workers)]=time.monotonic()-started
 result["workers"]=4 if result["seconds4"]<result["seconds1"]*0.9 else 1
 result["measuredClientSpeedRatio"]=result["seconds1"]/max(result["seconds4"],0.001)
 return result

def transfer_pending(items,db,journal,dest,previous,summary,deadline,save,workers,capacity):
 """Bound parallel writes by pending bytes and keep SQLite writes on the coordinator."""
 total=db.execute("SELECT COUNT(*),COALESCE(SUM(bytes),0) FROM copied").fetchone()
 summary["totalSourcePathsWritten"],summary["totalLogicalBytesWritten"]=total
 pending={};reserved=0;last_flush=time.monotonic();last_save=time.monotonic()
 def flush(force=False):
  nonlocal last_flush,last_save
  now=time.monotonic()
  if force or now-last_flush>=2:
   journal.flush();db.commit();last_flush=now
  if force or now-last_save>=15:
   save();last_save=now
 def receive(future):
  nonlocal reserved
  raw,size,plain_target=pending.pop(future);reserved-=size
  try:
   sig,digest,size=future.result();key=raw.casefold();old=previous.get(key)
   receipt={"source":raw,"cloudPath":str(plain_target),"bytes":size,"sha256":digest,"sourceSignature":sig,"state":"DIRECT_CLIENT_COPY_COMPLETE_SERVER_VERIFICATION_PENDING"}
   journal.write(json.dumps(receipt)+"\n")
   db.execute("INSERT OR REPLACE INTO copied VALUES(?,?,?,?,?)",(key,json.dumps(sig),str(plain_target),digest,size))
   summary["newFilesWrittenToDriveClient"]+=1;summary["newBytesWrittenToDriveClient"]+=size
   if old:summary["totalLogicalBytesWritten"]+=size-old[2]
   else:summary["totalSourcePathsWritten"]+=1;summary["totalLogicalBytesWritten"]+=size
   previous[key]=(sig,str(plain_target),size)
  except Exception as e:
   summary["copyErrorCount"]=summary.get("copyErrorCount",0)+1
   if len(summary["errors"])<100:summary["errors"].append({"path":raw,"error":str(e)})
  flush()
 exhausted=True
 try:
  with ThreadPoolExecutor(max_workers=workers) as executor:
   for raw,size in items:
    if time.monotonic()>deadline:exhausted=False;break
    while pending and (len(pending)>=workers*2 or min(capacity()[0]-reserved-size-768*1024**2,capacity()[1]-reserved-size-256*1024**2)<0):
     done,_=wait(pending,return_when=FIRST_COMPLETED)
     for future in done:receive(future)
    cfree,hfree=capacity()
    if cfree<832*1024**2 or hfree<320*1024**2:
     previous_state=summary.get("state","COPYING_CITY_SAMPLE_FIRST")
     summary["state"]="WAITING_FOR_DRIVE_CACHE_SPACE";flush(True)
     waited=time.monotonic()
     while time.monotonic()<deadline:
      cfree,hfree=capacity()
      summary["CFreeNow"]=cfree;summary["DriveClientFreeNow"]=hfree
      if cfree>=832*1024**2 and hfree>=320*1024**2:break
      time.sleep(min(5,max(0,deadline-time.monotonic())));flush()
     summary["cacheWaitSeconds"]=summary.get("cacheWaitSeconds",0)+(time.monotonic()-waited)
     summary["state"]=previous_state
     if time.monotonic()>=deadline:exhausted=False;break
    if cfree-reserved<size+768*1024**2 or hfree-reserved<size+256*1024**2:
     summary["deferred"]+=1;flush();continue
    relative=target_relative(raw);plain_target=dest/relative
    if io_path(plain_target).exists():plain_target=dest/"Versions"/(os.environ.get("GITHUB_RUN_ID","local")+"_"+uuid.uuid4().hex[:8])/relative
    future=executor.submit(copy_once,io_path(raw),io_path(plain_target))
    pending[future]=(raw,size,plain_target);reserved+=size
   while pending:
    done,_=wait(pending,return_when=FIRST_COMPLETED)
    for future in done:receive(future)
 finally:flush(True)
 return exhausted

def main():
 out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
 persistent=pathlib.Path(r"D:\ANOMALIA\unreal\Saved\CloudTransfer\Direct20261106");persistent.mkdir(parents=True,exist_ok=True)
 dest=pathlib.Path(r"H:\Mon Drive\ANOMALIAZ\02_Modeles_3D\Transfert_Direct_20261106")
 summary={"state":"PREPARING","batch":os.environ.get("GITHUB_RUN_ID"),"mode":"BOUNDED_PARALLEL_DIRECT_COPY_DUPLICATES_ACCEPTED","cloudFolderId":"1a9GemSBLXFkNlw4n_mhm8O4OC8SLhQra","originalFilesDeleted":0,"originalFilesModified":0,"remoteServerVerificationPending":True,"newFilesWrittenToDriveClient":0,"newBytesWrittenToDriveClient":0,"resumedUnchangedPaths":0,"missingSourcePaths":0,"deferred":0,"errors":[],"resumePolicy":"UNCHANGED_SOURCE_IDENTITY_AND_PREVIOUS_COMPLETED_CLIENT_RECEIPT","checkpointCommitIntervalSeconds":2}
 old_summary={}
 if (persistent/"summary.json").exists():
  old_summary=json.loads((persistent/"summary.json").read_text(encoding="utf-8"))
 def save():
  summary["reportedAtUTC"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
  (persistent/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
  (out/"direct-transfer-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
  try:
   if dest.is_dir():
    temp=dest/("progress_"+uuid.uuid4().hex[:12]+".tmp")
    temp.write_text(json.dumps(summary,indent=2),encoding="utf-8");os.replace(temp,dest/"direct-transfer-progress.json")
  except OSError:pass
 if old_summary.get("state")=="ALL_LOCAL_COPIES_WRITTEN_SERVER_VERIFICATION_PENDING":
  summary.update(old_summary);save();return
 save()
 for _ in range(12):
  if dest.is_dir():break
  time.sleep(5)
 if not dest.is_dir():raise RuntimeError("Verified cloud folder unavailable; originals retained")
 plan=persistent/"direct-source-plan.jsonl"
 if not plan.exists():make_plan(persistent,out)
 summary["plannedSourcePaths"]=sum(1 for _ in plan.open(encoding="utf-8"))
 db=sqlite3.connect(persistent/"written-paths.sqlite3")
 db.execute("CREATE TABLE IF NOT EXISTS copied(path TEXT PRIMARY KEY, signature TEXT, cloudPath TEXT, sha256 TEXT, bytes INTEGER)");db.commit()
 previous={row[0]:(json.loads(row[1]),row[2],row[3]) for row in db.execute("SELECT path,signature,cloudPath,bytes FROM copied")}
 total=db.execute("SELECT COUNT(*),COALESCE(SUM(bytes),0) FROM copied").fetchone()
 summary["totalSourcePathsWritten"],summary["totalLogicalBytesWritten"]=total
 deadline=time.monotonic()+285*60
 summary["state"]="COPYING_CITY_SAMPLE_FIRST";save()
 processed=0;last_progress=time.monotonic()
 def remaining():
  nonlocal processed,last_progress
  with plan.open(encoding="utf-8") as stream:
   for line in stream:
    if time.monotonic()>deadline:return
    raw=json.loads(line)["path"];processed+=1
    try:
     if not permitted(raw,True):raise ValueError("Invalid source plan scope")
     st=io_path(raw).stat()
     if not stat.S_ISREG(st.st_mode):continue
     if getattr(st,"st_file_attributes",0)&(0x1000|0x400000|0x400):summary["deferred"]+=1;continue
     prior=previous.get(raw.casefold())
     if prior and prior[0]==signature(st):
      summary["resumedUnchangedPaths"]+=1;continue
     yield raw,st.st_size
    except FileNotFoundError:summary["missingSourcePaths"]+=1
    except OSError as e:
     if len(summary["errors"])<100:summary["errors"].append({"path":raw,"error":str(e)})
    finally:
     summary["sourcePathsProcessedThisBatch"]=processed
     if time.monotonic()-last_progress>=15:save();last_progress=time.monotonic()
  summary["sourcePlanFullyEnumerated"]=True
 items=remaining();prefetch=list(itertools.islice(items,32))
 available=shutil.disk_usage("C:/").free
 try:
  summary["clientCopyBenchmark"]=client_copy_benchmark(prefetch,dest) if available>900*1024**2 else {"workers":1,"reason":"Cache reserve"}
 except Exception as e:summary["clientCopyBenchmark"]={"workers":1,"error":str(e)}
 workers=summary["clientCopyBenchmark"]["workers"];summary["parallelWorkers"]=workers;save()
 last_capacity=[0,None]
 def capacity():
  now=time.monotonic()
  if last_capacity[1] is None or now-last_capacity[0]>=0.25:
   last_capacity[:]=[now,(shutil.disk_usage("C:/").free,shutil.disk_usage("H:/").free)]
  return last_capacity[1]
 with (persistent/"direct-copy-receipts.jsonl").open("a",encoding="utf-8") as journal:
  exhausted=transfer_pending(itertools.chain(prefetch,items),db,journal,dest,previous,summary,deadline,save,workers,capacity)
 db.close()
 complete=exhausted and summary.get("sourcePlanFullyEnumerated") and not summary["deferred"] and not summary["errors"] and not summary["missingSourcePaths"]
 summary["state"]="ALL_LOCAL_COPIES_WRITTEN_SERVER_VERIFICATION_PENDING" if complete else "BATCH_TIME_LIMIT_AUTOMATIC_RESUME" if time.monotonic()>deadline else "PARTIAL_AUTOMATIC_RESUME_REQUIRED"
 save();print("DIRECT_TRANSFER_RESULT "+json.dumps(summary),flush=True)
if __name__=="__main__":main()
