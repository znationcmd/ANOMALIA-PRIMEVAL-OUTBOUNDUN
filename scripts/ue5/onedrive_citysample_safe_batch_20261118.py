"""Conservative OneDrive Files On-Demand staging pilot for City Sample.
Never delete, move, or modify originals. Never claim remote upload is verified.
"""
import os, pathlib, hashlib, shutil, subprocess, uuid, json, datetime, time, stat

SRC = pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample")
ONE = os.environ.get("OneDriveConsumer","")
OUT = pathlib.Path(os.environ["CITYSAMPLE_ONEDRIVE_OUT"])
CAP_BYTES = 1536 * 1024 * 1024
MAX_SINGLE = 1536 * 1024 * 1024
MIN_FREE_C = 4 * 1024 * 1024 * 1024
MIN_FREE_D = 2 * 1024 * 1024 * 1024
MAX_FILES = 2000
MAX_CANDIDATES_EXAMINED = 150000
EXCLUDE = {".git", "intermediate", "saved", "deriveddatacache", ".vs"}
def iso():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as stream:
        while True:
            block=stream.read(1024*1024)
            if not block:break
            h.update(block)
    return h.hexdigest()
def attrs(path):
    import ctypes
    mask=ctypes.windll.kernel32.GetFileAttributesW(str(path))
    return {"raw":int(mask),"offline":bool(mask & 0x1000),
        "unpinned":bool(mask & 0x00100000),
        "reparsePoint":bool(mask & 0x400),
        "recallOnDataAccess":bool(mask & 0x00400000)}
OUT.mkdir(parents=True,exist_ok=True)
state={"state":"STARTING","source":str(SRC),"destinationKind":"OneDrive consumer sync root",
       "maxBatchBytes":CAP_BYTES,"sourceFilesDeleted":0,"sourceFilesModified":0,
       "serverSideUploadVerified":False,"copiedFiles":0,"copiedBytes":0,
       "existingLocalMatches":0,"conflictsUntouched":0,"skippedForSizeOrSpace":0,
       "errors":[],"startedUTC":iso()}
def record():
    state["reportedAtUTC"]=iso()
    temporary=OUT/"onedrive-batch-summary.json.tmp"
    temporary.write_text(json.dumps(state,indent=2,ensure_ascii=False),encoding="utf-8")
    os.replace(temporary,OUT/"onedrive-batch-summary.json")
def abort(reason):
    state["state"]=reason;record()
    print("ONEDRIVE_CITY_SAMPLE_SAFE_BATCH "+json.dumps(state),flush=True)
    return
if not ONE or not pathlib.Path(ONE).is_dir():
    abort("SKIPPED_NO_PERSONAL_ONEDRIVE");raise SystemExit(0)
if not (SRC/"CitySample.uproject").is_file():
    abort("SKIPPED_NO_ORIGINAL_CITY_SAMPLE");raise SystemExit(0)
DEST=pathlib.Path(ONE)/"ANOMALIAZ_PRIGIMALIA"/"Backups"/"CitySample"
state["localOneDriveRootDrive"]=pathlib.Path(ONE).drive
pilot=DEST/"CitySample.uproject"
if not pilot.is_file() or hash_file(pilot)!=hash_file(SRC/"CitySample.uproject"):
    abort("SKIPPED_TINY_PILOT_NOT_LOCALLY_VERIFIED");raise SystemExit(0)
state["tinyPilotAttributes"]=attrs(pilot)
state["localFreeCBefore"]=shutil.disk_usage(ONE).free
state["localFreeDBefore"]=shutil.disk_usage(SRC).free
if state["localFreeCBefore"]<MIN_FREE_C+CAP_BYTES:
    abort("SKIPPED_INSUFFICIENT_C_RESERVE");raise SystemExit(0)
if state["localFreeDBefore"]<MIN_FREE_D:
    abort("SKIPPED_INSUFFICIENT_D_RESERVE");raise SystemExit(0)
# Size-bounded inventory. Preserve all non-target files and avoid reparse points.
candidates=[]
source_files=0
source_bytes=0
large_files=0
large_bytes=0
for base,dirs,names in os.walk(SRC,followlinks=False):
    dirs[:]=[d for d in dirs if d.casefold() not in EXCLUDE and not (pathlib.Path(base)/d).is_symlink()]
    for name in names:
        p=pathlib.Path(base)/name
        try:
            if p.is_symlink():continue
            st=p.stat()
            if stat.S_ISREG(st.st_mode):
                source_files+=1
                source_bytes+=st.st_size
                if st.st_size>MAX_SINGLE:
                    large_files+=1
                    large_bytes+=st.st_size
                elif st.st_size>0:
                    candidates.append((p.relative_to(SRC),st.st_size))
        except OSError:continue
candidates.sort(key=lambda row:(-row[1],str(row[0]).casefold()))
state["eligibleCandidateCount"]=len(candidates)
state["sourceFilesScanned"]=source_files
state["sourceBytesScanned"]=source_bytes
state["oversizeFilesNotHandled"]=large_files
state["oversizeBytesNotHandled"]=large_bytes
record()
state["state"]="COPYING_BOUNDED_PILOT"
for candidate_index,(relative,size) in enumerate(candidates):
    if candidate_index>=MAX_CANDIDATES_EXAMINED:break
    if state["copiedFiles"]>=MAX_FILES or state["copiedBytes"]>=CAP_BYTES:break
    if size>CAP_BYTES-state["copiedBytes"]:continue
    if shutil.disk_usage(ONE).free<MIN_FREE_C+size:
        state["state"]="PAUSED_LOCAL_C_RESERVE";break
    src=SRC/relative
    dest=DEST/relative
    temp=None
    try:
        if dest.exists():
            # Do not open cloud placeholders: reading them may re-download huge files to C:.
            state["conflictsUntouched"]+=1
            continue
        before=src.stat()
        dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_name(".ANOMALIA_COPY_"+uuid.uuid4().hex+".partial")
        h=hashlib.sha256()
        count=0
        with src.open("rb") as fin,temp.open("xb") as fout:
            while True:
                b=fin.read(1024*1024)
                if not b:break
                fout.write(b);h.update(b);count+=len(b)
        after=src.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise RuntimeError("Source changed during copy; original preserved")
        if count!=size or hash_file(temp)!=h.hexdigest():
            raise RuntimeError("Client write verification failed")
        if dest.exists():
            state["conflictsUntouched"]+=1
            continue
        temp.rename(dest)
        temp=None
        # Request Files On-Demand unpin. This is NOT proof of remote verification.
        attr=subprocess.run(["attrib","+U","-P",str(dest)],capture_output=True,text=True,timeout=30)
        if attr.returncode:
            state.setdefault("unpinWarnings",0)
            state["unpinWarnings"]+=1
        state["copiedFiles"]+=1
        state["copiedBytes"]+=size
        if state["copiedFiles"]<=10:
            state.setdefault("samples",[]).append({"relative":str(relative),"bytes":size,"localSha256":h.hexdigest(),"attrs":attrs(dest)})
    except Exception as exc:
        if len(state["errors"])<15:state["errors"].append({"file":str(relative),"message":str(exc)})
    finally:
        if temp is not None and temp.exists():
            try:temp.unlink()
            except OSError:pass
    if state["copiedFiles"]%5==0:record()
else:
    if state["state"]=="COPYING_BOUNDED_PILOT":state["state"]="ELIGIBLE_FILES_EXHAUSTED"
if state["state"]=="COPYING_BOUNDED_PILOT":state["state"]="BATCH_STAGED_CLIENT_SYNC_PENDING"
state["localFreeCAfter"]=shutil.disk_usage(ONE).free
state["localFreeDAfter"]=shutil.disk_usage(SRC).free
state["tinyPilotAttributesAfter"]=attrs(pilot)
record()
print("ONEDRIVE_CITY_SAMPLE_SAFE_BATCH "+json.dumps(state,ensure_ascii=False),flush=True)
