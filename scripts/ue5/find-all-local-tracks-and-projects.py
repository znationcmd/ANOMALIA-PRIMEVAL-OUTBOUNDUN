"""Read-only discovery of standalone Unreal/Fab projects on attached Windows disks."""
import os,json,time
from pathlib import Path
out=Path(os.environ["PROJECT_DISCOVERY_OUT"]);out.mkdir(parents=True,exist_ok=True)
deadline=time.monotonic()+1100
skip={"windows","$recycle.bin","system volume information","node_modules",".git","deriveddatacache","intermediate","binaries","saved"}
roots=[Path(f"{c}:/") for c in "CDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{c}:/").exists()]
projects=[];errors=[];seen=set();sketchfab_dirs=[];sketchfab_files=[];track_candidates=[]
def error(e):
    if len(errors)<200: errors.append(str(e))
for root in roots:
    for base,dirs,files in os.walk(root,followlinks=False,onerror=error):
        if time.monotonic()>deadline: break
        tokens=("circuit","motocross","moto-cross","moto_cross","raceway","racetrack","race_track","dirttrack","dirt_track","supercross","speedway","karting","mxtrack","mx_track")
        if any(t in Path(base).name.casefold() for t in tokens):
            track_candidates.append({"directory":str(Path(base))})
        for candidate_name in files:
            if any(t in candidate_name.casefold() for t in tokens):
                track_candidates.append({"file":str(Path(base,candidate_name))})
        if "sketchfab" in Path(base).name.casefold():
            sketchfab_dirs.append({"path":str(Path(base)),"resolved":str(Path(base).resolve())})
        if any("sketchfab" in part.casefold() for part in Path(base).parts):
            for f in files:
                p_raw=Path(base,f)
                if p_raw.suffix.casefold() in {".zip",".7z",".rar",".fbx",".glb",".gltf",".obj",".blend",".uproject"}:
                    try:
                        record={"path":str(p_raw),"bytes":p_raw.stat().st_size}
                        sketchfab_files.append(record)
                    except OSError as e:error(e)
        dirs[:]=[d for d in dirs if d.casefold() not in skip and not Path(base,d).is_symlink() and not getattr(os.path,"isjunction",lambda p: bool(os.lstat(p).st_file_attributes & 0x400))(Path(base,d))]
        for name in files:
            if not name.casefold().endswith(".uproject"):continue
            p=Path(base,name)
            try:
                key=str(p.resolve()).casefold()
                if key in seen:continue
                seen.add(key)
                data=json.loads(p.read_text(encoding="utf-8-sig"))
                entry={"project":str(p),"resolved":str(p.resolve()),"engine":data.get("EngineAssociation"),"modules":data.get("Modules",[]),"plugins":data.get("Plugins",[]),"contentRoots":[]}
                candidates=[p.parent/"Content"]
                plug=p.parent/"Plugins"
                if plug.exists():
                    for pb,pd,pf in os.walk(plug,followlinks=False,onerror=error):
                        pd[:]=[d for d in pd if d.casefold() not in {"binaries","intermediate","saved"}]
                        if "Content" in pd:
                            candidates.append(Path(pb)/"Content");pd.remove("Content")
                for content in candidates:
                    counts={"uasset":0,"umap":0,"fbx":0,"glb":0};matches=[];maps=[]
                    if content.exists():
                        for cb,cd,cf in os.walk(content,followlinks=False,onerror=error):
                            if time.monotonic()>deadline:break
                            for f in cf:
                                fp=Path(cb,f);ext=fp.suffix.lower().lstrip(".")
                                if ext in counts:counts[ext]+=1
                                rel=str(fp.relative_to(content))
                                if ext=="umap" and len(maps)<300:maps.append(rel)
                                if any(t in rel.casefold() for t in ["circuit","motocross","raceway","racetrack","race_track","dirttrack","dirt_track","speedway","supercross","karting"]) and len(matches)<500: matches.append(rel)
                    entry["contentRoots"].append({"path":str(content),"exists":content.exists(),"counts":counts,"maps":maps,"trackCandidates":matches})
                projects.append(entry)
                (out/"standalone-projects.json").write_text(json.dumps({"projects":projects,"errors":errors,"complete":False},indent=2),encoding="utf-8")
                print("PROJECT",str(p),flush=True)
            except Exception as e:error(e)
result={"trackCandidatesAcrossAllDisks":track_candidates,"sketchfabDirectories":sketchfab_dirs,"sketchfabSourceFiles":sketchfab_files,"projects":projects,"errors":errors,"complete":time.monotonic()<=deadline,"readOnly":True,"roots":[str(r) for r in roots],"excludedDirectoryNames":sorted(skip)}
(out/"standalone-projects.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps({"projects":len(projects),"complete":result["complete"]}),flush=True)
