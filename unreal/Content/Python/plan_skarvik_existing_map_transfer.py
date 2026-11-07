"""Read the existing SKARVIK package graph; never load or save a level."""
import unreal, pathlib, os, json, time, hashlib
stage=pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal")
target=pathlib.Path(r"D:\ANOMALIA\unreal")
out=pathlib.Path(os.environ["MISSION_MAP_OUT"])
report={"state":"STARTED","map":"/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1","assetsCopied":0,"packagesSaved":0,"errors":[]}
def write():
    (out/"skarvik-dependency-transfer-plan.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
write()
map_file=stage/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap"
before=hashlib.sha256(map_file.read_bytes()).hexdigest()
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
options=unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,include_hard_package_references=True,
    include_game_package_references=True,include_editor_only_package_references=True)
roots=[report["map"]]
external_dirs=[]
for kind in ["__ExternalActors__","__ExternalObjects__"]:
    folder=stage/"Content"/kind/"Maps/PRIGIMALIA_SKARVIK_FINAL_v1"
    if folder.is_dir():
        external_dirs.append(str(folder))
        roots.extend("/Game/"+f.relative_to(stage/"Content").with_suffix("").as_posix() for f in folder.rglob("*.uasset"))
report["externalActorDirectories"]=external_dirs
if not registry.get_assets_by_package_name(report["map"],True):
    raise RuntimeError("Existing final SKARVIK package is absent from the on-disk asset registry")
seen=set();pending=list(roots);external=set();native=set();edges=0;started=time.monotonic()
while pending:
    if len(seen)>=20000 or time.monotonic()-started>150:
        report["errors"].append("Dependency traversal budget reached; plan is incomplete")
        break
    package=pending.pop()
    if package in seen:continue
    seen.add(package)
    for dep in registry.get_dependencies(package,options) or []:
        dep=str(dep);edges+=1
        if dep.startswith("/Game/"):
            if dep not in seen:pending.append(dep)
        elif dep.startswith("/Script/"):native.add(dep)
        elif not dep.startswith("/Engine/"):external.add(dep)
rows=[];missing_bytes=0;different_bytes=0
for package in sorted(seen):
    relative=package[len("/Game/"):]
    candidates=[stage/"Content"/(relative+ext) for ext in [".umap",".uasset"]]
    src=next((p for p in candidates if p.is_file()),None)
    if src is None:
        rows.append({"package":package,"status":"SOURCE_PACKAGE_FILE_MISSING"});continue
    for suffix in [src.suffix,".uexp",".ubulk",".uptnl"]:
        source=src.with_suffix(suffix)
        if not source.is_file():continue
        rel=source.relative_to(stage)
        destination=target/rel
        size=source.stat().st_size
        status="MISSING_ON_D" if not destination.is_file() else ("SIZE_DIFFERS_PRESERVE_BOTH" if size!=destination.stat().st_size else "SAME_SIZE_HASH_COMPARISON_REQUIRED")
        if status=="MISSING_ON_D":missing_bytes+=size
        if status=="SIZE_DIFFERS_PRESERVE_BOTH":different_bytes+=size
        rows.append({"package":package,"path":rel.as_posix(),"bytes":size,"status":status})
report.update(state="READ_ONLY_PLAN_COMPLETE" if not pending else "INCOMPLETE_PLAN",
    dependencyPackages=len(seen),edges=edges,externalPluginPackages=sorted(external),nativeScriptPackages=sorted(native),
    missingOnDBytes=missing_bytes,conflictingSourceBytes=different_bytes,
    files=rows,elapsedSeconds=time.monotonic()-started,
    sourceMapSHA256Before=before,sourceMapSHA256After=hashlib.sha256(map_file.read_bytes()).hexdigest(),
    sameSizeIsNotIdentity=True,streamingAndDrivabilityValidated=False)
write()
if before!=report["sourceMapSHA256After"]:raise RuntimeError("Source map changed during read-only inspection")
if report["errors"]:raise RuntimeError("; ".join(report["errors"]))
