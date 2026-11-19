"""Bind three audited CitySample meshes to their exact named existing kit materials."""
import os,json,pathlib,hashlib,shutil,unreal
stage=pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal")
golden=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample\Content")
out=pathlib.Path(os.environ["MISSION_MATERIAL_OUT"])
audit=json.loads((out/"input/actual-material-slots.json").read_text(encoding="utf-8"))
assert len(audit["meshes"])==3 and audit["nullMaterialSlots"]==3
assert (stage/".skarvik-ci-stage-marker").read_text().strip()=="41188816555"
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_game_package_references=True,include_editor_only_package_references=True)
report={"state":"PREPARING_EXACT_NAMED_KIT_MATERIALS","priorInspectionRun":41839300043,"addedPackages":[],"modifiedMeshes":[],"backups":[],"unresolved":[],"bytesCopied":0,"mapsSaved":0,"mainDProjectModified":False,"missingInstanceParametersRecovered":False}
def save():
    (out/"three-mesh-material-repair.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
def sha(path):
    if not path.is_file():return None
    h=hashlib.sha256()
    with path.open("rb") as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()
def snapshot(mesh):
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    lods=mesh.get_num_lods()
    box=mesh.get_bounding_box()
    bounds={"min":[box.min.x,box.min.y,box.min.z],"max":[box.max.x,box.max.y,box.max.z]}
    return {"lods":lods,"triangles":[mesh.get_num_triangles(i) for i in range(lods)],"vertices":[mesh.get_num_vertices(i) for i in range(lods)],"bounds":bounds,"slotNames":[str(s.get_editor_property("material_slot_name")) for s in mesh.get_editor_property("static_materials")]}
def ensure_package(package):
    relative=package[len("/Game/"):]
    target=stage/"Content"/(relative+".uasset")
    if target.is_file():return target
    source=golden/(relative+".uasset")
    if not source.is_file():
        report["unresolved"].append(package);save();return None
    for ext in [".uasset",".uexp",".ubulk",".uptnl"]:
        src=source.with_suffix(ext);dst=target.with_suffix(ext)
        if not src.is_file():continue
        if dst.exists():raise RuntimeError("Existing target sidecar must be preserved: "+str(dst))
        count=src.stat().st_size
        if report["bytesCopied"]+count>1024**3 or shutil.disk_usage(stage).free<count+4*1024**3:
            raise RuntimeError("Bounded resource restoration exceeds disk reserve")
        before=sha(src);dst.parent.mkdir(parents=True,exist_ok=True)
        with src.open("rb") as inp,dst.open("xb") as dest:shutil.copyfileobj(inp,dest)
        assert sha(dst)==before and sha(src)==before
        report["addedPackages"].append({"source":str(src),"target":str(dst),"sha256":before,"bytes":count})
        report["bytesCopied"]+=count;save()
    registry.scan_files_synchronous([str(target)],True)
    return target
save()
plans=[];roots=[]
for audited in audit["meshes"]:
    package=audited["package"];relative=package[len("/Game/"):]
    path=stage/"Content"/(relative+".uasset")
    assert sha(path)==audited["stageSHA256After"],"Mesh differs from the inspected original; preserve it"
    assert sha(golden/(relative+".uasset"))==audited["existingOriginalSHA256"]
    kit=package.split("/Mesh/")[0]
    slots=audited["slots"]
    assert all(s["material"] is None and s["slotName"]==s["importedSlotName"] for s in slots)
    materials=[]
    for slot in slots:
        name=slot["slotName"]
        assert name.startswith("Bldg_") and "/" not in name
        material=kit+"/Material/M_"+name
        assert (golden/(material[len("/Game/"):]+".uasset")).is_file(),"Exact original kit material is absent"
        materials.append(material);roots.append(material)
    plans.append((audited,materials))
pending=list(roots);seen=set()
while pending:
    if len(seen)>=2000:raise RuntimeError("Bounded material dependency budget reached")
    package=pending.pop()
    if package in seen:continue
    seen.add(package)
    if ensure_package(package) is None:continue
    for dependency in registry.get_dependencies(package,options) or []:
        dependency=str(dependency)
        if dependency.startswith("/Game/") and dependency not in seen:pending.append(dependency)
report["materialDependencyPackages"]=len(seen);save()
assert not report["unresolved"],"Existing original material dependencies remain absent; no mesh was modified"
prepared=[]
for audited,material_paths in plans:
    mesh=unreal.load_asset(audited["package"])
    assert isinstance(mesh,unreal.StaticMesh)
    slots=list(mesh.get_editor_property("static_materials"))
    assert len(slots)==len(material_paths) and all(s.get_editor_property("material_interface") is None for s in slots)
    materials=[unreal.load_asset(p) for p in material_paths]
    assert all(isinstance(m,unreal.MaterialInterface) for m in materials),"Original kit material failed to load"
    prepared.append((audited,mesh,slots,materials,snapshot(mesh)))
backup_root=stage/"Saved/MissionMaterialBackups"/os.environ["GITHUB_RUN_ID"]
for audited,mesh,slots,materials,geometry in prepared:
    relative=audited["package"][len("/Game/"):]
    path=stage/"Content"/(relative+".uasset")
    assert sha(path)==audited["stageSHA256After"]
    for ext in [".uasset",".uexp",".ubulk",".uptnl"]:
        original=path.with_suffix(ext)
        if not original.is_file():continue
        backup=backup_root/(relative+ext);backup.parent.mkdir(parents=True,exist_ok=True)
        with original.open("rb") as inp,backup.open("xb") as dest:shutil.copyfileobj(inp,dest)
        assert sha(original)==sha(backup)
        report["backups"].append({"original":str(original),"backup":str(backup),"sha256":sha(backup)})
save()
for audited,mesh,slots,materials,geometry in prepared:
    for slot,material in zip(slots,materials):slot.set_editor_property("material_interface",material)
    mesh.set_editor_property("static_materials",slots)
    after=snapshot(mesh)
    report["lastGeometryComparison"]={"package":audited["package"],"before":geometry,"after":after};save()
    assert after==geometry,"Material assignment changed geometry or slot names"
    assert unreal.EditorAssetLibrary.save_asset(audited["package"],only_if_is_dirty=False)
    relative=audited["package"][len("/Game/"):]
    assert sha(golden/(relative+".uasset"))==audited["existingOriginalSHA256"],"Source CitySample original changed"
    report["modifiedMeshes"].append({"package":audited["package"],"sha256Before":audited["stageSHA256After"],"sha256After":sha(stage/"Content"/(relative+".uasset")),"materials":[m.get_path_name() for m in materials],"geometryBefore":geometry,"geometryAfter":snapshot(mesh)})
    save()
report["state"]="THREE_EXISTING_MESH_MATERIAL_BINDINGS_SAVED_REOPEN_AND_RENDER_REQUIRED"
save()
