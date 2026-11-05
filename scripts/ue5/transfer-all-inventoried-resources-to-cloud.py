"""Back up all inventoried game resources to the verified Google Drive desktop mount."""
import os,pathlib,json,hashlib,collections,time,shutil,uuid
MAIN=pathlib.Path(r"D:\ANOMALIA\unreal")
CLOUD=pathlib.Path(r"H:\Mon Drive\ANOMALIAZ\02_Modeles_3D")
DEST=CLOUD/"Ressources_Completes_20261105"
EXT={".uasset",".umap",".uexp",".ubulk",".uptnl",".fbx",".glb",".gltf",".obj",".blend",".abc",".usd",".usdz",".usda",".usdc",".3ds",".stl",".dae",".zip",".7z",".rar",".png",".jpg",".jpeg",".tga",".bmp",".tif",".tiff",".dds",".exr",".hdr",".psd",".wav",".ogg",".flac",".mp3",".bin",".mtl",".uproject",".uplugin"}
out=pathlib.Path(os.environ["CLOUD_TRANSFER_OUT"]);out.mkdir(parents=True,exist_ok=True)
persistent=MAIN/"Saved/CloudTransfer/20261105";persistent.mkdir(parents=True,exist_ok=True)
journal_path=persistent/"resource-transfers.jsonl"
deadline=time.monotonic()+285*60
summary={"state":"PREPARING","destination":str(DEST),"cloudFolderId":"1DM8M8wWZcuOMOef4Dpshb9PakHwx2scw","localFilesDeleted":0,"sourceFilesModified":0,"newBytesWrittenToDriveClient":0,"newFilesWrittenToDriveClient":0,"sourcePathsRecorded":0,"remoteServerVerificationPending":True,"errors":[],"sourceInventories":[41842801517,41974129695],"unrealGameplayAcceptance":False}
def save():
 (out/"cloud-transfer-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
 (persistent/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for b in iter(lambda:stream.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def reserve(size):
 return shutil.disk_usage("C:/").free>=size+1024**3 and shutil.disk_usage("H:/").free>=size+256*1024**2
for _ in range(12):
 if DEST.is_dir():break
 time.sleep(10)
if not DEST.is_dir():raise RuntimeError("Connector-created cloud folder not visible on verified H mount; no transfer started")
sources={}
def add(name,provenance):
 try:
  p=pathlib.Path(name)
  if not p.is_file() or p.suffix.lower() not in EXT:return
  resolved=p.resolve()
  if resolved.drive.casefold() not in {"c:","d:"}:return
  st=p.stat()
  if getattr(st,"st_file_attributes",0)&(0x1000|0x400000):return
  sources.setdefault(str(resolved).casefold(),{"path":str(resolved),"bytes":st.st_size,"provenance":provenance})
 except OSError as e:
  if len(summary["errors"])<200:summary["errors"].append({"path":str(name),"error":str(e)})
plan=json.loads((out/"plan/bulk-import-summary.json").read_text(encoding="utf-8-sig"))
# Prior manifests are reused, not replaced by another full-disk audit.
for row in plan.get("rawSources",[]):add(row["path"],"prior-raw-sources")
for line in (out/"plan/source-packages.jsonl").open(encoding="utf-8-sig"):
 row=json.loads(line);add(row["source"],"prior-native-packages")
 for side in row.get("sidecars",[]):add(side["source"],"native-sidecar")
for line in (out/"inventory/new-source-files.jsonl").open(encoding="utf-8-sig"):
 row=json.loads(line);p=pathlib.Path(row["path"])
 if p.suffix.lower() in EXT:
  if p.suffix.lower() in {".zip",".7z",".rar"} and not any(k in str(p).lower() for k in ["sketchfab","fabimports","fablibrary","anomalia","unreal"]):continue
  add(str(p),"supplemental-C-D-inventory")
# Include newly imported assets absent from earlier inventories.
for base,dirs,names in os.walk(MAIN/"Content",followlinks=False):
 dirs[:]=[d for d in dirs if not d.startswith(".")]
 for name in names:add(str(pathlib.Path(base,name)),"current-actual-main-content")
for catalog in (MAIN/"SourceAssets/ExternalResources").glob("original-source-catalog-*.json"):
 data=json.loads(catalog.read_text(encoding="utf-8-sig"))
 for row in data.get("files",[]):
  if row.get("importSource"):add(row["importSource"],"verified-original-source-catalog")
summary["sourceFilesPlanned"]=len(sources);summary["logicalSourceBytesBeforeContentDedup"]=sum(x["bytes"] for x in sources.values())
summary["state"]="TRANSFERRING";save()
print(json.dumps({k:v for k,v in summary.items() if k!="errors"}),flush=True)
# Compare likely matching preexisting cloud files before allocating another cloud copy.
existing=collections.defaultdict(list)
for base,dirs,names in os.walk(CLOUD,followlinks=False):
 dirs[:]=[d for d in dirs if d!="Ressources_Completes_20261105"]
 for name in names:
  p=pathlib.Path(base,name)
  if p.suffix.lower() not in EXT:continue
  try:existing[(name.casefold(),p.stat().st_size)].append(p)
  except OSError:pass
 if time.monotonic()>deadline:break
objects={};hashes={};counts=collections.Counter()
if journal_path.exists():
 for line in journal_path.open(encoding="utf-8"):
  try:
   item=json.loads(line)
   p=pathlib.Path(item["cloudPath"])
   if p.is_file() and p.stat().st_size==item["bytes"]:objects[item["sha256"]]=p
  except (OSError,ValueError,KeyError):pass
priority=lambda row:(0 if any(w in row["path"].lower() for w in ["sand-mountain","karting-club","shanghai-international"]) else 1 if pathlib.Path(row["path"]).suffix.lower() in {".zip",".fbx",".glb",".gltf",".obj"} else 2,row["bytes"])
try:
 with journal_path.open("a",encoding="utf-8") as journal:
  for row in sorted(sources.values(),key=priority):
   if time.monotonic()>deadline:
    summary["state"]="PARTIAL_TIME_WINDOW_REQUIRES_RESUME";break
   p=pathlib.Path(row["path"])
   try:
    before=p.stat();identity=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
    if identity not in hashes:hashes[identity]=sha(p)
    digest=hashes[identity]
    cloud=objects.get(digest);state="CONTENT_ALREADY_REFERENCED"
    if cloud is None:
     for candidate in existing.get((p.name.casefold(),before.st_size),[])[:20]:
      if not reserve(before.st_size):break
      if sha(candidate)==digest:
       cloud=candidate;state="EXISTING_DRIVE_FILE_HASH_VERIFIED";break
    if cloud is None:
     if not reserve(before.st_size):
      counts["DEFERRED_LOCAL_CACHE_OR_CLOUD_RESERVE"]+=1
      continue
     name=replaced_name=p.name
     if len(name)>100:name=p.stem[:60]+"_"+digest[:12]+p.suffix
     cloud=DEST/"Objects"/digest[:2]/digest/name
     cloud.parent.mkdir(parents=True,exist_ok=True)
     if cloud.exists():
      if cloud.stat().st_size!=before.st_size or sha(cloud)!=digest:raise RuntimeError("Existing cloud object differs; preserve it")
      state="EXISTING_OBJECT_HASH_VERIFIED"
     else:
      temporary=cloud.with_name(cloud.name+".upload-"+uuid.uuid4().hex)
      with p.open("rb") as src,temporary.open("xb") as dst:shutil.copyfileobj(src,dst,4*1024*1024)
      if sha(temporary)!=digest:raise RuntimeError("Drive-client readback checksum mismatch; local original retained")
      after=p.stat()
      if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError("Source changed during upload; original retained")
      os.rename(temporary,cloud) # Windows refuses to overwrite an existing cloud file.
      state="DRIVE_CLIENT_WRITTEN_HASH_VERIFIED_REMOTE_CONFIRMATION_PENDING"
      summary["newBytesWrittenToDriveClient"]+=before.st_size;summary["newFilesWrittenToDriveClient"]+=1
      print("CLOUD_WRITTEN "+json.dumps({"source":str(p),"cloud":str(cloud),"bytes":before.st_size,"sha256":digest}),flush=True)
    objects[digest]=cloud
    record={**row,"sha256":digest,"bytes":before.st_size,"cloudPath":str(cloud),"state":state}
    journal.write(json.dumps(record,separators=(",",":"))+"\n");journal.flush()
    counts[state]+=1;summary["sourcePathsRecorded"]+=1
   except Exception as e:
    counts["ERROR_ORIGINAL_RETAINED"]+=1
    if len(summary["errors"])<200:summary["errors"].append({"path":str(p),"error":str(e)})
   if sum(counts.values())%100==0:
    summary["counts"]=dict(counts);save()
    print("CLOUD_PROGRESS "+json.dumps({"processed":sum(counts.values()),"counts":dict(counts),"bytesWritten":summary["newBytesWrittenToDriveClient"]}),flush=True)
 if summary["state"]=="TRANSFERRING":
  summary["state"]="BATCH_WRITTEN_REMOTE_CONFIRMATION_PENDING" if not counts["DEFERRED_LOCAL_CACHE_OR_CLOUD_RESERVE"] and not counts["ERROR_ORIGINAL_RETAINED"] else "PARTIAL_REQUIRES_CACHE_SPACE_OR_ERROR_CORRECTION"
finally:
 summary["counts"]=dict(counts);summary["uniqueContentObjectsReferenced"]=len(objects);save()
 shutil.copyfile(journal_path,out/"resource-transfers.jsonl")
 # The restore manifest retains every original path while identical payloads are stored once.
 if reserve(journal_path.stat().st_size):
  remote_manifest=DEST/("resource-manifest-"+os.environ["GITHUB_RUN_ID"]+".jsonl")
  if not remote_manifest.exists():
   with journal_path.open("rb") as src,remote_manifest.open("xb") as dst:shutil.copyfileobj(src,dst)
 print("CLOUD_RESULT "+json.dumps(summary),flush=True)
