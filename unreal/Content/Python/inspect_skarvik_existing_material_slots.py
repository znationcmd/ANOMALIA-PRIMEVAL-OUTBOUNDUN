"""Read actual material slots on bounded existing CitySample meshes; never save."""
import unreal,os,pathlib,json,hashlib
out=pathlib.Path(os.environ["MISSION_MATERIAL_OUT"])
graph=json.loads((out/"input/skarvik-dependency-transfer-plan.json").read_text(encoding="utf-8"))
stage=pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal")
golden=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample\Content")
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.wait_for_completion()
options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_game_package_references=True,include_editor_only_package_references=True)
report={"state":"READ_ONLY_MATERIAL_SLOT_INSPECTION","graphRun":41838072041,"meshes":[],"savedAssets":0,"errors":[]}
def digest(path):
    if not path.is_file():return None
    h=hashlib.sha256()
    with path.open("rb") as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()
def save():
    (out/"actual-material-slots.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
kits=set();seen=set();save()
for row in graph["files"]:
    if row["status"]!="SOURCE_PACKAGE_FILE_MISSING" or not row["package"].startswith("/Game/Building/"):continue
    missing=row["package"];kit=missing.split("/Material/")[0]
    if kit in kits:continue
    found=0
    for ref in registry.get_referencers(missing,options) or []:
        package=str(ref)
        if package in seen or not package.startswith("/Game/Building/"):continue
        assets=registry.get_assets_by_package_name(package,True) or []
        for data in assets:
            if str(data.asset_class_path.asset_name)!="StaticMesh":continue
            relative=package[len("/Game/"):]
            path=stage/"Content"/(relative+".uasset")
            original=golden/(relative+".uasset")
            before=digest(path)
            mesh=data.get_asset()
            if not isinstance(mesh,unreal.StaticMesh):
                report["errors"].append("Referenced static mesh failed to load: "+package);save();continue
            slots=[]
            for slot in mesh.get_editor_property("static_materials"):
                material=slot.get_editor_property("material_interface")
                name=str(slot.get_editor_property("material_slot_name"))
                imported=str(slot.get_editor_property("imported_material_slot_name"))
                slots.append({"slotName":name,"importedSlotName":imported,"material":material.get_path_name() if material else None})
            entry={"package":package,"missingReference":missing,"slots":slots,"stageSHA256Before":before,"stageSHA256After":digest(path),"existingOriginalSHA256":digest(original),"originalExists":original.is_file()}
            report["meshes"].append(entry);seen.add(package);found+=1;save()
            if entry["stageSHA256Before"]!=entry["stageSHA256After"]:raise RuntimeError("Mesh changed during read-only inspection")
            if found>=2:break
        if found>=2:break
    if found:kits.add(kit)
    if len(kits)>=3 or len(seen)>=6:break
report["sampledKits"]=len(kits);report["nullMaterialSlots"]=sum(slot["material"] is None for m in report["meshes"] for slot in m["slots"])
save()
if not seen:raise RuntimeError("No actual referring StaticMesh package was loaded; no material conclusion is available")
