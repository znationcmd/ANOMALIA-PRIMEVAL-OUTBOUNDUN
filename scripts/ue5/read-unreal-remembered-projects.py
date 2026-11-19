"""Read only Unreal/Epic remembered project locations and inspect their descriptors."""
import pathlib,os,json,re
out=pathlib.Path(os.environ["UE_PROJECT_LIST_OUT"]);out.mkdir(parents=True,exist_ok=True)
report={"readOnly":True,"rememberedLocations":[],"projects":[],"errors":[]}
roots=set();projects=set()
def add(value,origin):
 value=value.strip().strip('"').replace("\\\\","\\")
 p=pathlib.Path(value)
 if not p.is_absolute():return
 report["rememberedLocations"].append({"path":str(p),"origin":str(origin),"exists":p.exists()})
 if p.suffix.lower()==".uproject":projects.add(p)
 elif p.is_dir():roots.add(p)
for profile in pathlib.Path("C:/Users").iterdir():
 if not profile.is_dir():continue
 roots.add(profile/"Documents"/"Unreal Projects")
 roots.add(profile/"Documents"/"UnrealProjects")
 local=profile/"AppData"/"Local"
 configs=list((local/"EpicGamesLauncher"/"Saved"/"Config").glob("*/GameUserSettings.ini"))
 configs+=list((local/"UnrealEngine").glob("*/Saved/Config/*/EditorSettings.ini"))
 configs+=list((local/"UnrealEngine").glob("*/Saved/Config/*/EditorGameAgnostic.ini"))
 for config in configs:
  try:
   for line in config.read_text(encoding="utf-8-sig",errors="replace").splitlines():
    if not any(k.lower() in line.lower() for k in ["CreatedProjectPaths","RecentlyOpenedProjectFiles","LastOpenedProject","ProjectPath"]):continue
    for value in re.findall(r'[A-Za-z]:[\\/][^"\r\n,)]*',line):add(value,config)
  except OSError as e:report["errors"].append(str(e))
for p in [pathlib.Path("C:/Unreal Projects"),pathlib.Path("D:/Unreal Projects"),pathlib.Path("C:/Users/Public/Documents/Unreal Projects")]:
 if p.exists():roots.add(p)
for root in roots:
 if not root.exists():continue
 for base,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if d.lower() not in {"content","saved","intermediate","binaries","deriveddatacache",".git","node_modules","engine"} and not pathlib.Path(base,d).is_symlink()]
  for f in files:
   if f.lower().endswith(".uproject"):projects.add(pathlib.Path(base,f))
seen=set()
for p in sorted(projects):
 try:
  if not p.is_file():continue
  key=str(p.resolve()).lower()
  if key in seen:continue
  seen.add(key);data=json.loads(p.read_text(encoding="utf-8-sig"))
  item={"project":str(p),"resolved":str(p.resolve()),"engine":data.get("EngineAssociation"),"modules":data.get("Modules",[]),"plugins":data.get("Plugins",[]),"contentExists":(p.parent/"Content").exists()}
  report["projects"].append(item);print(json.dumps(item),flush=True)
 except Exception as e:report["errors"].append({"project":str(p),"error":str(e)})
(out/"unreal-remembered-projects.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"projects":len(report["projects"]),"rememberedLocations":len(report["rememberedLocations"]),"errors":len(report["errors"])}),flush=True)
