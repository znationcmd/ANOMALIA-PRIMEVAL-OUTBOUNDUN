"""Extract all inventoried game-resource archives, preserving originals and native Content layouts."""
import os,pathlib,json,hashlib,zipfile,stat,shutil,time,re,subprocess,collections,zlib,uuid
MODELS={".fbx",".glb",".gltf",".obj"}
OTHER_MODELS={".blend",".abc",".usd",".usdz",".usda",".usdc",".dae",".stl",".3ds",".bvh",".max",".ma",".mb",".c4d"}
NATIVE={".uasset",".umap"}
ARCHIVES={".zip",".7z",".rar"}
GENERATED={".git","node_modules","intermediate","deriveddatacache","__macosx",".tmp.driveupload"}
EXECUTABLE={".exe",".dll",".msi",".com",".scr",".ddp",".pdb",".pak",".ucas",".utoc"}
CATEGORIES={
"bank_cards":r"bank.?card|credit.?card|debit.?card|carte.?banc|carte.?bleue",
"keys":r"(?:^|[/_ -])(?:key|keys|keycard|cle|clé)(?:[/_. -]|$)|padlock|container.?key",
"handcuffs":r"handcuff|menott|restraint",
"clothing":r"clothing|clothes|shirt|pants|jacket|boots?|shoes?|helmet|backpack|vêtements?|gilet|veste|pantalon",
"food":r"food|drink|bread|milk|apple|meat|canned|soup|nourrit|aliment|water.?bottle",
"vehicles":r"vehicle|bmw|truck|motorcycle|snowmobile|scooter|helicopter|aircraft|hovercraft|boat|tank|train|scania",
"maps_tracks":r"landscape|terrain|circuit|motocross|citysample|metro|drift|racetrack",
"animations":r"animation|motion|locomotion|sprint"
}
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024**2),b""):h.update(b)
 return h.hexdigest()
def safe_path(name):
 if any(ord(c)<32 for c in name):raise ValueError("Control character in archive path")
 p=pathlib.PurePosixPath(name.replace("\\","/"))
 if p.is_absolute() or ".." in p.parts or any(":" in s or s.endswith((" ",".")) for s in p.parts):raise ValueError("Archive path escapes owned extraction")
 for part in p.parts:
  if part.split(".")[0].upper() in {"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}:raise ValueError("Reserved Windows path")
 return p
def wanted(p):
 return not GENERATED.intersection(x.lower() for x in p.parts) and p.suffix.lower() not in EXECUTABLE
def categories(names):
 return [key for key,pattern in CATEGORIES.items() if any(re.search(pattern,n,re.I) for n in names)]
def zip_members(path):
 rows=[];blocked=[]
 with zipfile.ZipFile(path) as z:
  for member in z.infolist():
   try:
    pure=safe_path(member.filename)
    if stat.S_IFMT(member.external_attr>>16)==stat.S_IFLNK:raise ValueError("Archive symlink retained only in original archive")
    if member.flag_bits&1:raise ValueError("Encrypted archive member")
    if not member.is_dir() and wanted(pure):rows.append({"path":str(pure),"size":member.file_size,"crc":member.CRC,"zipName":member.filename})
   except ValueError as exc:blocked.append({"member":member.filename,"reason":str(exc)})
 return rows,blocked
def seven_members(path,tool):
 result=subprocess.run([str(tool),"l","-slt","-ba","-sccUTF-8","-p-","--",str(path)],stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=180)
 if result.returncode:raise RuntimeError("7-Zip listing failed: "+result.stderr[-1200:])
 rows=[]
 for block in re.split(r"\r?\n\r?\n",result.stdout):
  row=dict(line.split(" = ",1) for line in block.splitlines() if " = " in line)
  if "Path" not in row or "Type" in row:continue
  pure=safe_path(row["Path"])
  if any(row.get(k) for k in ["Symbolic Link","Hard Link"]) or "reparse" in row.get("Attributes","").lower():raise ValueError("Linked archive entries require separate review")
  if row.get("Encrypted")=="+" :raise ValueError("Encrypted archive requires its owner password")
  directory=row.get("Folder")=="+" or row.get("Attributes","").startswith("D")
  if not directory and wanted(pure):rows.append({"path":str(pure),"size":int(row.get("Size","0"))})
 return rows,[]
def extract_zip(path,folder,rows):
 with zipfile.ZipFile(path) as z:
  for row in rows:
   target=folder.joinpath(*pathlib.PurePosixPath(row["path"]).parts)
   if not target.parent.resolve().is_relative_to(folder.resolve()):raise ValueError("Extraction parent escapes owner")
   target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():
    if getattr(target.lstat(),"st_file_attributes",0)&0x400 or not target.is_file() or target.stat().st_size!=row["size"]:raise ValueError("Different existing extraction preserved")
    crc=0
    with target.open("rb") as f:
     for b in iter(lambda:f.read(4*1024**2),b""):crc=zlib.crc32(b,crc)
    if crc&0xffffffff!=row["crc"]:raise ValueError("Existing extraction CRC differs; no overwrite")
   else:
    with z.open(row["zipName"]) as src,target.open("xb") as dst:shutil.copyfileobj(src,dst,4*1024**2)
def main():
 project=pathlib.Path(r"D:\ANOMALIA\unreal");assert (project/"AnomaliaPrimeval.uproject").is_file()
 state=project/"Saved/ImportReceipts/AllResources20261107";state.mkdir(parents=True,exist_ok=True)
 raw_state=project/"Saved/ImportReceipts/RawResume20261107"
 raw_path=raw_state/"raw-preparation-manifest.json"
 raw=json.loads(raw_path.read_text(encoding="utf-8"))
 seen_models={r["sha256"] for r in raw["imports"]}
 ledger=state/"archive-receipts.jsonl";known={}
 if ledger.exists():
  for line in ledger.open(encoding="utf-8"):
   r=json.loads(line)
   if r.get("state")=="VERIFIED_EXTRACTED":known[r["archiveSHA256"]]=r
 tool=pathlib.Path(os.environ["ANOMALIA_7ZIP"]) if os.environ.get("ANOMALIA_7ZIP") else None
 out=pathlib.Path(os.environ["MISSION_ALL_OUT"]);out.mkdir(parents=True,exist_ok=True)
 plan=project/"Saved/CloudTransfer/Direct20261106/direct-source-plan.jsonl"
 candidates={}
 for line in plan.open(encoding="utf-8"):
  p=pathlib.Path(json.loads(line)["path"])
  if p.suffix.lower() in ARCHIVES and not GENERATED.intersection(x.lower() for x in p.parts):candidates.setdefault(str(p).casefold(),p)
 # Reuse prior inventories and references; no global personal-disk rescan.
 for catalog in (project/"SourceAssets/ExternalResources").glob("original-source-catalog-*.json"):
  data=json.loads(catalog.read_text(encoding="utf-8-sig"))
  for row in data.get("files",[]):
   p=pathlib.Path(row.get("importSource",""))
   if p.suffix.lower() in ARCHIVES:candidates.setdefault(str(p).casefold(),p)
 queue=collections.deque((p,0) for p in sorted(candidates.values(),key=lambda p:str(p).casefold()))
 summary={"state":"EXTRACTING","inventoriedArchives":len(queue),"archivesNewlyExtracted":0,"archivesReused":0,"newRawModels":0,"nativePackagesPrepared":0,"nativeContentRoots":[],"nativeMountReview":[],"categories":{},"blocked":[],"originalFilesDeleted":0,"existingAssetsOverwritten":0}
 native_roots=set();processed=set();started=time.monotonic()
 def save():
  summary["elapsedSeconds"]=time.monotonic()-started
  summary["freeBytes"]={d:shutil.disk_usage(d+":/").free for d in ["C","D"]}
  summary["nativeContentRoots"]=sorted(native_roots)
  (out/"all-asset-extraction-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
  (state/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
  tmp=raw_path.with_suffix(".all-resources.tmp");tmp.write_text(json.dumps(raw,indent=2),encoding="utf-8");os.replace(tmp,raw_path)
  print("ALL_RESOURCE_EXTRACTION "+json.dumps({k:v for k,v in summary.items() if k not in {"blocked","nativeContentRoots"}}),flush=True)
 while queue:
  if time.monotonic()-started>150*60:summary["timeBudgetReached"]=True;break
  path,depth=queue.popleft()
  try:
   if not path.is_file():
    ref=path.with_name(path.name+".duplicate.json")
    if ref.exists():
     data=json.loads(ref.read_text(encoding="utf-8"));path=pathlib.Path(data["retainedOriginalPath"])
     if digest(path)!=data["sha256"]:raise ValueError("Retained duplicate archive differs")
    else:raise FileNotFoundError("Inventoried archive not local; reference retained")
   before=path.stat()
   if getattr(before,"st_file_attributes",0)&(0x1000|0x400000):raise ValueError("Archive is not resident locally")
   archive_hash=digest(path)
   if archive_hash in processed:continue
   processed.add(archive_hash)
   if archive_hash in known and pathlib.Path(known[archive_hash]["folder"]).is_dir():
    folder=pathlib.Path(known[archive_hash]["folder"]);rows=known[archive_hash]["files"];summary["archivesReused"]+=1
   else:
    rows,blocked=zip_members(path) if path.suffix.lower()==".zip" else seven_members(path,tool) if tool and tool.is_file() else (_ for _ in ()).throw(RuntimeError("RAR/7z decoder unavailable; ZIP extraction continues"))
    summary["blocked"].extend({"archive":str(path),**r} for r in blocked)
    if not any(pathlib.PurePosixPath(r["path"]).suffix.lower() in MODELS|OTHER_MODELS|NATIVE|ARCHIVES for r in rows):continue
    if len({r["path"].casefold() for r in rows})!=len(rows):raise ValueError("Archive contains conflicting Windows paths; original preserved")
    required=sum(r["size"] for r in rows)
    # Reuse complete prior extractions instead of creating a second physical copy.
    old_folder=pathlib.Path(r"C:\AZRI\41851208057\inputs")/archive_hash[:20]
    if path.suffix.lower()==".zip" and old_folder.is_dir():
     missing=sum(r["size"] for r in rows if not old_folder.joinpath(*pathlib.PurePosixPath(r["path"]).parts).is_file())
     if missing and shutil.disk_usage(old_folder).free<missing+8*1024**3:raise RuntimeError("Prior extraction needs missing dependencies but C reserve must be retained")
     folder=old_folder;extract_zip(path,folder,rows);summary["archivesReused"]+=1
    else:
     root=project/"SourceAssets/AllExtracted";root.mkdir(parents=True,exist_ok=True)
     if shutil.disk_usage(root).free<required+12*1024**3:raise RuntimeError("Insufficient space to extract this archive while retaining 12 GiB D reserve; requiredBytes="+str(required))
     folder=root/archive_hash[:20]
     if folder.exists() and getattr(folder.lstat(),"st_file_attributes",0)&0x400:raise RuntimeError("Existing extraction directory reparse point preserved")
     if path.suffix.lower()==".zip":
      folder.mkdir(exist_ok=True);extract_zip(path,folder,rows)
     else:
      temporary=root/(archive_hash+".partial-"+uuid.uuid4().hex[:12]);temporary.mkdir()
      include=state/("members-"+uuid.uuid4().hex+".txt")
      include.write_text("\n".join(r["path"] for r in rows),encoding="utf-8")
      command=[str(tool),"x","-y","-aos","-spd","-sccUTF-8","-scsUTF-8","-p-","-i@"+str(include),"-o"+str(temporary),"--",str(path)]
      result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=3600)
      if result.returncode:raise RuntimeError("7-Zip extraction failed; partial output retained for diagnosis: "+result.stdout[-1500:].decode(errors="replace"))
      for row in rows:
       p=temporary.joinpath(*pathlib.PurePosixPath(row["path"]).parts)
       if not p.is_file() or p.stat().st_size!=row["size"] or getattr(p.lstat(),"st_file_attributes",0)&0x400:raise RuntimeError("External extraction verification failed")
      if folder.exists():raise RuntimeError("Existing canonical extraction preserved; new output retained separately")
      os.rename(temporary,folder)
     summary["archivesNewlyExtracted"]+=1
    after=path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns) or digest(path)!=archive_hash:raise RuntimeError("Archive changed during extraction")
    receipt={"state":"VERIFIED_EXTRACTED","source":str(path),"archiveSHA256":archive_hash,"folder":str(folder),"files":rows,"categories":categories([r["path"] for r in rows])}
    with ledger.open("a",encoding="utf-8") as f:f.write(json.dumps(receipt)+"\n");f.flush();os.fsync(f.fileno())
    known[archive_hash]=receipt
   for category in categories([r["path"] for r in rows]):summary["categories"][category]=summary["categories"].get(category,0)+1
   for row in rows:
    p=folder.joinpath(*pathlib.PurePosixPath(row["path"]).parts)
    if p.suffix.lower() in ARCHIVES:
     if depth<3:queue.append((p,depth+1))
     else:summary["blocked"].append({"archive":str(p),"reason":"Nested archive depth exceeds the bounded pass; original retained"})
    if p.suffix.lower() in MODELS:
     sha=digest(p)
     if sha not in seen_models:
      seen_models.add(sha)
      raw["imports"].append({"source":str(p),"prepared":str(p),"sha256":sha,"preparedSHA256":sha,"family":hashlib.sha256(archive_hash.encode()).hexdigest(),"animationOnly":bool(re.search(r"[/\\](?:animations?|motions?)[/\\]|[/\\]RM_|[/\\]IP_",str(p),re.I))})
      summary["newRawModels"]+=1
    if p.suffix.lower() in NATIVE:
     summary["nativePackagesPrepared"]+=1
     parts=pathlib.PurePosixPath(row["path"]).parts
     content_index=next((i for i,v in enumerate(parts) if v.casefold()=="content"),None)
     if content_index is not None and not any(v.casefold()=="plugins" for v in parts[:content_index]):
      native_roots.add(str(folder.joinpath(*parts[:content_index+1])))
     else:
      mount={"package":str(p),"reason":"Plugin mount or original Content root must be resolved before installation"}
      if len(summary["nativeMountReview"])<200:summary["nativeMountReview"].append(mount)
   save()
  except Exception as exc:summary["blocked"].append({"archive":str(path),"reason":str(exc)});save()
 summary["remainingQueuedArchives"]=len(queue)
 summary["state"]="EXTRACTION_FINISHED_WITH_EXPLICIT_BLOCKERS" if summary["blocked"] or queue else "ALL_INVENTORIED_SUPPORTED_ARCHIVES_EXTRACTED"
 raw["imports"].sort(key=lambda r:(r.get("animationOnly",False),r["source"].casefold()));save()
 if native_roots:
  integration=out/"native-input";integration.mkdir(exist_ok=True)
  source_projects=[];manifest=integration/"source-packages.jsonl"
  with manifest.open("w",encoding="utf-8") as f:
   for root in sorted(native_roots):
    base=pathlib.Path(root);identity=hashlib.sha256(str(base).casefold().encode()).hexdigest()[:16]
    source_projects.append({"id":identity,"content":str(base),"projects":[]})
    for current,dirs,names in os.walk(base):
     dirs[:]=[d for d in dirs if d.lower() not in GENERATED]
     for name in names:
      p=pathlib.Path(current)/name
      if p.suffix.lower() not in NATIVE:continue
      s=p.stat();sidecars=[]
      for ext in [".uexp",".ubulk",".uptnl"]:
       side=p.with_suffix(ext)
       if side.is_file():sidecars.append({"source":str(side),"extension":ext,"bytes":side.stat().st_size})
      f.write(json.dumps({"sourceId":identity,"source":str(p),"relative":p.relative_to(base).as_posix(),"bytes":s.st_size,"mtimeNS":s.st_mtime_ns,"sidecars":sidecars})+"\n")
  native_plan={"state":"LOCAL_SOURCE_RECONCILIATION_PLAN_COMPLETE","sourceManifestSHA256":digest(manifest),"sourceProjects":source_projects}
  (integration/"bulk-import-summary.json").write_text(json.dumps(native_plan,indent=2),encoding="utf-8")
 print("ALL_RESOURCE_EXTRACTION_RESULT "+json.dumps(summary),flush=True)
if __name__=="__main__":main()
