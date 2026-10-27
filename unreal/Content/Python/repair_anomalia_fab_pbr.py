"""Repair exact known PBR texture sets on newly imported assets only."""
import hashlib,json,os,shutil,traceback
from pathlib import Path
import unreal
root=Path(r"C:\ANOMALIA\FabImports\UserSelection_40561644379")
stage=json.loads((root/"stage-manifest.json").read_text(encoding="utf-8"))
receipt=json.loads((root/"import-report.json").read_text(encoding="utf-8"))
base=receipt["namespace"]
out=Path(os.environ["FAB_PBR_REPORT"])
fixbase=base+"/PBRRepair_"+os.environ["GITHUB_RUN_ID"]
report={"state":"FAILED","namespace":base,"repairs":[],"errors":[],"unresolved":["FPS Guns Rifle 1 material-to-texture mapping not verified","Police Pistol external textures not found"],"originalFabSourcesModified":False}
profiles={
"587e3f02":("ak_Base_color.png","ak_Metallic.png","ak_Roughness.png","ak_Normal_OpenGL.png","ak_Mixed_AO.png"),
"3c61e7dc":("T_DoubleBarrel_C.png","T_DoubleBarrel_M.png","T_DoubleBarrel_R.png","T_DoubleBarrel_N.png","T_DoubleBarrel_AO.png"),
"488b4223":("T_1911_C.png","T_1911_M.png","T_1911_R2.png","T_1911_N.png","T_1911_AO.png"),
"5ba11f83":("T_Shotgun_02_C.png","T_Shotgun_02_M.png","T_Shotgun_02_R.png","T_Shotgun_02_N.png","T_Shotgun_02_AO.png"),
"85d28dd1":("T_Shotgun_02_C.png","T_Shotgun_02_M.png","T_Shotgun_02_R.png","T_Shotgun_02_N.png","T_Shotgun_02_AO.png"),
"8c23e20f":("T_M14_C.png","T_M14_M.png","T_M14_R.png","T_M14_N.png","T_M14_AO.png"),
"ad1be7d2":("T_DoubleBarrel_C.png","T_DoubleBarrel_M.png","T_DoubleBarrel_R.png","T_DoubleBarrel_N.png","T_DoubleBarrel_AO.png")}
try:
    if unreal.EditorAssetLibrary.does_directory_exist(fixbase):raise RuntimeError("Repair namespace exists")
    backup=root/"Backups"/("pbr-"+os.environ["GITHUB_RUN_ID"]);backup.mkdir(parents=True,exist_ok=False)
    jobs=[]
    for short,names in profiles.items():
        pack=next(p for p in stage["sourcePacks"] if p["id"].startswith(short))
        sources=[]
        for name in names:
            matches=[p for p in pack["files"] if Path(p["relative"].replace("\\","/")).name==name]
            if len(matches)!=1:raise RuntimeError("Texture identity ambiguous or absent: "+short+" "+name)
            row=matches[0];p=Path(pack["staged"])/row["relative"]
            if hashlib.sha256(p.read_bytes()).hexdigest()!=row["sha256"]:raise RuntimeError("Texture source changed "+str(p))
            sources.append(p)
        meshes=[unreal.load_asset(a["path"]) for r in receipt["sources"] if r["id"].startswith(short) for a in r["assets"] if a["class"]=="StaticMesh"]
        for mesh in meshes:
            if not mesh or not mesh.get_path_name().startswith(base+"/"):raise RuntimeError("Mesh outside owned namespace")
            package=mesh.get_path_name().split(".")[0]
            disk=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))/package.removeprefix("/Game/")
            for ext in (".uasset",".uexp",".ubulk"):
                p=Path(str(disk)+ext)
                if p.exists():
                    dst=backup/p.relative_to(Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())))
                    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
                    if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(dst.read_bytes()).digest():raise RuntimeError("Backup mismatch")
        jobs.append((short,sources,meshes))
    props=(unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialProperty.MP_METALLIC,unreal.MaterialProperty.MP_ROUGHNESS,unreal.MaterialProperty.MP_NORMAL,unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    for short,sources,meshes in jobs:
        folder=fixbase+"/"+short
        mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_PBR_"+short,folder,unreal.Material,unreal.MaterialFactoryNew())
        if not mat:raise RuntimeError("Material creation failed")
        row={"id":short,"material":mat.get_path_name(),"textures":[],"meshes":[],"backup":str(backup)}
        report["repairs"].append(row)
        for i,p in enumerate(sources):
            t=unreal.AssetImportTask()
            for k,v in {"filename":str(p),"destination_path":folder+"/Textures","automated":True,"replace_existing":False,"save":False}.items():t.set_editor_property(k,v)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
            ts=[o for o in t.get_objects() if isinstance(o,unreal.Texture2D)]
            if len(ts)!=1:raise RuntimeError("Expected one imported texture "+str(p))
            tex=ts[0];tex.set_editor_property("srgb",i==0)
            if i==3:
                tex.set_editor_property("compression_settings",unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("flip_green_channel","OpenGL" in p.name)
            elif i!=0:tex.set_editor_property("compression_settings",unreal.TextureCompressionSettings.TC_MASKS)
            node=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,i*220)
            node.set_editor_property("texture",tex)
            node.set_editor_property("sampler_type",unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if i==3 else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if i==0 else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            if not unreal.MaterialEditingLibrary.connect_material_property(node,"RGB" if i in (0,3) else "R",props[i]):raise RuntimeError("Texture graph connection failed")
            if not unreal.EditorAssetLibrary.save_loaded_asset(tex,only_if_is_dirty=False):raise RuntimeError("Texture save failed")
            row["textures"].append({"source":p.name,"asset":tex.get_path_name(),"normalGreenFlipped":i==3 and "OpenGL" in p.name})
        unreal.MaterialEditingLibrary.recompile_material(mat)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False):raise RuntimeError("Material save failed")
        for mesh in meshes:
            old=[m.material_interface.get_path_name() if m.material_interface else None for m in mesh.get_editor_property("static_materials")]
            for i in range(len(old)):mesh.set_material(i,mat)
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False):raise RuntimeError("Mesh save failed")
            row["meshes"].append({"path":mesh.get_path_name(),"oldMaterials":old,"newMaterial":mat.get_path_name()})
        out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    report["state"]="EXACT_TEXTURE_SETS_CONNECTED_NEEDS_GPU_REVIEW"
except Exception as e:
    report["errors"].append(str(e));unreal.log_error(traceback.format_exc())
out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
