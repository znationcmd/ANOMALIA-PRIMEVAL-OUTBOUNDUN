"""Read-only VaultCache to native-game match audit for safe reclaim planning.
Hash-checks selected top peers; deletes nothing, changes nothing.
"""
import os,pathlib,stat,hashlib,json,shutil,datetime,time,collections
ROOT=pathlib.Path(r"D:\ANOMALIA\FabImports\VaultCache")
GAME=pathlib.Path(r"D:\ANOMALIA\unreal\Content")
OUT=pathlib.Path(os.environ["VAULT_MATCH_AUDIT_OUT"])
def filehash(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def nonreparse(p):
 try:return not (getattr(p.lstat(),"st_file_attributes",0)&0x400)
 except OSError:return False
summary={"readOnly":True,"filesDeleted":0,"logicalSourceFiles":0,"logicalSourceBytes":0,
"matchPathFiles":0,"matchPathBytes":0,"sameSizePeerFiles":0,"sameSizePeerBytes":0,
"distinctSameSizeFiles":0,"distinctSameSizeBytes":0,"hardlinkedSameSizeFiles":0,
"sameSizeByPack":{},"hashProbes":[],"noPeerLargeSamples":[],"beginUTC":datetime.datetime.now(datetime.timezone.utc).isoformat()}
candidates=[]
for base,dirs,names in os.walk(ROOT,followlinks=False):
 parent=pathlib.Path(base)
 dirs[:]=[d for d in dirs if nonreparse(parent/d)]
 for name in names:
  p=parent/name
  try:
   s=p.lstat()
   if not stat.S_ISREG(s.st_mode) or (getattr(s,"st_file_attributes",0)&0x400):continue
   summary["logicalSourceFiles"]+=1;summary["logicalSourceBytes"]+=s.st_size
   if p.suffix.lower() not in (".uasset",".umap"):continue
   rel=p.relative_to(ROOT)
   parts=rel.parts
   indices=[i for i,x in enumerate(parts[:-1]) if x.casefold()=="content"]
   if not indices:continue
   index=indices[-1]
   suffix=pathlib.Path(*parts[index+1:])
   if not suffix.parts:continue
   peer=GAME/suffix
   try:
    other=peer.lstat()
    if not stat.S_ISREG(other.st_mode) or getattr(other,"st_file_attributes",0)&0x400:continue
   except OSError:
    if len(summary["noPeerLargeSamples"])<10 and s.st_size>50*1024*1024:
     summary["noPeerLargeSamples"].append(str(rel))
    continue
   summary["matchPathFiles"]+=1;summary["matchPathBytes"]+=s.st_size
   if s.st_size!=other.st_size:continue
   summary["sameSizePeerFiles"]+=1;summary["sameSizePeerBytes"]+=s.st_size
   if s.st_ino==other.st_ino and s.st_dev==other.st_dev:
    summary["hardlinkedSameSizeFiles"]+=1
    continue
   if s.st_nlink!=1:continue
   summary["distinctSameSizeFiles"]+=1;summary["distinctSameSizeBytes"]+=s.st_size
   pack=rel.parts[0]
   g=summary["sameSizeByPack"].setdefault(pack,{"files":0,"bytes":0})
   g["files"]+=1;g["bytes"]+=s.st_size
   candidates.append((p,peer,s.st_size,rel))
  except OSError:continue
candidates.sort(key=lambda x:x[2],reverse=True)
summary["sameSizeByPack"]=sorted(({"pack":k,**v} for k,v in summary["sameSizeByPack"].items()),key=lambda x:x["bytes"],reverse=True)[:35]
summary["largestCandidateSamples"]=[{"path":str(rel),"peer":str(peer),"bytes":size} for p,peer,size,rel in candidates[:35]]
hashed_bytes=0
for p,peer,size,rel in candidates:
 if hashed_bytes>=2*1024**3 or len(summary["hashProbes"])>=30:break
 try:
  d1=filehash(p);d2=filehash(peer)
  summary["hashProbes"].append({"vaultRelative":str(rel),"gameRelative":str(peer.relative_to(GAME)),"bytes":size,"sameSHA256":d1==d2,"vaultSha256":d1})
  hashed_bytes+=size
 except OSError as exc:
  summary["hashProbes"].append({"vaultRelative":str(rel),"error":str(exc)})
summary["hashTestedBytes"]=hashed_bytes
summary["hashVerifiedIdenticalBytes"]=sum(x["bytes"] for x in summary["hashProbes"] if x.get("sameSHA256"))
summary["hashVerifiedIdenticalFiles"]=sum(bool(x.get("sameSHA256")) for x in summary["hashProbes"])
summary["freeDBytes"]=shutil.disk_usage("D:/").free
summary["endUTC"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"vaultcache-peer-audit.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
print("VAULTCACHE_PEER_AUDIT "+json.dumps(summary,ensure_ascii=False),flush=True)
