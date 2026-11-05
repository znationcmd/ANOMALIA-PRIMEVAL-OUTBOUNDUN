"""Reconcile exact raw-resource duplicates; replace only managed recovery copies on the same volume."""
import os,pathlib,json,hashlib,collections,shutil,time,uuid
RAW={".zip",".7z",".rar",".fbx",".glb",".gltf",".obj",".blend",".abc",".usd",".usdz",".usdc",".usda",".png",".tga",".jpg",".jpeg",".dds",".wav",".ogg",".flac"}
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def share_verified_copy(source,target,managed_root):
 source=pathlib.Path(source);target=pathlib.Path(target);managed_root=pathlib.Path(managed_root).resolve()
 if not target.resolve().is_relative_to(managed_root):raise ValueError("Target is not an owned recovery copy")
 if target.is_symlink() or source.is_symlink():raise ValueError("Preserve symbolic links")
 a=source.stat();b=target.stat()
 if a.st_dev!=b.st_dev:raise ValueError("Cross-volume originals remain separate")
 if os.path.samefile(source,target):return 0
 expected=digest(source)
 if a.st_size!=b.st_size or expected!=digest(target):raise ValueError("Different contents preserved")
 # Keep both original pathnames; only this tool-owned duplicate allocation is replaced.
 temporary=target.with_name(target.name+".dedup-"+uuid.uuid4().hex)
 try:
  os.link(source,temporary)
  if digest(temporary)!=expected:raise RuntimeError("Link verification failed")
  current=target.stat();latest=source.stat()
  if (current.st_ino,current.st_size,current.st_mtime_ns)!=(b.st_ino,b.st_size,b.st_mtime_ns):raise RuntimeError("Target changed; preserved")
  if (latest.st_ino,latest.st_size,latest.st_mtime_ns)!=(a.st_ino,a.st_size,a.st_mtime_ns):raise RuntimeError("Source changed; preserved")
  os.replace(temporary,target)
  if not os.path.samefile(source,target) or digest(target)!=expected:raise RuntimeError("Post-replacement verification failed")
  return b.st_size if b.st_nlink==1 else 0
 finally:
  if temporary.exists():temporary.unlink() # Only a temporary link created above.
def main():
 out=pathlib.Path(os.environ["DUPLICATE_REPORT_OUT"]);out.mkdir(parents=True,exist_ok=True)
 managed=pathlib.Path(r"D:\ANOMALIA\sketchfab\Recovered_C")
 paths=set()
 plan=json.loads((out/"plan"/"bulk-import-summary.json").read_text(encoding="utf-8-sig"))
 for row in plan.get("rawSources",[]):paths.add(row["path"])
 inventory=out/"inventory"/"new-source-files.jsonl"
 with inventory.open(encoding="utf-8-sig") as stream:
  for line in stream:
   row=json.loads(line)
   if pathlib.Path(row["path"]).suffix.lower() in RAW:paths.add(row["path"])
 if managed.exists():
  for base,dirs,files in os.walk(managed,followlinks=False):
   dirs[:]=[d for d in dirs if not pathlib.Path(base,d).is_symlink()]
   for name in files:
    if pathlib.Path(name).suffix.lower() in RAW:paths.add(str(pathlib.Path(base,name)))
 report={"state":"IN_PROGRESS","filesConsidered":len(paths),"groups":[],"actions":[],"errors":[],"estimatedDuplicateBytesReleased":0,"existingOriginalPathsRemoved":0,"unrealAssetsModified":0,"sourcePayloadsCopied":0,"savesModified":0,"excludedExtensions":[".uasset",".umap",".uexp",".ubulk",".uptnl"],"diskFreeBefore":{}}
 for drive in ["C:/","D:/"]:
  if pathlib.Path(drive).exists():report["diskFreeBefore"][drive]=shutil.disk_usage(drive).free
 sizes=collections.defaultdict(list);hashcache={};started=time.monotonic()
 for name in paths:
  p=pathlib.Path(name)
  try:
   if p.suffix.lower() not in RAW or not p.is_file():continue
   s=p.stat()
   if getattr(s,"st_file_attributes",0)&(0x1000|0x400000):continue
   sizes[s.st_size].append(p)
  except OSError as e:report["errors"].append({"path":str(p),"error":str(e)})
 for size,items in sizes.items():
  if len(items)<2:continue
  groups=collections.defaultdict(list)
  for p in items:
   try:
    s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if key not in hashcache:hashcache[key]=digest(p)
    groups[hashcache[key]].append(p)
   except OSError as e:report["errors"].append({"path":str(p),"error":str(e)})
  for sha,peers in groups.items():
   if len(peers)<2:continue
   identities={(p.stat().st_dev,p.stat().st_ino) for p in peers}
   group={"sha256":sha,"bytesPerFile":size,"paths":[str(p) for p in peers],"physicalCopies":len(identities),"alreadyLinked":len(identities)==1}
   report["groups"].append(group)
   originals=[p for p in peers if not p.resolve().is_relative_to(managed.resolve())]
   for target in peers:
    if not target.resolve().is_relative_to(managed.resolve()):continue
    source=next((p for p in originals if p.stat().st_dev==target.stat().st_dev),None)
    if source is None:
     report["actions"].append({"target":str(target),"state":"CROSS_VOLUME_OR_UNOWNED_COPY_PRESERVED_USE_ORIGINAL_SOURCE"});continue
    try:
     if os.path.samefile(source,target):continue
     freed=share_verified_copy(source,target,managed)
     report["estimatedDuplicateBytesReleased"]+=freed
     report["actions"].append({"source":str(source),"target":str(target),"state":"VERIFIED_MANAGED_COPY_SHARED_SAME_VOLUME","estimatedReleasedBytes":freed})
    except Exception as e:report["errors"].append({"target":str(target),"error":str(e)})
  if time.monotonic()-started>1500:
   report["state"]="PARTIAL_TIME_LIMIT_RETAINED";break
  (out/"duplicate-reconciliation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 report["state"]="COMPLETE_FOR_REUSED_INVENTORIES" if report["state"]=="IN_PROGRESS" else report["state"]
 report["diskFreeAfter"]={drive:shutil.disk_usage(drive).free for drive in report["diskFreeBefore"]}
 (out/"duplicate-reconciliation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps({k:v for k,v in report.items() if k not in {"groups","actions","errors"}}),flush=True)
 print("GROUPS",len(report["groups"]),"ACTIONS",len(report["actions"]),"ERRORS",len(report["errors"]),flush=True)
if __name__=="__main__":main()
