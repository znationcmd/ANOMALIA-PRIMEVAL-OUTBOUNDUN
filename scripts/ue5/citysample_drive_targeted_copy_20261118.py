"""Copy only original City Sample sources to an existing Google Drive Desktop mirror.
Never delete or modify originals. Local Drive-client writes are not proof of server upload.
"""
import os, pathlib, shutil, hashlib, time, json, uuid, stat, sys
SRC=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample")
DST=pathlib.Path(r"H:\Mon Drive\ANOMALIAZ\02_Modeles_3D\City Sample - Unreal Engine\CitySample")
OUT=pathlib.Path(os.environ["CITYSAMPLE_REPORT_OUT"])
EXCLUDE={".git","deriveddatacache","intermediate","saved",".vs"}
RESERVE=2*1024**3
OUT.mkdir(parents=True,exist_ok=True)
def report():
    summary["reportedAtUTC"]=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    p=OUT/"citysample-cloud-targeted-summary.json"
    tmp=p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(summary,indent=2),encoding="utf-8")
    os.replace(tmp,p)
def free(p):return shutil.disk_usage(p).free
if not (SRC/"CitySample.uproject").is_file():raise RuntimeError("Source CitySample.uproject absent: no changes")
if not (DST/"CitySample.uproject").is_file():raise RuntimeError("Existing Google Drive CitySample mirror not mounted: no changes")
if SRC.resolve()==DST.resolve():raise RuntimeError("Source equals destination")
source=[]
for base,dirs,names in os.walk(SRC,followlinks=False):
    dirs[:]=[d for d in dirs if d.casefold() not in EXCLUDE and not (pathlib.Path(base)/d).is_symlink()]
    for name in names:
        p=pathlib.Path(base)/name
        try:
            if p.is_symlink():continue
            st=p.stat()
            if stat.S_ISREG(st.st_mode):source.append((p.relative_to(SRC),st.st_size))
        except OSError:continue
source.sort(key=lambda x:(-x[1],str(x[0]).casefold()))
summary=dict(state="COPYING_CITY_SAMPLE_ONLY",source=str(SRC),cloudClientPath=str(DST),
    sourceFiles=len(source),sourceBytes=sum(s for _,s in source),
    newClientFilesCopied=0,newClientBytesCopied=0,
    existingSameSizeButNotVerified=0,conflictsPreserved=0,
    skippedForCache=0,copyErrors=0,errors=[],
    originalFilesDeleted=0,originalFilesModified=0,remoteServerVerificationPending=True)
report()
started=time.monotonic()
for i,(rel,size) in enumerate(source):
    if time.monotonic()-started>3.5*3600:
        summary["state"]="PAUSED_RUNTIME_RESUME_REQUIRED";break
    if free(SRC)<RESERVE or free(DST)<RESERVE:
        summary["state"]="PAUSED_DRIVE_CLIENT_CACHE_RESERVE";break
    if size+RESERVE>min(free(SRC),free(DST)):
        summary["skippedForCache"]+=1;continue
    src=SRC/rel;dst=DST/rel
    try:
        if dst.exists():
            if dst.stat().st_size==size:summary["existingSameSizeButNotVerified"]+=1
            else:summary["conflictsPreserved"]+=1
            continue
        before=src.stat()
        if before.st_size!=size:raise RuntimeError("Source changed after inventory")
        dst.parent.mkdir(parents=True,exist_ok=True)
        temp=dst.with_name(".anomalia-citycopy-"+uuid.uuid4().hex+".partial")
        try:
            written=0
            with src.open("rb") as f,temp.open("xb") as g:
                while True:
                    block=f.read(4*1024*1024)
                    if not block:break
                    g.write(block);written+=len(block)
            after=src.stat()
            if written!=size or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                raise RuntimeError("Source modified during copy")
            if dst.exists():
                summary["conflictsPreserved"]+=1
            else:
                temp.rename(dst)
                summary["newClientFilesCopied"]+=1
                summary["newClientBytesCopied"]+=written
        finally:
            if temp.exists():temp.unlink()
    except Exception as e:
        summary["copyErrors"]+=1
        if len(summary["errors"])<20:summary["errors"].append({"file":str(rel),"error":str(e)})
    if i%50==0:report()
else:
    summary["state"]="ALL_SELECTED_FILES_CHECKED_SERVER_VERIFICATION_REQUIRED"
report()
print("CITYSAMPLE_TARGETED_COPY_REPORT "+json.dumps(summary),flush=True)
