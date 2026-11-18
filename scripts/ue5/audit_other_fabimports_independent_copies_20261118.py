"""Read-only: find imported uasset/umap copies in FabImports packs
excluding CitySample and VaultCache. No file changes.
"""
import os,pathlib,stat,json,time,hashlib,shutil,datetime
ROOT=pathlib.Path(r"D:\ANOMALIA\FabImports")
GAME=pathlib.Path(r"D:\ANOMALIA\unreal\Content")
OUT=pathlib.Path(os.environ["FABIMPORT_AUDIT_OUT"])
SKIP={"citysample","vaultcache"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
candidates=[]
d={"readOnly":True,"filesDeleted":0,"startUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"totalFilesScanned":0,"totalLogicalBytesScanned":0,"independentSameSizeFiles":0,"independentSameSizeBytes":0,
"hardlinkedGameFiles":0,"hardlinkedGameBytes":0,"byPack":{},"hashSamples":[]}
for base,dirs,names in os.walk(ROOT,followlinks=False):
 parent=pathlib.Path(base)
 relparent=parent.relative_to(ROOT)
 dirs[:]=[n for n in dirs if not (not relparent.parts and n.casefold() in SKIP) and not (getattr((parent/n).lstat(),"st_file_attributes",0)&0x400)]
 for name in names:
  p=parent/name
  try:
   st=p.lstat()
   if not stat.S_ISREG(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:continue
   d["totalFilesScanned"]+=1;d["totalLogicalBytesScanned"]+=st.st_size
   if p.suffix.lower() not in {".uasset",".umap"}:continue
   rel=p.relative_to(ROOT)
   indexes=[i for i,x in enumerate(rel.parts[:-1]) if x.casefold()=="content"]
   if not indexes:continue
   peer=GAME/pathlib.Path(*rel.parts[indexes[-1]+1:])
   try:
    other=peer.lstat()
    if not stat.S_ISREG(other.st_mode) or getattr(other,"st_file_attributes",0)&0x400:continue
   except OSError:continue
   if other.st_size!=st.st_size:continue
   if other.st_dev==st.st_dev and other.st_ino==st.st_ino:
    d["hardlinkedGameFiles"]+=1;d["hardlinkedGameBytes"]+=st.st_size;continue
   if st.st_nlink!=1:continue
   d["independentSameSizeFiles"]+=1;d["independentSameSizeBytes"]+=st.st_size
   pack=rel.parts[0]
   part=d["byPack"].setdefault(pack,{"count":0,"bytes":0})
   part["count"]+=1;part["bytes"]+=st.st_size
   candidates.append((p,peer,st.st_size,rel))
  except OSError:pass
candidates.sort(key=lambda x:x[2],reverse=True)
d["byPack"]=sorted(({"pack":k,**v} for k,v in d["byPack"].items()),key=lambda r:r["bytes"],reverse=True)[:25]
d["largestIndependentMatches"]=[{"relative":str(rel),"bytes":n} for p,peer,n,rel in candidates[:20]]
total=0
for p,peer,n,rel in candidates:
 if total>=1024**3 or len(d["hashSamples"])>=20:break
 try:
  match=sha(p)==sha(peer)
  d["hashSamples"].append({"relative":str(rel),"bytes":n,"sameSha256":match})
  total+=n
 except OSError as exc:d["hashSamples"].append({"relative":str(rel),"error":str(exc)})
d["bytesHashSampled"]=total
d["verifiedIdenticalSampleBytes"]=sum(x["bytes"] for x in d["hashSamples"] if x.get("sameSha256"))
d["endUTC"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
d["freeDBytes"]=shutil.disk_usage("D:/").free
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"fabimports-excluding-vault-citysample-audit.json").write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
print("OTHER_FABIMPORTS_VERIFIED_DUPLICATES_AUDIT "+json.dumps(d,ensure_ascii=False),flush=True)
