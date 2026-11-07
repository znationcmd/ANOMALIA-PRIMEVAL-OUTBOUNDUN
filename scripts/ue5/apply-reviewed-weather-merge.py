"""Install only clean reviewed three-way native merges, with complete rollback and actual D regression execution."""
import os,sys,pathlib,json,hashlib,shutil,subprocess,uuid
MAIN=pathlib.Path(r"D:\ANOMALIA\unreal")
REVIEW=MAIN/"Saved/WeatherMergeReview"/os.environ["GITHUB_RUN_ID"]
report=json.loads((REVIEW/"merge-review.json").read_text(encoding="utf-8"))
OUT=REVIEW/"native-validation";OUT.mkdir(parents=True,exist_ok=True)
ENGINE=pathlib.Path(r"C:\Program Files\Epic Games\UE_5.8")
result={"mainProject":str(MAIN/"AnomaliaPrimeval.uproject"),"sourceCommit":os.environ["GITHUB_SHA"],"mainProjectUpdated":False,"originalMapsModified":0,"saveFilesModified":0,"checks":[],"gameplayAccepted":False}
def save():
 (OUT/"actual-native-result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
 print("ACTUAL_MERGED_NATIVE "+json.dumps(result),flush=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
save()
if report["conflicts"] or report["errors"]:
 result["state"]="UNRESOLVED_MERGES_PRESERVED";save();raise SystemExit(0)
prior=MAIN/"Saved/WeatherValidation/42379630246/weather-validation-report.json"
prior_data=json.loads(prior.read_text(encoding="utf-8"))
if not any(c.get("project")=="preserved_source_validation" and c.get("exitCode")==0 for c in prior_data["checks"]):
 raise RuntimeError("Previous engine build/regressions did not pass; preserve actual source")
if shutil.disk_usage("D:/").free<10*1024**3:raise RuntimeError("Preserve 10 GiB main native build reserve")
sources=MAIN/"Source/AnomaliaPrimeval"
allowed={"AnomaliaInventoryComponent.cpp","AnomaliaInventoryComponent.h","AnomaliaInventoryWidget.cpp","AnomaliaInventoryWidget.h","AnomaliaVitalsComponent.cpp","AnomaliaVitalsComponent.h","AnomaliaGameMode.cpp","Survival/AnomaliaWeather.cpp","Survival/AnomaliaWeather.h","Survival/AnomaliaThermalModel.h","Tests/AnomaliaWeatherSurvivalTests.cpp"}
entries=[]
for row in report["clean"]:
 dst=pathlib.Path(row["path"]);src=pathlib.Path(row["merged"])
 if not dst.is_relative_to(sources) or dst.relative_to(sources).as_posix() not in allowed or not src.resolve().is_relative_to(REVIEW.resolve()):raise RuntimeError("Reviewed source scope differs")
 if row.get("originalSHA256"):
  if not dst.is_file() or digest(dst)!=row["originalSHA256"]:raise RuntimeError("Main file changed since review; preserve new work")
 elif dst.exists():raise RuntimeError("A reviewed new native path now exists; preserve it")
 text=src.read_text(encoding="utf-8")
 if any(line.startswith(("<<<<<<<","=======",">>>>>>>")) for line in text.splitlines()):raise RuntimeError("Unresolved conflict marker; source preserved")
 entries.append((dst,src,dst.exists()))
backup=OUT/"originals";backup.mkdir()
if (MAIN/"Binaries").exists():shutil.copytree(MAIN/"Binaries",backup/"Binaries")
written=[]
try:
 for dst,src,existed in entries:
  if existed:
   original=backup/"Source"/dst.relative_to(sources);original.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,original)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);written.append((dst,existed))
 for target in ["AnomaliaPrimevalEditor","AnomaliaPrimeval"]:
  cmd=[os.environ.get("COMSPEC","cmd.exe"),"/d","/c",str(ENGINE/"Engine/Build/BatchFiles/Build.bat"),target,"Win64","Development","-Project="+str(MAIN/"AnomaliaPrimeval.uproject"),"-WaitMutex","-NoHotReloadFromIDE"]
  with (OUT/(target+".log")).open("w",encoding="utf-8") as f:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
  result["checks"].append({"kind":"build","target":target,"exitCode":code});save()
  if code:raise RuntimeError("Actual native build failed; restoring originals")
 export=OUT/("automation-"+uuid.uuid4().hex);export.mkdir()
 cmd=[str(ENGINE/"Engine/Binaries/Win64/UnrealEditor-Cmd.exe"),str(MAIN/"AnomaliaPrimeval.uproject"),"-unattended","-nopause","-nosound","-NullRHI","-ExecCmds=Automation RunTests Anomalia.Native.; Quit","-ReportExportPath="+str(export),"-abslog="+str(export/"editor.log")]
 with (export/"process.log").open("w",encoding="utf-8") as f:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
 tests=json.loads((export/"index.json").read_text(encoding="utf-8-sig")).get("tests",[])
 expected={"Anomalia.Native.WeatherThermalModel","Anomalia.Native.FrozenInventoryPersistence","Anomalia.Native.FarmFoodConsumption"}
 passed={t.get("fullTestPath") for t in tests if t.get("state")=="Success"}
 failures=[t.get("fullTestPath") for t in tests if t.get("state") not in {"Success","Skipped"}]
 result["checks"].append({"kind":"actual_native_automation","exitCode":code,"tests":len(tests),"requiredPassed":sorted(expected&passed),"failures":failures});save()
 if code or failures or not expected.issubset(passed):raise RuntimeError("Required actual main regressions did not pass; restoring originals")
 result["mainProjectUpdated"]=True;result["state"]="ACTUAL_MAIN_BUILDS_AND_NATIVE_REGRESSIONS_PASSED_PIE_REQUIRED";save()
except BaseException as exc:
 failed=OUT/"failed-native-output";failed.mkdir(exist_ok=True)
 for dst,existed in written:
  if existed:shutil.copy2(backup/"Source"/dst.relative_to(sources),dst)
  elif dst.exists():
   archived=failed/"Source"/dst.relative_to(sources);archived.parent.mkdir(parents=True,exist_ok=True);shutil.move(dst,archived)
 if (backup/"Binaries").exists():
  if (MAIN/"Binaries").exists():shutil.move(MAIN/"Binaries",failed/"Binaries")
  shutil.copytree(backup/"Binaries",MAIN/"Binaries")
 result["state"]="NATIVE_FAILURE_ORIGINALS_RESTORED";result["error"]=str(exc);save();raise
