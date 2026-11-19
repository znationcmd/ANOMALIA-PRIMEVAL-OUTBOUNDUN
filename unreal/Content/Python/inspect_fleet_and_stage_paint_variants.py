"""Inspect actual fleet; create separate paint variants only for explicit paint materials."""
import unreal,os,pathlib,json,re,collections,gc,time,shutil,hashlib
expected=pathlib.Path(r"D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject").resolve()
assert pathlib.Path(unreal.Paths.get_project_file_path()).resolve()==expected
out=pathlib.Path(os.environ["VEHICLE_REPAIR_OUT"]);out.mkdir(parents=True,exist_ok=True)
run=os.environ["GITHUB_RUN_ID"];dest="/Game/Anomalia/VehicleRepairs/B_"+run
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True);registry.wait_for_completion()
assets=registry.get_assets_by_path("/Game",True,True) or []
name_re=re.compile(r"bmw|e39|sedan|truck|motorcycle|motobike|snowmobile|scooter|formula|(?:^|[_/])f1(?:[_/]|$)|alfa.?romeo|renault.?r30|scania|iveco|daf.?cf|polaris|vehicle|vehvar|carpaint|car_body",re.I)
excluded=re.compile(r"weapon|rifle|backpack|vest|plate.?carrier|circuitboard",re.I)
palette={"Black":(.012,.012,.015,1),"Grey":(.23,.25,.27,1),"DarkGrey":(.055,.065,.075,1),"ForestGreen":(.025,.075,.035,1),"MidnightBlue":(.012,.025,.08,1),"White":(.8,.8,.8,1),"Red":(.45,.015,.01,1)}
report={"project":str(expected),"state":"IN_PROGRESS","vehicles":[],"paintVariants":[],"errors":[],"originalAssetsSaved":0,"mapsSaved":0,"drivingTestsPerformed":0,"palette":palette}
paint_done=set();started=time.monotonic()
tools=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.EditorAssetLibrary;matlib=unreal.MaterialEditingLibrary
def prop(obj,name,default=None):
 try:return obj.get_editor_property(name)
 except Exception:return default
def path(obj):return obj.get_path_name() if obj else None
def write():
 (out/"vehicle-repair-report.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
def inspect_material(material,slot_name):
 if not material:return {"slot":slot_name,"missing":True}
 result={"slot":slot_name,"material":path(material)}
 try:params=[str(n) for n in matlib.get_vector_parameter_names(material)]
 except Exception as e:result["parameterInspectionError"]=str(e);return result
 result["vectorParameters"]=params
 # Never tint windows, tyres, lights, decals or a combined atlas.
 label=(slot_name+" "+material.get_name()).lower()
 if any(t in label for t in ["glass","tire","tyre","rubber","lamp","light","decal","atlas","interior"]):return result
 if not any(t in label for t in ["carpaint","car_paint","bodypaint","body_paint","carrosserie","paint"]):return result
 candidates=[p for p in params if p.lower().replace("_","").replace(" ","") in {"paintcolor","bodycolor","carcolor","basecolor","colour","color","tint","paintcolour","bodycolour"}]
 if len(candidates)!=1:result["paintBlocked"]="No unique explicit paint color parameter";return result
 parameter=candidates[0];key=path(material)
 if key in paint_done:return result
 paint_done.add(key)
 if shutil.disk_usage(expected.parent).free<1024**3:
  result["paintBlocked"]="Disk reserve";return result
 group=hashlib.sha256(key.encode()).hexdigest()[:14]
 for color,rgba in palette.items():
  package=dest+"/"+group+"/MI_"+color
  if lib.does_asset_exist(package):continue
  mi=tools.create_asset("MI_"+color,dest+"/"+group,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
  if not mi:raise RuntimeError("Cannot create isolated paint material")
  matlib.set_material_instance_parent(mi,material)
  value=unreal.LinearColor(*rgba)
  if not matlib.set_material_instance_vector_parameter_value(mi,parameter,value):raise RuntimeError("Paint parameter rejected")
  matlib.update_material_instance(mi)
  if not lib.save_loaded_asset(mi,only_if_is_dirty=False):raise RuntimeError("Paint variant save failed")
  actual=matlib.get_material_instance_vector_parameter_value(mi,parameter)
  if max(abs(getattr(actual,k)-rgba[i]) for i,k in enumerate(["r","g","b","a"]))>.0001:raise RuntimeError("Paint value verification failed")
  report["paintVariants"].append({"sourceMaterial":key,"parameter":parameter,"color":color,"asset":path(mi),"state":"SAVED_PARAMETER_VERIFIED_VISUAL_TEST_REQUIRED","appliedToVehicle":False})
 return result
for data in assets:
 kind=str(data.asset_class_path.asset_name);package=str(data.package_name)
 if kind not in {"StaticMesh","SkeletalMesh","Blueprint"}:continue
 parent=str(data.get_tag_value("NativeParentClass") or "")
 if not (name_re.search(package) or "WheeledVehicle" in parent or "ChaosRoadVehicle" in parent):continue
 if excluded.search(package):continue
 if time.monotonic()-started>1450:
  report["timeLimitReached"]=True;break
 row={"package":package,"class":kind,"drivingAccepted":False,"issues":[]};report["vehicles"].append(row)
 try:
  obj=lib.load_asset(package)
  if not obj:raise RuntimeError("Asset cannot load in actual D project")
  if kind in {"StaticMesh","SkeletalMesh"}:
   mats=prop(obj,"static_materials",[]) if kind=="StaticMesh" else prop(obj,"materials",[])
   row["materials"]=[]
   for entry in mats:
    slot=str(prop(entry,"material_slot_name",""))
    row["materials"].append(inspect_material(prop(entry,"material_interface"),slot))
   if not mats or any(m.get("missing") for m in row["materials"]):row["issues"].append("MISSING_MATERIAL")
   if kind=="StaticMesh":
    bounds=obj.get_bounds();row["dimensionsCm"]=[2*getattr(bounds.box_extent,k) for k in ["x","y","z"]]
    setup=prop(obj,"body_setup");agg=prop(setup,"agg_geom") if setup else None
    row["collisionShapeCounts"]={n:len(prop(agg,n,[]) or []) for n in ["box_elems","sphere_elems","sphyl_elems","convex_elems"]} if agg else {}
    if not any(row["collisionShapeCounts"].values()):row["issues"].append("NO_SIMPLE_COLLISION_REQUIRES_CHASSIS_INSPECTION")
    row["issues"].append("STATIC_ART_REQUIRES_VERIFIED_WHEEL_RIG_OR_AUTHORED_MODULAR_CHASSIS")
   else:
    row["skeleton"]=path(prop(obj,"skeleton"));row["physicsAsset"]=path(prop(obj,"physics_asset"))
    if not row["skeleton"]:row["issues"].append("MISSING_SKELETON")
    if not row["physicsAsset"]:row["issues"].append("MISSING_PHYSICS_ASSET")
  else:
   cls=lib.load_blueprint_class(package)
   if not cls:raise RuntimeError("Blueprint generated class cannot load")
   cdo=unreal.get_default_object(cls);row["nativeParent"]=parent
   row["wheelBones"]=[str(x) for x in prop(cdo,"wheel_bones",[]) or []]
   row["roadMesh"]=path(prop(cdo,"road_mesh"));row["roadBodyMesh"]=path(prop(cdo,"road_body_mesh"))
   row["roadAnimation"]=path(prop(cdo,"road_animation"))
   for name in ["has_valid_road_rig","is_chaos_drive_ready"]:
    if hasattr(cdo,name):
     try:row[name]=bool(getattr(cdo,name)())
     except Exception as e:row[name+"_error"]=str(e)
   row["issues"].append("PIE_ACCELERATION_BRAKING_STEERING_AND_COLORS_REQUIRED")
 except Exception as e:row["issues"].append("INSPECTION_FAILED");row["error"]=str(e);report["errors"].append({"package":package,"error":str(e)})
 if len(report["vehicles"])%20==0:
  write();print(json.dumps({"inspected":len(report["vehicles"]),"paintVariants":len(report["paintVariants"]),"errors":len(report["errors"])}),flush=True)
  obj=None;gc.collect();unreal.collect_garbage()
report["state"]="FLEET_INSPECTED_PAINT_VARIANTS_STAGED_NOT_DRIVING_ACCEPTED";report["elapsedSeconds"]=time.monotonic()-started
write();print(json.dumps({"state":report["state"],"inspected":len(report["vehicles"]),"paintVariants":len(report["paintVariants"]),"errors":len(report["errors"])}),flush=True)
