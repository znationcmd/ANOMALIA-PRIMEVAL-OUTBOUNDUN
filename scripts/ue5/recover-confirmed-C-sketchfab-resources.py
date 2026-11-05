"""Reference original resources directly; never copy resource payloads between C and D."""
import pathlib,hashlib,json,os,collections,time
main=pathlib.Path(r"D:\ANOMALIA");out=pathlib.Path(os.environ["RECOVERY_REPORT"]);out.mkdir(parents=True,exist_ok=True)
source_root=pathlib.Path(r"C:\sketchfab");downloads=pathlib.Path(r"C:\Users\utilisateur\Downloads")
def files(root):
 if not root.exists():return
 for base,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if not d.startswith(".") and not pathlib.Path(base,d).is_symlink()]
  for name in names:
   p=pathlib.Path(base,name)
   if not name.startswith(".") and p.is_file():yield p
sources=list(files(source_root))
if downloads.exists():
 for root in downloads.iterdir():
  if root.is_dir() and root.name.lower().startswith("cmd"):sources.extend(files(root))
 for name in ["karting-club-lider-outdoor-race-track-ready.zip","sand-mountain-motocross.zip"]:
  if (downloads/name).is_file():sources.append(downloads/name)
report={"mode":"REFERENCE_ORIGINALS_NO_PAYLOAD_COPY","originalsModified":0,"filesExecuted":0,"payloadBytesCopied":0,"unrealImportValidated":False,"files":[]}
groups=collections.defaultdict(list)
for p in sources:
 try:
  before=p.stat();h=hashlib.sha256()
  with p.open("rb") as stream:
   for b in iter(lambda:stream.read(1024*1024),b""):h.update(b)
  after=p.stat()
  if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError("Source changed while cataloguing")
  digest=h.hexdigest()
  row={"source":str(p),"importSource":str(p),"bytes":before.st_size,"sha256":digest,"state":"ORIGINAL_SOURCE_REFERENCED_NO_COPY"}
  groups[digest].append(str(p));report["files"].append(row)
 except Exception as e:report["files"].append({"source":str(p),"state":"ERROR_PRESERVED","error":str(e)})
report["duplicateSourceGroups"]=[{"sha256":sha,"canonicalSource":paths[0],"aliases":paths[1:]} for sha,paths in groups.items() if len(paths)>1]
catalog=main/"unreal"/"SourceAssets"/"ExternalResources"/("original-source-catalog-"+os.environ["GITHUB_RUN_ID"]+".json")
catalog.parent.mkdir(parents=True,exist_ok=True)
text=json.dumps(report,indent=2)
with catalog.open("x",encoding="utf-8") as stream:stream.write(text)
(out/"C-resource-recovery.json").write_text(text,encoding="utf-8")
print(json.dumps({"mode":report["mode"],"files":len(report["files"]),"duplicateSourceGroups":len(report["duplicateSourceGroups"]),"payloadBytesCopied":0,"catalog":str(catalog)}),flush=True)
