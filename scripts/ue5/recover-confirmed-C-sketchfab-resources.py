import pathlib,hashlib,json,shutil,os,zipfile
main=pathlib.Path(r"D:\ANOMALIA"); out=pathlib.Path(os.environ["RECOVERY_REPORT"]);out.mkdir(parents=True,exist_ok=True)
target=main/"sketchfab"/"Recovered_C";target.mkdir(parents=True,exist_ok=True)
priority=[pathlib.Path(r"C:\Users\utilisateur\Downloads\karting-club-lider-outdoor-race-track-ready.zip"),pathlib.Path(r"C:\Users\utilisateur\Downloads\sand-mountain-motocross.zip")]
source_root=pathlib.Path(r"C:\sketchfab")
def local_files(root):
 if not root.exists():return
 for base,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if not d.startswith(".") and not pathlib.Path(base,d).is_symlink()]
  for name in files:
   p=pathlib.Path(base,name)
   if not name.startswith(".") and p.is_file():yield p
downloads=pathlib.Path(r"C:\Users\utilisateur\Downloads")
cmd_roots=[p for p in downloads.iterdir() if p.is_dir() and p.name.casefold().startswith("cmd")] if downloads.exists() else []
sources=priority+list(local_files(source_root))+[f for root in cmd_roots for f in local_files(root)]
report={"originalsModified":0,"filesExecuted":0,"hiddenUploadCachesExcluded":True,"unrealImportValidated":False,"files":[]}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
for p in sources:
 try:
  rel=pathlib.Path("Downloads")/p.name if p in priority else (pathlib.Path("Sketchfab")/p.relative_to(source_root) if p.is_relative_to(source_root) else pathlib.Path("CMD_Additions")/p.relative_to(downloads))
  d=target/rel;before=p.stat()
  if not d.exists() and shutil.disk_usage(target).free<4*1024**3+before.st_size:
   item={"source":str(p),"target":str(d),"bytes":before.st_size,"state":"DEFERRED_DISK_RESERVE"}
   report["files"].append(item)
   print(json.dumps(item),flush=True)
   continue
  expected=sha(p)
  item={"source":str(p),"target":str(d),"bytes":before.st_size,"sha256":expected,"unrealImportValidated":False}
  if d.exists():
   item["state"]="ALREADY_IDENTICAL" if d.is_file() and sha(d)==expected else "EXISTING_CONFLICT_PRESERVED"
  elif shutil.disk_usage(target).free<4*1024**3+before.st_size:item["state"]="DEFERRED_DISK_RESERVE"
  else:
   d.parent.mkdir(parents=True,exist_ok=True)
   with p.open("rb") as src,d.open("xb") as dst:shutil.copyfileobj(src,dst,1024*1024)
   assert sha(d)==expected and sha(p)==expected
   item["state"]="COPIED_AND_HASH_VERIFIED"
  if p in priority and zipfile.is_zipfile(p):
   with zipfile.ZipFile(p) as z:
    item["modelMembers"]=[i.filename for i in z.infolist() if pathlib.Path(i.filename).suffix.lower() in {".fbx",".glb",".gltf",".obj",".blend",".uproject"}]
    item["licenseMembers"]=[i.filename for i in z.infolist() if any(t in i.filename.lower() for t in ["license","licence","readme","credit"])]
  report["files"].append(item);print(json.dumps(item),flush=True)
 except Exception as e:report["files"].append({"source":str(p),"state":"ERROR_PRESERVED","error":str(e)})
 (out/"C-resource-recovery.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"files":len(report["files"]),"copied":sum(x["state"]=="COPIED_AND_HASH_VERIFIED" for x in report["files"]),"deferred":sum(x["state"]=="DEFERRED_DISK_RESERVE" for x in report["files"])}),flush=True)
