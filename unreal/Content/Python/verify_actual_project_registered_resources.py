"""Verify registered resource classes and source hashes in the actual existing D project."""
import unreal,os,pathlib,json,collections,re,time
project=pathlib.Path(unreal.Paths.get_project_file_path()).resolve()
expected=pathlib.Path(r"D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject").resolve()
assert project==expected,"Refusing a validation copy instead of the real D project"
out=pathlib.Path(os.environ["MISSION_REGISTERED_OUT"])
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True);registry.wait_for_completion()
assets=registry.get_assets_by_path("/Game",True,True) or []
classes=collections.Counter();animations=[];vehicles=[];source_index=[];missing_skeletons=[]
animation_types={"AnimSequence","AnimMontage","AnimComposite","BlendSpace","BlendSpace1D","AimOffsetBlendSpace","AimOffsetBlendSpace1D","AnimBlueprint","PoseAsset","IKRigDefinition","IKRetargeter","ControlRigBlueprint"}
vehicle_name=re.compile(r"(?:^|[_/])(?:bmw|e39|vehicle[0-9]*|sedan|truck|moto|motorcycle|snowmobile|scooter|formula|f1|quad|hovercraft|car[0-9]*|boat|plane|train|ship|bus|suv|b777)(?:[_/]|$)",re.I)
def tags(data,names):
    return {name:value for name in names if (value:=data.get_tag_value(name))}
def package_from_export(value):
    found=re.search(r"(/Game/[^']+)",value or "")
    return found.group(1).split(".")[0] if found else None
for data in assets:
    kind=str(data.asset_class_path.asset_name);classes[kind]+=1
    package=str(data.package_name);name=str(data.asset_name)
    if kind in animation_types:
        row={"package":package,"name":name,"class":kind,"tags":tags(data,["Skeleton","TargetSkeleton","ParentClass","NativeParentClass"])}
        skeleton=package_from_export(row["tags"].get("Skeleton") or row["tags"].get("TargetSkeleton"))
        if skeleton:
            row["skeletonPackageRegistered"]=bool(registry.get_assets_by_package_name(skeleton,True))
            if not row["skeletonPackageRegistered"]:missing_skeletons.append({"animation":package,"skeleton":skeleton})
        animations.append(row)
    if kind in {"StaticMesh","SkeletalMesh","Blueprint","AnimBlueprint"}:
        parent=tags(data,["ParentClass","NativeParentClass"])
        native_vehicle=any("WheeledVehicle" in value or "ChaosVehicle" in value for value in parent.values())
        if native_vehicle or vehicle_name.search(package):
            vehicles.append({"package":package,"name":name,"class":kind,"parentTags":parent,"nativeVehicleParentCandidate":native_vehicle,"drivingTested":False})
    if kind in {"StaticMesh","SkeletalMesh","AnimSequence","AnimMontage","Skeleton"}:
        imported=tags(data,["SourceFile","Skeleton","TargetSkeleton"])
        if imported:source_index.append({"package":package,"class":kind,"tags":imported})
report={"state":"REGISTERED_RESOURCES_READ_IN_ACTUAL_D_PROJECT","project":str(project),"assetCount":len(assets),"assetClasses":dict(classes),"animationAssetCount":len(animations),"vehicleCandidateCount":len(vehicles),"missingRegisteredSkeletons":missing_skeletons,"packagesSaved":0,"objectsLoadedForGameplay":0,"runtimeOrDrivingAcceptance":False,"animationRetargetingAccepted":False}
(out/"registered-resource-summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
for name,rows in [("registered-animations.jsonl",animations),("registered-vehicle-candidates.jsonl",vehicles),("registered-source-import-data.jsonl",source_index)]:
    with (out/name).open("w",encoding="utf-8") as stream:
        for row in rows:stream.write(json.dumps(row,separators=(",",":"))+"\n")
print(json.dumps(report,indent=2))
