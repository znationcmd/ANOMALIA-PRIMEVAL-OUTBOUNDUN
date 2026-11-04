"""Plan reconciliation of existing local Unreal content and raw Fab/Sketchfab sources."""
import os,pathlib,json,hashlib,zipfile,collections,time
main=pathlib.Path(r"D:\ANOMALIA\unreal")
out=pathlib.Path(os.environ["MISSION_BULK_OUT"]);out.mkdir(parents=True,exist_ok=True)
assert (main/"AnomaliaPrimeval.uproject").is_file(),"Actual existing D project is required"
started=time.monotonic()
def identity(path):
    return str(path.resolve()).casefold()
def identifier(path):
    return hashlib.sha256(identity(path).encode("utf-8")).hexdigest()[:16]
def descriptor(path):
    raw=path.read_bytes()
    text=raw.decode("utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")
    value=json.loads(text)
    return {"path":str(path),"name":path.stem,"engineAssociation":value.get("EngineAssociation"),"modules":value.get("Modules",[]),"plugins":[p.get("Name") for p in value.get("Plugins",[]) if p.get("Enabled")]}
excluded={"content","plugins","source","intermediate","saved","deriveddatacache","binaries","build",".vs",".git","node_modules","windows","program files","program files (x86)","programdata","$recycle.bin","system volume information"}
roots=[pathlib.Path(r"D:\ANOMALIA\FabImports"),pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555"),pathlib.Path(os.environ["USERPROFILE"])/"Documents/Unreal Projects",pathlib.Path(os.environ["USERPROFILE"])/"OneDrive/Documents/Unreal Projects"]
for drive in ["C:/","D:/"]:
    base=pathlib.Path(drive)
    if not base.is_dir():continue
    for child in base.iterdir():
        name=child.name.casefold()
        if child.is_dir() and name not in excluded and ("anomalia" in name or "unreal" in name or "project" in name) and not any(t in name for t in ["mission","validation","archive","backup"]):
            roots.append(child)
queue=collections.deque((p,0) for p in roots if p.is_dir());visited=set();content={};errors=[]
while queue:
    folder,depth=queue.popleft();key=identity(folder)
    if key in visited:continue
    visited.add(key)
    if len(visited)>4000:raise RuntimeError("Bounded project-root discovery exceeded")
    try:
        children=list(folder.iterdir())
        projects=[descriptor(p) for p in children if p.is_file() and p.suffix.casefold()==".uproject"]
        payload=folder/"Content"
        if payload.is_dir() and identity(payload)!=identity(main/"Content"):
            content.setdefault(identity(payload),{"id":identifier(payload),"content":str(payload),"physicalContent":str(payload.resolve()),"projects":projects,"priority":0 if "SKARVIK_STAGE_41188816555" in str(folder) else 1})
        if depth<5:
            for child in children:
                name=child.name.casefold()
                if child.is_dir() and name not in excluded and not any(t in name for t in ["03_validation","mission_archive","mission_source","mission_native","mission_config","missionmaterialbackups"]):
                    queue.append((child,depth+1))
    except (OSError,ValueError) as exc:errors.append({"path":str(folder),"error":str(exc)})
sources=sorted(content.values(),key=lambda p:(p["priority"],p["content"].casefold()))
package_exts={".uasset",".umap"}
summary={"state":"PLAN_STARTED","actualProject":str(main/"AnomaliaPrimeval.uproject"),"mainProject":descriptor(main/"AnomaliaPrimeval.uproject"),"sourceProjects":sources,"priorInventoryRun":41663867323,"priorInstalledAuditRun":41794604995,"sourcePackages":0,"samePathExisting":0,"missingPackagePaths":0,"sourceBytes":0,"rootDirectoriesInspected":len(visited),"errors":errors,"assetsModified":0,"rawSources":[]}
def write():
    (out/"bulk-import-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
write()
with (out/"source-packages.jsonl").open("w",encoding="utf-8") as manifest:
    for source in sources:
        folder=pathlib.Path(source["content"]);count=0;size=0;seen_dirs=set()
        for current,dirs,files in os.walk(folder,followlinks=False):
            canonical=identity(pathlib.Path(current))
            if canonical in seen_dirs:dirs[:]=[];continue
            seen_dirs.add(canonical)
            dirs[:]=[d for d in dirs if d.casefold() not in {".git","__pycache__","python"}]
            for name in files:
                path=pathlib.Path(current)/name
                if path.suffix.casefold() not in package_exts:continue
                relative=path.relative_to(folder).as_posix()
                stat=path.stat();sidecars=[]
                for ext in [".uexp",".ubulk",".uptnl"]:
                    side=path.with_suffix(ext)
                    if side.is_file():sidecars.append({"source":str(side),"bytes":side.stat().st_size,"extension":ext})
                existing=(main/"Content"/relative).is_file()
                row={"sourceId":source["id"],"source":str(path),"relative":relative,"bytes":stat.st_size,"mtimeNS":stat.st_mtime_ns,"sidecars":sidecars,"mainExists":existing}
                manifest.write(json.dumps(row,separators=(",",":"))+"\n")
                count+=1;size+=stat.st_size+sum(x["bytes"] for x in sidecars)
                summary["samePathExisting"]+=existing;summary["missingPackagePaths"]+=not existing
        source.update(packageCount=count,packageBytes=size)
        summary["sourcePackages"]+=count;summary["sourceBytes"]+=size;write()
raw_roots=[pathlib.Path(r"D:\ANOMALIA\sketchfab"),pathlib.Path(r"D:\ANOMALIA\FabImports"),pathlib.Path(r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\FabLibrary"),pathlib.Path(os.environ["USERPROFILE"])/"AppData/Local/Temp/FabLibrary"]
seen_raw=set()
for root in raw_roots:
    if not root.is_dir():continue
    for current,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d.casefold() not in excluded]
        for name in files:
            path=pathlib.Path(current)/name
            if path.suffix.casefold() not in {".fbx",".glb",".gltf",".obj",".zip"}:continue
            key=identity(path)
            if key in seen_raw:continue
            seen_raw.add(key)
            item={"path":str(path),"bytes":path.stat().st_size,"extension":path.suffix.casefold()}
            if path.suffix.casefold()==".zip":
                try:
                    with zipfile.ZipFile(path) as archive:
                        selected=[{"name":m.filename,"bytes":m.file_size,"crc32":m.CRC,"encrypted":bool(m.flag_bits&1)} for m in archive.infolist() if not m.is_dir() and pathlib.PurePosixPath(m.filename).suffix.casefold() in {".fbx",".glb",".gltf",".obj",".uasset",".umap"}]
                        item["members"]=selected
                        item["notices"]=[m.filename for m in archive.infolist() if any(x in pathlib.PurePosixPath(m.filename).name.casefold() for x in ["license","licence","credit","attribution","readme"])]
                except (OSError,zipfile.BadZipFile) as exc:item["error"]=str(exc)
            summary["rawSources"].append(item)
summary["state"]="LOCAL_SOURCE_RECONCILIATION_PLAN_COMPLETE"
summary["elapsedSeconds"]=time.monotonic()-started
summary["sourceManifestSHA256"]=hashlib.sha256((out/"source-packages.jsonl").read_bytes()).hexdigest()
summary["diskFreeBytes"]={drive:__import__("shutil").disk_usage(drive).free for drive in ["C:/","D:/"]}
write()
print(json.dumps({k:summary[k] for k in ["state","sourcePackages","samePathExisting","missingPackagePaths","sourceBytes","elapsedSeconds"]}),flush=True)
