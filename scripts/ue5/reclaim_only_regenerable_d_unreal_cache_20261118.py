"""Release only explicitly scoped, cold regenerable Unreal caches on D:.

Never touch UE map/content/source assets, Saved, plugins, or built game files.
Keep all Intermediate/Build PCH, OBJ, makefiles, binaries, and project source.
"""
import os, pathlib, time, json, shutil, stat, datetime, subprocess
D=pathlib.Path("D:/")
GAME=pathlib.Path(r"D:\ANOMALIA\unreal")
SOURCE=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample")
OUT=pathlib.Path(os.environ["D_CACHE_RECOVERY_OUT"])
roots=[
 (GAME/"DerivedDataCache", {"cache", "udd", "ddc", "ddp", "bin"}, "game_derived_data"),
 (GAME/"Intermediate"/"CachedAssetRegistry", {"bin"}, "asset_registry"),
]
specific=[
 (SOURCE/"Intermediate"/"ProjectFiles"/"UE5.vcxproj", "generated_citysample_vcxproj"),
 (SOURCE/"Intermediate"/"ProjectFiles"/"UE5.vcxproj.filters", "generated_citysample_vs_filters"),
]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def is_reparse(path):
  return bool(getattr(path.lstat(),"st_file_attributes",0)&0x400)
def active_unreal():
  s=subprocess.run(["tasklist.exe","/FO","CSV","/NH"],capture_output=True,text=True,timeout=30)
  if s.returncode:raise RuntimeError("Unable to establish Unreal process inactivity")
  names=["unrealeditor.exe","unrealeditor-cmd.exe","unrealbuildtool.exe","shadercompileworker.exe","anomaliprimeval.exe"]
  return [n for n in names if '"'+n+'"' in s.stdout.lower()]
if not (GAME/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
  raise RuntimeError("Main game world missing - abort all cleanup")
if not (SOURCE/"CitySample.uproject").is_file():
  raise RuntimeError("Original City Sample missing - abort all cleanup")
if active_unreal():raise RuntimeError("Unreal/game active - abort all cleanup")
OUT.mkdir(parents=True,exist_ok=True)
journal=OUT/"regenerable-d-cache-deletions.jsonl"
report={"state":"SCANNING_SAFE_GENERATED_CACHES","startUTC":now(),
  "freeDBefore":shutil.disk_usage(D).free,"deletedFiles":0,
  "logicalCacheBytesRemoved":0,"byKind":{},"errors":[],"sourceAssetsDeleted":0,
  "gameMapsModified":0,"saveFilesModified":0,"compiledPCHPreserved":True}
cutoff=time.time()-12*3600
def safe_file(p,root,extensions):
  if not p.is_file() or p.is_symlink() or is_reparse(p):return False
  if p.suffix.lower().lstrip(".") not in extensions:return False
  if p.resolve().anchor.lower()!="d:\\":return False
  if not p.resolve().is_relative_to(root.resolve()):return False
  st=p.lstat()
  return stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_mtime<cutoff
def prune(p,kind,j,root,extensions):
  if not safe_file(p,root,extensions):return
  before=p.stat()
  entry={"path":str(p),"bytes":before.st_size,"mtime_ns":before.st_mtime_ns,"kind":kind}
  j.write(json.dumps({**entry,"state":"PREPARED"})+"\n");j.flush();os.fsync(j.fileno())
  after=p.stat()
  if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
    raise RuntimeError("Generated cache changed during cleanup")
  p.unlink()
  report["deletedFiles"]+=1;report["logicalCacheBytesRemoved"]+=before.st_size
  kindRecord=report["byKind"].setdefault(kind,{"count":0,"bytes":0})
  kindRecord["count"]+=1;kindRecord["bytes"]+=before.st_size
  j.write(json.dumps({**entry,"state":"COLD_REGENERABLE_CACHE_RELEASED"})+"\n")
with journal.open("a",encoding="utf-8") as j:
  for root,ext,kind in roots:
    if not root.is_dir() or root.is_symlink() or is_reparse(root):continue
    for base,dirs,names in os.walk(root,followlinks=False):
      dirs[:]=[d for d in dirs if not is_reparse(pathlib.Path(base)/d)]
      for name in names:
        p=pathlib.Path(base)/name
        try:prune(p,kind,j,root,ext)
        except Exception as e:
          if len(report["errors"])<25:report["errors"].append({"file":str(p),"error":str(e)})
  for p,kind in specific:
    try:
      root=SOURCE/"Intermediate"/"ProjectFiles"
      if root.is_dir() and not root.is_symlink() and not is_reparse(root):
        prune(p,kind,j,root,{"vcxproj","filters"})
    except Exception as e:
      if len(report["errors"])<25:report["errors"].append({"file":str(p),"error":str(e)})
report["state"]="SAFE_D_CACHE_CLEANUP_FINISHED"
report["finishedUTC"]=now()
report["freeDAfter"]=shutil.disk_usage(D).free
report["actualDFreeDelta"]=report["freeDAfter"]-report["freeDBefore"]
report["mainMapPresentAfter"]= (GAME/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file()
report["originalCitySamplePresentAfter"]= (SOURCE/"CitySample.uproject").is_file()
report["protectedPCHFiles"]=[str(p) for p in (GAME/"Intermediate"/"Build").rglob("*.pch") if p.is_file()][:10]
(OUT/"d-cache-recovery-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("ANOMALIA_D_CACHE_SAFE_RECOVERY "+json.dumps(report),flush=True)
