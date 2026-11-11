"""Supplement previous inventories with uncovered game resources on C and D; never import or modify payloads."""
import pathlib,os,json,time,collections,shutil
main=pathlib.Path(r"D:\ANOMALIA\unreal");out=pathlib.Path(os.environ["ALL_RESOURCE_OUT"]);out.mkdir(parents=True,exist_ok=True)
prior=json.loads((out/"prior"/"bulk-import-summary.json").read_text(encoding="utf-8-sig"))
covered={str(pathlib.Path(s["content"]).resolve()).casefold() for s in prior["sourceProjects"]}
covered.add(str((main/"Content").resolve()).casefold())
persistent=main/"Saved"/"ResourceDiscovery"/"C_D_all_categories_v1";persistent.mkdir(parents=True,exist_ok=True)
state_file=persistent/"state.json"
if state_file.exists():state=json.loads(state_file.read_text(encoding="utf-8"))
else:state={"pending":["D:/","C:/"],"directories":0,"counts":{},"files":0,"skippedKnownContentRoots":[],"errors":[]}
pending=collections.deque(state["pending"]);counts=collections.Counter(state["counts"]);deadline=time.monotonic()+2400
manifest=persistent/"new-source-files.jsonl"
always={".uproject",".uplugin",".uasset",".umap",".uexp",".ubulk",".uptnl",".fbx",".glb",".gltf",".obj",".blend",".abc",".usd",".usdz",".usdc",".usda",".zip",".7z",".rar",".sbsar"}
contextual={".png",".jpg",".jpeg",".tga",".bmp",".tif",".tiff",".dds",".exr",".hdr",".psd",".wav",".ogg",".flac",".mp3",".csv",".json",".bin",".mtl",".txt",".md",".license"}
skip={"windows","$recycle.bin","system volume information",".git","node_modules","deriveddatacache","intermediate","binaries"}
tags={"boats":["boat","ship","yacht","zodiac","riva"],"hovercraft":["hovercraft","aeroglisseur"],"aircraft":["plane","aircraft","airliner","b777","cessna"],"helicopters":["helicopter","chopper","helico","blackhawk"],"armour":["tank","abrams","leopard","t90","t-90","armored","armoured"],"trucks":["truck","scania","iveco","daf","zetros","lorry","camion"],"weapons":["weapon","rifle","pistol","shotgun","ak47","ammo","grenade"],"medical":["medicine","medical","medkit","bandage","pill","syringe","morphine","paracetamol"],"drugs":["cocaine","cannabis","marijuana","heroin","amphetamine","drug"],"clothing":["clothing","jacket","pants","trouser","shirt","boot","helmet","vest","backpack","glove"]}
def save():
 state["pending"]=list(pending);state["counts"]=dict(counts);state["complete"]=not pending
 state_file.write_text(json.dumps(state,indent=2),encoding="utf-8")
 shutil.copyfile(state_file,out/"all-resource-discovery-summary.json")
with manifest.open("a",encoding="utf-8") as stream:
 while pending and time.monotonic()<deadline:
  directory=pathlib.Path(pending.popleft())
  try:
   real=str(directory.resolve()).casefold()
   if real in covered:
    if real not in state["skippedKnownContentRoots"]:state["skippedKnownContentRoots"].append(real)
    continue
   if directory.name.casefold() in skip:continue
   # Runtime/OS installation trees do not contain the user's standalone project library.
   if str(directory).casefold() in {r"c:\program files",r"c:\program files (x86)"}:continue
   try:entries=list(os.scandir(directory))
   except OSError as e:
    if len(state["errors"])<300:state["errors"].append({"path":str(directory),"error":str(e)})
    continue
   context=any(x in real for x in ["sketchfab","fabimports","fablibrary","vaultcache","sourceassets","unreal projects","unrealprojects","\\content"])
   for entry in entries:
    try:
     stat=entry.stat(follow_symlinks=False)
     if stat.st_file_attributes & 0x400:continue
     if entry.is_dir(follow_symlinks=False):pending.append(entry.path);continue
     suffix=pathlib.Path(entry.name).suffix.casefold()
     if suffix not in always and not(context and suffix in contextual):continue
     lower=entry.path.casefold()
     inferred=[key for key,words in tags.items() if any(w in lower for w in words)]
     stream.write(json.dumps({"path":entry.path,"bytes":stat.st_size,"extension":suffix,"mtimeNS":stat.st_mtime_ns,"filenameCategoryHints":inferred,"contentVerified":False},separators=(",",":"))+"\n")
     counts[suffix]+=1;state["files"]+=1
    except OSError as e:
     if len(state["errors"])<300:state["errors"].append({"path":entry.path,"error":str(e)})
   state["directories"]+=1
   if state["directories"]%1000==0:
    stream.flush();save();print(json.dumps({"directories":state["directories"],"newSourceFiles":state["files"],"pendingDirectories":len(pending)}),flush=True)
  except Exception as e:
   if len(state["errors"])<300:state["errors"].append({"path":str(directory),"error":str(e)})
 stream.flush()
save()
shutil.copyfile(manifest,out/"new-source-files.jsonl")
print(json.dumps({"complete":state["complete"],"files":state["files"],"knownPlanContentRoots":len(covered),"remainingDirectories":len(pending),"counts":dict(counts)}),flush=True)
