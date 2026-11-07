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
def rollback():
 plan_path=OUT/"deployment-plan.json"
 if not plan_path.exists():return
 plan=json.loads(plan_path.read_text(encoding="utf-8"))
 if plan.get("mainProject")!=str(MAIN):raise RuntimeError("Rollback owner mismatch; preserve all files")
 if (OUT/"actual-native-result.json").exists():
  prior=json.loads((OUT/"actual-native-result.json").read_text(encoding="utf-8"))
  if prior.get("mainProjectUpdated"):return
 for row in plan["files"]:
  dst=pathlib.Path(row["path"])
  if dst.exists() and digest(dst) not in {row["desiredSHA256"],row.get("originalSHA256")}:
   raise RuntimeError("New source changes detected after installation; preserve them and all backups")
 failed=OUT/"failed-native-output";failed.mkdir(exist_ok=True)
 for row in plan["files"]:
  dst=pathlib.Path(row["path"])
  if row["existed"]:
   original=OUT/"originals/Source"/dst.relative_to(MAIN/"Source/AnomaliaPrimeval")
   if not original.is_file():raise RuntimeError("Rollback original missing; preserve diagnostics")
   temporary=dst.with_name(dst.name+".restore-"+uuid.uuid4().hex)
   shutil.copy2(original,temporary);os.replace(temporary,dst)
  elif dst.exists():
   archived=failed/"Source"/dst.relative_to(MAIN/"Source/AnomaliaPrimeval");archived.parent.mkdir(parents=True,exist_ok=True);shutil.move(dst,archived)
 if plan.get("binariesBackedUp"):
  if (MAIN/"Binaries").exists():
   destination=failed/("Binaries-"+uuid.uuid4().hex[:8]);shutil.move(MAIN/"Binaries",destination)
  shutil.copytree(OUT/"originals/Binaries",MAIN/"Binaries")
if "--rollback-only" in sys.argv:
 rollback();print("Rollback guard completed; confirmed successful installations are retained",flush=True);raise SystemExit(0)
save()
if report["conflicts"] or report["errors"]:
 result["state"]="UNRESOLVED_MERGES_PRESERVED";save();raise SystemExit(0)
validated=[]
for prior in (MAIN/"Saved/WeatherValidation").glob("*/weather-validation-report.json"):
 try:
  data=json.loads(prior.read_text(encoding="utf-8"))
  if data.get("sourceFingerprint")==report.get("proposedSourceFingerprint") and data.get("sourceFingerprint") and any(v.get("project")=="preserved_source_validation" and v.get("exitCode")==0 for v in data.get("checks",[])):validated.append(prior)
 except (ValueError,OSError):pass
if not validated:raise RuntimeError("These exact proposed native sources have no passed engine build/regressions; preserve main source")
result["validatedSourceReport"]=str(max(validated,key=lambda p:p.stat().st_mtime_ns))
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
 if dst.exists() and getattr(dst.lstat(),"st_file_attributes",0)&0x400:raise RuntimeError("Existing source reparse point preserved")
 if not dst.parent.resolve().is_relative_to(sources.resolve()):raise RuntimeError("Main source parent escapes the actual module")
 entries.append((dst,src,dst.exists()))
backup=OUT/"originals";backup.mkdir()
if (MAIN/"Binaries").exists():shutil.copytree(MAIN/"Binaries",backup/"Binaries")
def atomic_copy(src,dst):
 temporary=dst.with_name(dst.name+".weather-"+uuid.uuid4().hex+".tmp")
 with temporary.open("xb") as f:
  f.write(src.read_bytes());f.flush();os.fsync(f.fileno())
 os.replace(temporary,dst)
plan={"mainProject":str(MAIN),"binariesBackedUp":(backup/"Binaries").exists(),"files":[]}
for dst,src,existed in entries:
 if existed:
  original=backup/"Source"/dst.relative_to(sources);original.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,original)
 plan["files"].append({"path":str(dst),"existed":existed,"originalSHA256":digest(dst) if existed else None,"desiredSHA256":digest(src)})
with (OUT/"deployment-plan.json").open("x",encoding="utf-8") as f:
 json.dump(plan,f);f.flush();os.fsync(f.fileno())
try:
 for dst,src,existed in entries:
  dst.parent.mkdir(parents=True,exist_ok=True);atomic_copy(src,dst)
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
 try:rollback()
 except Exception as restore_error:result["restoreError"]=str(restore_error)
 result["state"]="NATIVE_FAILURE_ORIGINALS_RESTORED" if not result.get("restoreError") else "NATIVE_FAILURE_NEW_CHANGES_AND_BACKUPS_PRESERVED"
 result["error"]=str(exc);save();raise
