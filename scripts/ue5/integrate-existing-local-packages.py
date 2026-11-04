"""Add existing Unreal packages to the real D project without replacing user files."""
import os,pathlib,json,hashlib,shutil,collections,subprocess,csv,io,time
main=pathlib.Path(r"D:\ANOMALIA\unreal");content=main/"Content"
out=pathlib.Path(os.environ["MISSION_BULK_OUT"])
inputs=out/"input"
plan=json.loads((inputs/"bulk-import-summary.json").read_text(encoding="utf-8"))
manifest=inputs/"source-packages.jsonl"
assert plan["state"]=="LOCAL_SOURCE_RECONCILIATION_PLAN_COMPLETE"
assert hashlib.sha256(manifest.read_bytes()).hexdigest()==plan["sourceManifestSHA256"]
assert (main/"AnomaliaPrimeval.uproject").is_file()
run=os.environ["GITHUB_RUN_ID"]
persistent=main/"Saved/ImportReceipts"/run;persistent.mkdir(parents=True,exist_ok=True)
journal=(persistent/"package-actions.jsonl").open("a",encoding="utf-8")
summary={"state":"IN_PROGRESS","project":str(main/"AnomaliaPrimeval.uproject"),"planRun":41842801517,"sourceManifestSHA256":plan["sourceManifestSHA256"],"counts":{},"copiedBytes":0,"hardlinkedBytes":0,"junctions":[],"originalMaps":0,"originalMapsChanged":[],"sourceFilesWritten":0,"existingAssetsOverwritten":0,"sourceCodeOrConfigModified":False,"nativeValidationRequired":True,"rawModelImportRequired":True}
counts=collections.Counter();cache={};last_process_check=0.;started=time.monotonic()
root=content.resolve();allowed=[root];pool_paths={}
def checkpoint():
    summary["counts"]=dict(counts);summary["elapsedSeconds"]=time.monotonic()-started
    text=json.dumps(summary,indent=2)
    (out/"bulk-integration-summary.json").write_text(text,encoding="utf-8")
    (persistent/"summary.json").write_text(text,encoding="utf-8")
def record(row,state,**extra):
    counts[state]+=1
    journal.write(json.dumps({"sourceId":row.get("sourceId"),"relative":row.get("relative"),"state":state,**extra},separators=(",",":"))+"\n")
    if sum(counts.values())%256==0:journal.flush();checkpoint()
def check_process():
    global last_process_check
    if time.monotonic()-last_process_check<10:return
    result=subprocess.run(["tasklist.exe","/FO","CSV","/NH"],capture_output=True,text=True,errors="replace",check=True)
    forbidden={"unrealeditor.exe","unrealeditor-cmd.exe","anomaliaprimeval.exe","anomaliazprigimalia.exe"}
    if any(row and row[0].casefold() in forbidden for row in csv.reader(io.StringIO(result.stdout))):
        raise RuntimeError("Unreal is active; pause package integration and retain the receipt")
    last_process_check=time.monotonic()
def digest(path):
    stat=path.stat();key=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,str(path) if not stat.st_ino else "")
    if key not in cache:
        h=hashlib.sha256()
        with path.open("rb") as stream:
            while chunk:=stream.read(1024*1024):h.update(chunk)
        cache[key]=h.hexdigest()
    return cache[key]
def identical(a,b):
    x=a.stat();y=b.stat()
    if x.st_size!=y.st_size:return False
    if x.st_ino and x.st_dev==y.st_dev and x.st_ino==y.st_ino:return True
    return digest(a)==digest(b)
def permitted(path):
    resolved=path.resolve()
    return any(resolved.is_relative_to(base) for base in allowed)
def pool_for(source):
    drive=pathlib.Path(source.resolve().anchor)
    base=drive/"AZRP"/run
    payload=base/"payload";marker=base/"owner.json"
    if marker.exists():
        owner=json.loads(marker.read_text())
        assert owner["mainContent"]==str(root)
    else:
        base.mkdir(parents=True,exist_ok=False)
        marker.write_text(json.dumps({"mainContent":str(root),"run":run,"purpose":"Existing resource clones; no source project relocation"}),encoding="utf-8")
    payload.mkdir(exist_ok=True)
    if payload.resolve() not in allowed:allowed.append(payload.resolve())
    pool_paths[str(drive)]=payload
    return payload
def prepare_parent(target,source):
    current=content
    for part in target.parent.relative_to(content).parts:
        child=current/part
        if child.exists():
            if not child.is_dir() or not permitted(child):raise RuntimeError("Preserve an existing external target directory")
        else:
            if current.resolve().stat().st_dev==source.stat().st_dev:
                child.mkdir()
            else:
                payload=pool_paths.get(source.resolve().anchor) or pool_for(source)
                backing=payload/child.relative_to(content)
                backing.mkdir(parents=True,exist_ok=True)
                env=os.environ.copy();env["ANOMALIA_JUNCTION_LINK_PATH"]=str(child);env["ANOMALIA_JUNCTION_BACKING_PATH"]=str(backing)
                subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command","$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:ANOMALIA_JUNCTION_LINK_PATH -Value $env:ANOMALIA_JUNCTION_BACKING_PATH | Out-Null"],env=env,check=True,capture_output=True,text=True)
                summary["junctions"].append({"path":str(child),"ownedResourceBacking":str(backing)})
        current=child
    assert permitted(target.parent)
def source_available(path):
    stat=path.stat()
    return not (getattr(stat,"st_file_attributes",0)&(0x1000|0x400000))
for drive in ["C:/","D:/"]:
    existing=pathlib.Path(drive)/"AZRP"
    if existing.is_dir():
        for marker in existing.glob("*/owner.json"):
            try:
                owner=json.loads(marker.read_text(encoding="utf-8"))
                if owner.get("mainContent")==str(root):allowed.append((marker.parent/"payload").resolve())
            except (OSError,ValueError):pass
check_process()
original_maps={p.relative_to(content).as_posix():digest(p) for p in content.rglob("*.umap")}
original_map_keys={name.casefold() for name in original_maps}
summary["originalMaps"]=len(original_maps);checkpoint()
sources={s["id"]:s for s in plan["sourceProjects"]}
authoritative=pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\Content").resolve()
source_order=sorted(sources,key=lambda key:(0 if pathlib.Path(sources[key]["content"]).resolve()==authoritative else 1,0 if "StorageRecovery" in sources[key]["content"] else 1,sources[key]["content"].casefold()))
by_source=collections.defaultdict(list);same_volume=collections.defaultdict(list)
target_device=root.stat().st_dev
with manifest.open(encoding="utf-8") as stream:
    for line in stream:
        row=json.loads(line);by_source[row["sourceId"]].append(row)
        if pathlib.Path(row["source"]).resolve().drive.casefold()==main.resolve().drive.casefold():
            same_volume[row["relative"].casefold()].append(row)
map_owners={};map_stems={}
for source_id in source_order:
    stems=[]
    for row in by_source[source_id]:
        if pathlib.Path(row["relative"]).suffix.casefold()==".umap":
            stem=row["relative"][:-5];stems.append(stem)
            if row["relative"].casefold() not in original_map_keys:map_owners.setdefault(stem.casefold(),source_id)
    map_stems[source_id]=sorted(stems,key=len,reverse=True)
def alternate(source,row,target,extension=None):
    parent=target.parent
    while not parent.exists():parent=parent.parent
    preferred=parent.resolve().stat().st_dev
    if source.stat().st_dev==preferred or preferred!=target_device:return source
    for candidate in same_volume.get(row["relative"].casefold(),[]):
        path=pathlib.Path(candidate["source"])
        if extension:path=path.with_suffix(extension)
        if path.is_file() and source_available(path) and identical(source,path):return path
    return source
try:
    for source_id in source_order:
        check_process()
        for row in by_source[source_id]:
            check_process()
            source=pathlib.Path(row["source"]);target=content/row["relative"]
            if not source.is_file() or not source_available(source):
                record(row,"SOURCE_NOT_LOCAL_OR_MISSING");continue
            stat=source.stat()
            if stat.st_size!=row["bytes"] or stat.st_mtime_ns!=row["mtimeNS"]:
                record(row,"SOURCE_CHANGED_PRESERVED");continue
            relative=row["relative"]
            if relative.casefold().startswith(("__externalactors__/","__externalobjects__/")):
                world_path=relative.split("/",1)[1]
                owning=next((stem for stem in map_stems[source_id] if world_path.casefold().startswith(stem.casefold()+"/")),None)
                if owning is None or (owning+".umap").casefold() in original_map_keys or map_owners.get(owning.casefold())!=source_id:
                    record(row,"EXISTING_OR_UNOWNED_LEVEL_EXTERNALS_PRESERVED");continue
            if source.suffix.casefold()==".umap" and relative.casefold() not in original_map_keys and map_owners.get(relative[:-5].casefold())!=source_id:
                record(row,"OTHER_SOURCE_LEVEL_VERSION_PRESERVED");continue
            if target.is_file():
                if not identical(source,target):record(row,"EXISTING_ASSET_CONFLICT_PRESERVED");continue
                conflict=False
                for side in row["sidecars"]:
                    dst=target.with_suffix(side["extension"]);src=pathlib.Path(side["source"])
                    if dst.exists() and (not dst.is_file() or not identical(src,dst)):conflict=True
                if conflict:record(row,"EXISTING_SIDECAR_CONFLICT_PRESERVED");continue
                # Existing packages remain untouched; sidecar gaps require a separate validated repair.
                record(row,"ALREADY_PRESENT_IDENTICAL");continue
            if any(target.with_suffix(ext).exists() for ext in [".uexp",".ubulk",".uptnl"]):
                record(row,"EXISTING_ORPHAN_SIDECAR_PRESERVED");continue
            with source.open("rb") as stream:
                if stream.read(4)!=b"\xc1\x83\x2a\x9e":
                    record(row,"NON_EDITOR_PACKAGE_PRESERVED");continue
            payloads=[(pathlib.Path(s["source"]),target.with_suffix(s["extension"]),s["extension"]) for s in row["sidecars"]]+[(source,target,None)]
            prepared=[]
            for src,dst,ext in payloads:
                if not source_available(src):raise RuntimeError("Source sidecar is not local")
                backing=alternate(src,row,dst,ext)
                prepare_parent(dst,backing)
                prepared.append((src,backing,dst))
            copy_by_drive=collections.Counter()
            for src,backing,dst in prepared:
                if backing.stat().st_dev!=dst.parent.resolve().stat().st_dev:copy_by_drive[dst.parent.resolve().anchor]+=src.stat().st_size
            if any(shutil.disk_usage(drive).free<4*1024**3+count for drive,count in copy_by_drive.items()):
                record(row,"DEFERRED_DISK_RESERVE",copyBytesRequired=dict(copy_by_drive));continue
            actions=[]
            for src,backing,dst in prepared:
                before=src.stat()
                if dst.exists():raise RuntimeError("Target appeared during the no-overwrite import")
                if backing.stat().st_dev==dst.parent.resolve().stat().st_dev:
                    os.link(backing,dst)
                    assert os.path.samefile(backing,dst)
                    summary["hardlinkedBytes"]+=before.st_size
                    method="NTFS_HARDLINK_EXISTING_BYTES"
                else:
                    expected=digest(src)
                    with src.open("rb") as inp,dst.open("xb") as dest:shutil.copyfileobj(inp,dest)
                    assert digest(dst)==expected and digest(src)==expected
                    summary["copiedBytes"]+=before.st_size;method="VERIFIED_PRIVATE_COPY"
                after=src.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
                actions.append({"source":str(src),"backing":str(backing),"target":str(dst),"bytes":before.st_size,"method":method})
            record(row,"PACKAGE_ADDED_NATIVE_VALIDATION_REQUIRED",files=actions)
        journal.flush();checkpoint()
    summary["state"]="CONTENT_RECONCILED_NATIVE_VALIDATION_REQUIRED"
except Exception as exc:
    summary["state"]="PAUSED_WITH_PRESERVED_ORIGINALS";summary["error"]=str(exc)
    raise
finally:
    for relative,expected in original_maps.items():
        path=content/relative
        if not path.is_file() or digest(path)!=expected:summary["originalMapsChanged"].append(relative)
    journal.flush();journal.close()
    checkpoint()
    shutil.copyfile(persistent/"package-actions.jsonl",out/"package-actions.jsonl")
    if summary["originalMapsChanged"]:raise RuntimeError("An existing level changed; retain all evidence and stop")
