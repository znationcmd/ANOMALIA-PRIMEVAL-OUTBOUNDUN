"""Safely install a narrow extra UE native map identifier on the ORIGINAL D project.

Requires an unmodified verified native file baseline, backs up each original,
only edits the new enum/height branch and one map resolver. Does NOT modify any
pre-existing map, asset, or game settings. Mode rollback requires exact post
hash match, so user edits during a run cannot be clobbered.
"""
import os,sys,pathlib,json,hashlib,shutil,datetime
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
OUT=pathlib.Path(os.environ["APOCALYPTIC_BUILD_OUT"])
REPO=pathlib.Path(__file__).resolve().parents[2]
EXPECTED={
 "header":"40AB60DB23898F002DC05CE052A322B66884A1BBD275CF6ED4B587823ED80E63",
 "cpp":"BB47579CEBF6A4E3B3AFF3FB14070740DD0F54D6D58721F51D39CECBBA469A0F"
}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest().upper()
def write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_name(path.name+".APOCALYPTIC_TEMP")
 try:
  temp.write_text(text,encoding="utf-8")
  os.replace(temp,path)
 finally:
  if temp.exists():temp.unlink()
def report(data):
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"source-install-result.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
 print("APOCALYPTIC_NATIVE_SOURCE_INSTALL "+json.dumps(data,ensure_ascii=False),flush=True)
def findpaths():
 project=json.loads((PROJECT/"AnomaliaPrimeval.uproject").read_text(encoding="utf-8-sig"))
 module=project["Modules"][0]["Name"]
 if module!="AnomaliaPrimeval":raise RuntimeError("Unknown D native game module; preserve it")
 native=PROJECT/"Source"/module/"World"
 return module,{"header":native/"AnomaliaPrimevalRequestedWorldHeights.h",
                "cpp":native/"AnomaliaPrimevalRequestedWorldLibrary.cpp"}
def apply():
 module,files=findpaths()
 dest=PROJECT/"Content/Maps/PRIGIMALIA_APOCALYPTIC_OUTBREAK.umap"
 if dest.exists():raise RuntimeError("Native map package already exists; refuse to reinstall blindly")
 for name,path in files.items():
  if not path.is_file():raise RuntimeError("Native source not found: "+str(path))
  digest=sha(path)
  if digest!=EXPECTED[name]:raise RuntimeError("Installed source changed: "+name+" SHA "+digest+" ; preserve local work")
 existingHeader=files["header"].read_text(encoding="utf-8-sig")
 existingCpp=files["cpp"].read_text(encoding="utf-8-sig")
 sourceHeader=(REPO/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaExtraWorldHeights.h").read_text(encoding="utf-8")
 start=sourceHeader.find(" if(world==EWorld::ApocalypticOutbreak){")
 end=sourceHeader.find(" if(world==EWorld::Karskov){",start)
 if start<0 or end<start:raise RuntimeError("Repository terrain formula marker not found")
 fragment=sourceHeader[start:end]
 if "ApocalypticOutbreak" in existingHeader or "APOCALYPTIC_OUTBREAK" in existingCpp:
  raise RuntimeError("New map identifier already partially installed; refuse editing")
 anchors=[
  ("enum class EWorld : std::uint8_t { Karskov, Vorgrad, Nemoris, Drakheim, Yudinavia, Moscovie, Corsivia, BotSever, Invalid };",
   "enum class EWorld : std::uint8_t { Karskov, Vorgrad, Nemoris, Drakheim, Yudinavia, Moscovie, Corsivia, BotSever, ApocalypticOutbreak, Invalid };"),
  ("world==EWorld::Corsivia ? 15000 : world==EWorld::BotSever ? 50000 : 0;",
   "world==EWorld::Corsivia ? 15000 : world==EWorld::BotSever ? 50000 :\n        world==EWorld::ApocalypticOutbreak ? 15000 : 0;"),
  (" if(world==EWorld::Karskov){",fragment+" if(world==EWorld::Karskov){")
 ]
 header=existingHeader
 for orig,replacement in anchors:
  if header.count(orig)!=1:raise RuntimeError("Unique native header anchor missing, refuse editing")
  header=header.replace(orig,replacement)
 orig=' if(Id==TEXT("BOT_SEVER"))return EWorld::BotSever;'
 if existingCpp.count(orig)!=1:raise RuntimeError("Native map resolver differs; refuse editing")
 cpp=existingCpp.replace(orig,orig+'\n if(Id==TEXT("APOCALYPTIC_OUTBREAK"))return EWorld::ApocalypticOutbreak;')
 backup=OUT/"source-backups"
 if backup.exists():raise RuntimeError("Backup directory exists; refuse to overwrite source backups")
 backup.mkdir(parents=True,exist_ok=False)
 records=[]
 for name,path in files.items():
  prev=backup/path.name
  shutil.copy2(path,prev)
  if sha(prev)!=EXPECTED[name]:raise RuntimeError("Backup hash mismatch, abort")
  records.append({"name":name,"path":str(path),"backup":str(prev),"preSHA256":EXPECTED[name]})
 for name,text in (("header",header),("cpp",cpp)):
  write(files[name],text)
  item=next(x for x in records if x["name"]==name)
  item["postSHA256"]=sha(files[name])
 result={"state":"NATIVE_SOURCE_PATCHED_COMPILATION_PENDING","module":module,
         "files":records,"originalMapFilesDeleted":0,
         "sourceFilesBackedUp":len(records),
         "updatedAtUTC":datetime.datetime.now(datetime.timezone.utc).isoformat()}
 report(result)
 return 0
def rollback():
 manifest=OUT/"source-install-result.json"
 if not manifest.is_file():return 0
 data=json.loads(manifest.read_text(encoding="utf-8"))
 if data.get("state")!="NATIVE_SOURCE_PATCHED_COMPILATION_PENDING":return 0
 for record in data["files"]:
  path,backup=pathlib.Path(record["path"]),pathlib.Path(record["backup"])
  if not backup.is_file() or sha(backup)!=record["preSHA256"]:
   raise RuntimeError("Source backup altered; not rolling back")
  if not path.is_file() or sha(path)!=record["postSHA256"]:
   raise RuntimeError("Installed source altered externally; not rolling back")
 for record in data["files"]:
  shutil.copy2(record["backup"],record["path"])
 data["state"]="COMPILATION_FAILED_OR_MAP_NOT_SAVED_SOURCES_RESTORED"
 data["rollbackAtUTC"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 report(data)
 return 0
if __name__=="__main__":
 try:raise SystemExit(rollback() if len(sys.argv)>1 and sys.argv[1]=="rollback" else apply())
 except Exception as exc:
  print("APOCALYPTIC_ADDON_SAFETY_ABORT "+str(exc),flush=True)
  raise
