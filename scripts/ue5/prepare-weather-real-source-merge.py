"""Prepare three-way weather merges against actual user source; never modify the main project."""
import os,sys,pathlib,json,subprocess,hashlib,re
NEW=pathlib.Path(sys.argv[1]);BASE=pathlib.Path(sys.argv[2])
MAIN=pathlib.Path(r"D:\ANOMALIA\unreal")
OUT=MAIN/"Saved/WeatherMergeReview"/os.environ["GITHUB_RUN_ID"]
OUT.mkdir(parents=True,exist_ok=True)
FILES=["AnomaliaZPrigimaliaInventoryComponent.cpp","AnomaliaZPrigimaliaInventoryComponent.h","AnomaliaZPrigimaliaInventoryWidget.cpp","AnomaliaZPrigimaliaInventoryWidget.h","AnomaliaZPrigimaliaVitalsComponent.cpp","AnomaliaZPrigimaliaVitalsComponent.h","AnomaliaZPrigimaliaGameMode.cpp","Survival/AnomaliaZPrigimaliaWeather.cpp","Survival/AnomaliaZPrigimaliaWeather.h","Survival/AnomaliaZPrigimaliaThermalModel.h","Tests/AnomaliaZPrigimaliaWeatherSurvivalTests.cpp"]
def legacy(s):return s.replace("ANOMALIAZPRIGIMALIA_API","ANOMALIAPRIMEVAL_API").replace("AnomaliaZPrigimalia","Anomalia").replace("\r\n","\n").lstrip("\ufeff").rstrip()+"\n"
report={"mainProject":str(MAIN/"AnomaliaPrimeval.uproject"),"mainFilesModified":0,"commit":os.environ["GITHUB_SHA"],"clean":[],"conflicts":[],"errors":[]}
for name in FILES:
 relative=name.replace("AnomaliaZPrigimalia","Anomalia")
 actual=MAIN/"Source/AnomaliaPrimeval"/relative
 expected=BASE/"unreal/Source/AnomaliaZPrigimalia"/name
 proposed=NEW/"unreal/Source/AnomaliaZPrigimalia"/name
 folder=OUT/"files"/relative;folder.parent.mkdir(parents=True,exist_ok=True)
 current=folder.with_name(folder.name+".current")
 old=folder.with_name(folder.name+".baseline")
 future=folder.with_name(folder.name+".proposed")
 merged=folder.with_name(folder.name+".merged")
 try:
  wanted=legacy(proposed.read_text(encoding="utf-8-sig"));future.write_text(wanted,encoding="utf-8")
  if not actual.exists():
   if expected.exists():raise ValueError("Expected main source is missing; preserve scope")
   merged.write_text(wanted,encoding="utf-8");report["clean"].append({"path":str(actual),"kind":"NEW_FILE","merged":str(merged)});continue
  raw=actual.read_bytes();current.write_text(raw.decode("utf-8-sig").replace("\r\n","\n").rstrip()+"\n",encoding="utf-8")
  if not expected.exists():
   if current.read_text(encoding="utf-8")!=wanted:raise ValueError("New native path already contains different work")
   merged.write_text(wanted,encoding="utf-8");code=0
  else:
   old.write_text(legacy(expected.read_text(encoding="utf-8-sig")),encoding="utf-8")
   result=subprocess.run(["git","merge-file","--stdout",str(current),str(old),str(future)],capture_output=True)
   code=result.returncode
   merged_bytes=result.stdout
   if code==1 and relative=="AnomaliaInventoryWidget.h":
    text=merged_bytes.decode("utf-8")
    pattern=r"<<<<<<<[^\n]*\n(.*?)\n=======\n(.*?)\n>>>>>>>[^\n]*\n"
    match=re.search(pattern,text,re.S)
    if match:
     ours=[v.strip().rstrip(",") for v in match.group(1).splitlines() if v.strip()]
     theirs=[v.strip().rstrip(",") for v in match.group(2).splitlines() if v.strip()]
     if ours==["DogCommand","QuickbarActivate","CombineCraft"] and set(theirs)=={"DogCommand","WetHead"} and len(theirs)==2:
      replacement="\n".join("    "+name+("," if i<3 else "") for i,name in enumerate(ours+["WetHead"]))+"\n"
      text=text[:match.start()]+replacement+text[match.end():]
      if not re.search(r"^(?:<<<<<<<|=======|>>>>>>>)",text,re.M):
       merged_bytes=text.encode("utf-8");code=0
       report.setdefault("resolutions",[]).append({"path":str(actual),"reason":"Preserved existing DogCommand/QuickbarActivate/CombineCraft action order and appended WetHead"})
   merged.write_bytes(merged_bytes)
   if code<0 or code>127:raise RuntimeError(result.stderr.decode(errors="replace"))
  item={"path":str(actual),"originalSHA256":hashlib.sha256(raw).hexdigest(),"merged":str(merged),"conflictCount":code}
  (report["conflicts"] if code else report["clean"]).append(item)
 except Exception as exc:report["errors"].append({"path":str(actual),"error":str(exc)})
report["state"]="CLEAN_THREE_WAY_MERGES_READY_FOR_NATIVE_VALIDATION" if not report["conflicts"] and not report["errors"] else "MERGE_CONFLICTS_PRESERVED_FOR_REVIEW"
(OUT/"merge-review.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("ACTUAL_SOURCE_MERGE_REVIEW "+json.dumps(report),flush=True)
