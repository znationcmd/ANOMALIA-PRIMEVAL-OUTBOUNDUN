"""Read-only NTFS hardlink/deletable-space assessment for City Sample and VaultCache.

Checks physical file identity; does not remove, change, hash, or download files.
"""
import os,pathlib,stat,json,shutil,time,datetime,collections
SRC=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample")
GAME=pathlib.Path(r"D:\ANOMALIA\unreal")
VAULT=pathlib.Path(r"D:\ANOMALIA\FabImports\VaultCache")
RECOVERY=pathlib.Path(r"D:\ANOMALIA\StorageRecovery\CitySampleUniqueCacheFiles")
OUT=pathlib.Path(os.environ["HARDLINK_AUDIT_OUT"])
def snap(p):
 s=p.stat()
 return s.st_dev,s.st_ino,s.st_size,s.st_nlink
def iterfiles(root):
 for base,dirs,names in os.walk(root,followlinks=False):
  path=pathlib.Path(base)
  dirs[:]=[d for d in dirs if not (getattr((path/d).lstat(),"st_file_attributes",0)&0x400)]
  for name in names:
   p=path/name
   try:
    st=p.lstat()
    if not stat.S_ISREG(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:continue
    yield p,st
   except OSError:pass
def audit_source():
 r={"files":0,"bytesLogical":0,"hardlinkedCount":0,"hardlinkedLogicalBytes":0,
   "exactPeerInGameFiles":0,"exactPeerInGameLogicalBytes":0,
   "independentCount":0,"independentBytes":0,"notFoundInGame":0,
   "existsButIndependentFiles":0,"examples":[]}
 for p,s in iterfiles(SRC):
  r["files"]+=1;r["bytesLogical"]+=s.st_size
  if s.st_nlink>1:r["hardlinkedCount"]+=1;r["hardlinkedLogicalBytes"]+=s.st_size
  rel=p.relative_to(SRC)
  peer=GAME/rel if rel.parts[0].lower() in ("content","plugins","source") else None
  same=False
  if peer:
   try:
    st=peer.stat()
    same=(st.st_dev==s.st_dev and st.st_ino==s.st_ino)
   except OSError:pass
  if same:
   r["exactPeerInGameFiles"]+=1;r["exactPeerInGameLogicalBytes"]+=s.st_size
   if len(r["examples"])<4:r["examples"].append({"relative":str(rel),"bytes":s.st_size,"links":s.st_nlink,"peer":str(peer)})
  elif s.st_nlink==1:
   r["independentCount"]+=1;r["independentBytes"]+=s.st_size
  if not same and peer and peer.exists():r["existsButIndependentFiles"]+=1
  elif not same:r["notFoundInGame"]+=1
 return r
def audit_vault():
 r={"files":0,"logicalBytes":0,"hardlinkedFiles":0,"hardlinkedBytes":0,
 "independentFiles":0,"independentBytes":0,"byTopSubfolder":{},"byExtension":{},"largest":[],"examples":[]}
 for p,s in iterfiles(VAULT):
  r["files"]+=1;r["logicalBytes"]+=s.st_size
  if s.st_nlink>1:r["hardlinkedFiles"]+=1;r["hardlinkedBytes"]+=s.st_size
  else:r["independentFiles"]+=1;r["independentBytes"]+=s.st_size
  rel=p.relative_to(VAULT)
  top=rel.parts[0] if rel.parts else "(root)"
  group=r["byTopSubfolder"].setdefault(top,{"files":0,"bytes":0,"linkedBytes":0})
  group["files"]+=1;group["bytes"]+=s.st_size
  if s.st_nlink>1:group["linkedBytes"]+=s.st_size
  ext=p.suffix.lower() or "(none)"
  e=r["byExtension"].setdefault(ext,{"files":0,"bytes":0})
  e["files"]+=1;e["bytes"]+=s.st_size
  if s.st_size>=250*1024*1024:
   r["largest"].append({"path":str(rel),"bytes":s.st_size,"hardlinkCount":s.st_nlink,"ageDays":round((time.time()-s.st_mtime)/86400,1)})
  if len(r["examples"])<8:r["examples"].append({"relative":str(rel),"bytes":s.st_size,"links":s.st_nlink})
 r["largest"]=sorted(r["largest"],key=lambda x:x["bytes"],reverse=True)[:25]
 r["byExtension"]=sorted(({"extension":k,**v} for k,v in r["byExtension"].items()),key=lambda x:x["bytes"],reverse=True)[:20]
 r["byTopSubfolder"]=sorted(({"name":k,**v} for k,v in r["byTopSubfolder"].items()),key=lambda x:x["bytes"],reverse=True)[:20]
 return r
def audit_recovery():
 r={"files":0,"logicalBytes":0,"hardlinkedFiles":0,"hardlinkedBytes":0,"largest":[]}
 for p,s in iterfiles(RECOVERY):
  r["files"]+=1;r["logicalBytes"]+=s.st_size
  if s.st_nlink>1:r["hardlinkedFiles"]+=1;r["hardlinkedBytes"]+=s.st_size
  if s.st_size>250*1024*1024:r["largest"].append({"rel":str(p.relative_to(RECOVERY)),"bytes":s.st_size,"links":s.st_nlink})
 r["largest"]=sorted(r["largest"],key=lambda x:x["bytes"],reverse=True)[:15]
 return r
started=time.monotonic()
report={"readOnly":True,"deletions":0,"reportedAtUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "freeDBytesBefore":shutil.disk_usage("D:/").free}
for label,root,fn in [("citySample",SRC,audit_source),("vaultCache",VAULT,audit_vault),("citySampleRecovery",RECOVERY,audit_recovery)]:
 if root.is_dir():
  report[label]=fn()
  print("NTFS_HARDLINK_AUDIT_SECTION "+json.dumps({"section":label,"result":report[label]},ensure_ascii=False),flush=True)
 else:report[label]={"missing":True}
report["elapsedSeconds"]=round(time.monotonic()-started,2)
report["freeDBytesAfter"]=shutil.disk_usage("D:/").free
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"citysample-hardlinks-and-vault-audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("NTFS_HARDLINK_AUDIT_COMPLETE "+json.dumps({"elapsedSeconds":report["elapsedSeconds"],"freeDBytesAfter":report["freeDBytesAfter"]}),flush=True)
