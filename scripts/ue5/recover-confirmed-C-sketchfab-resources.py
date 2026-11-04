import pathlib,hashlib,json,shutil,os,zipfile
main=pathlib.Path(r"D:\ANOMALIA"); out=pathlib.Path(os.environ["RECOVERY_REPORT"]);out.mkdir(parents=True,exist_ok=True)
target=main/"sketchfab"/"Recovered_C";target.mkdir(parents=True,exist_ok=True)
priority=[pathlib.Path(r"C:\Users\utilisateur\Downloads\karting-club-lider-outdoor-race-track-ready.zip"),pathlib.Path(r"C:\Users\utilisateur\Downloads\sand-mountain-motocross.zip")]
source_root=pathlib.Path(r"C:\sketchfab")
sources=priority+([p for p in source_root.rglob("*") if p.is_file()] if source_root.exists() else [])
report={"originalsModified":0,"files":[]}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
for p in sources:
 try:
  rel=pathlib.Path("Downloads")/p.name if p in priority else pathlib.Path("Sketchfab")/p.relative_to(source_root)
  d=target/rel;before=p.stat();expected=sha(p)
  item={"source":str(p),"target":str(d),"bytes":before.st_size,"sha256":expected}
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
