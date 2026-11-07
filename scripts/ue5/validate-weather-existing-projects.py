"""Validate weather changes against preserved projects; install only on exact main-source baselines."""
import os,sys,pathlib,json,shutil,subprocess,hashlib,time
NEW=pathlib.Path(sys.argv[1]);BASE=pathlib.Path(sys.argv[2])
MAIN=pathlib.Path(r"D:\ANOMALIA\unreal")
VALIDATION=pathlib.Path(r"C:\ANOMALIA_MISSION_41801391717")
OUT=MAIN/"Saved/WeatherValidation"/os.environ["GITHUB_RUN_ID"]
OUT.mkdir(parents=True,exist_ok=True)
ENGINE=pathlib.Path(r"C:\Program Files\Epic Games\UE_5.8")
FILES=[
"AnomaliaZPrigimaliaInventoryComponent.cpp","AnomaliaZPrigimaliaInventoryComponent.h",
"AnomaliaZPrigimaliaInventoryWidget.cpp","AnomaliaZPrigimaliaInventoryWidget.h",
"AnomaliaZPrigimaliaVitalsComponent.cpp","AnomaliaZPrigimaliaVitalsComponent.h",
"AnomaliaZPrigimaliaGameMode.cpp","Survival/AnomaliaZPrigimaliaWeather.cpp",
"Survival/AnomaliaZPrigimaliaWeather.h","Survival/AnomaliaZPrigimaliaThermalModel.h",
"Tests/AnomaliaZPrigimaliaWeatherSurvivalTests.cpp"]
report={"mainProject":str(MAIN/"AnomaliaPrimeval.uproject"),"validationProject":str(VALIDATION/"unreal/AnomaliaZPrigimalia.uproject"),"commit":os.environ["GITHUB_SHA"],"mainProjectUpdated":False,"originalMapsModified":0,"saveFilesModified":0,"matches":[],"conflicts":[],"checks":[],"gameplayAccepted":False}
def norm(text):return text.replace("\r\n","\n").lstrip("\ufeff").rstrip()+"\n"
def convert(text,old):
 if not old:return text
 return text.replace("ANOMALIAZPRIGIMALIA_API","ANOMALIAPRIMEVAL_API").replace("AnomaliaZPrigimalia","Anomalia")
def persist():
 (OUT/"weather-validation-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print("WEATHER_NATIVE_STATUS "+json.dumps(report),flush=True)
def audit():
 descriptor=json.loads((MAIN/"AnomaliaPrimeval.uproject").read_text(encoding="utf-8-sig"))
 names=[m["Name"] for m in descriptor.get("Modules",[])]
 module=next((m for m in names if m in {"AnomaliaPrimeval","AnomaliaZPrigimalia"}),None)
 if not module:raise RuntimeError("Unrecognized actual native module; preserve main project")
 old=module=="AnomaliaPrimeval"
 targets=[]
 for name in FILES:
  relative=name.replace("AnomaliaZPrigimalia","Anomalia") if old else name
  dst=MAIN/"Source"/module/relative
  original=BASE/"unreal/Source/AnomaliaZPrigimalia"/name
  desired=convert((NEW/"unreal/Source/AnomaliaZPrigimalia"/name).read_text(encoding="utf-8-sig"),old)
  expected=convert(original.read_text(encoding="utf-8-sig"),old) if original.exists() else None
  actual=dst.read_text(encoding="utf-8-sig") if dst.exists() else None
  if actual is not None and norm(actual)==norm(desired):report["matches"].append({"path":str(dst),"state":"ALREADY_PRESENT"})
  elif actual is None and expected is None:report["matches"].append({"path":str(dst),"state":"NEW_NATIVE_FILE"})
  elif actual is not None and expected is not None and norm(actual)==norm(expected):report["matches"].append({"path":str(dst),"state":"EXACT_BASELINE"})
  else:report["conflicts"].append({"path":str(dst),"reason":"Existing source differs; no automatic replacement"})
  targets.append((dst,desired))
 return module,targets
module,targets=audit();persist()
if "--audit-only" in sys.argv:raise SystemExit(0)
if not (VALIDATION/"unreal/AnomaliaZPrigimalia.uproject").is_file():raise RuntimeError("Preserved validation project missing; do not create a substitute")
if shutil.disk_usage("C:/").free<12*1024**3:raise RuntimeError("Preserve 12 GiB C reserve before native compilation")
backup=OUT/"validation-originals";backup.mkdir()
for relative in ["unreal/Source","unreal/Config","public/config","scripts/ue5"]:
 src=VALIDATION/relative
 if src.exists():shutil.copytree(src,backup/relative)
 shutil.copytree(NEW/relative,VALIDATION/relative,dirs_exist_ok=True)
cmd=[sys.executable,str(VALIDATION/"scripts/ue5/validate-build.py"),"--engine-root",str(ENGINE),"--output",str(OUT/"validated-source"),"--run-tests","--require-loot-tests"]
with (OUT/"validation-process.log").open("w",encoding="utf-8") as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
report["checks"].append({"project":"preserved_source_validation","exitCode":code});persist()
if code:raise SystemExit(code)
if report["conflicts"]:
 report["state"]="SOURCE_VALIDATED_MAIN_BASELINE_CONFLICTS_PRESERVED";persist();raise SystemExit(0)
# Every main source file passed the exact-baseline guard. Preserve code and binaries before install.
backup_main=OUT/"main-originals"
if (MAIN/"Binaries").exists():shutil.copytree(MAIN/"Binaries",backup_main/"Binaries")
written=[]
try:
 for dst,text in targets:
  existed=dst.exists()
  if existed:
   saved=backup_main/"Source"/dst.relative_to(MAIN/"Source");saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,saved)
  dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(text,encoding="utf-8");written.append((dst,existed))
 for target in [module+"Editor",module]:
  command=[os.environ.get("COMSPEC","cmd.exe"),"/d","/c",str(ENGINE/"Engine/Build/BatchFiles/Build.bat"),target,"Win64","Development","-Project="+str(MAIN/"AnomaliaPrimeval.uproject"),"-WaitMutex","-NoHotReloadFromIDE"]
  with (OUT/(target+".log")).open("w",encoding="utf-8") as log:code=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
  report["checks"].append({"project":"actual_main","target":target,"exitCode":code});persist()
  if code:raise RuntimeError("Actual main compilation failed; restore its original source and binaries")
 report["mainProjectUpdated"]=True;report["state"]="MAIN_NATIVE_COMPILED_GAMEPLAY_VALIDATION_REQUIRED";persist()
except Exception as exc:
 failed=OUT/"failed-native-output";failed.mkdir()
 for dst,existed in written:
  if existed:shutil.copy2(backup_main/"Source"/dst.relative_to(MAIN/"Source"),dst)
  elif dst.exists():
   saved=failed/"Source"/dst.relative_to(MAIN/"Source");saved.parent.mkdir(parents=True,exist_ok=True);shutil.move(dst,saved)
 if (backup_main/"Binaries").exists():
  if (MAIN/"Binaries").exists():shutil.move(MAIN/"Binaries",failed/"Binaries")
  shutil.copytree(backup_main/"Binaries",MAIN/"Binaries")
 report["state"]="MAIN_NATIVE_FAILURE_ORIGINALS_RESTORED";report["error"]=str(exc);persist();raise
