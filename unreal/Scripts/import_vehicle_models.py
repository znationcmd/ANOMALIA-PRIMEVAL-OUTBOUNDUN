"""Run inside Unreal Editor. Import verified GLB assets; imports are not playtests."""
import hashlib
import json
import os
from pathlib import Path
import uuid
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
BASE=ROOT/'SourceAssets/Vehicles'
OUTPUT=Path(os.environ.get('ANOMALIA_VEHICLE_IMPORT_REPORT',str(ROOT/'Saved/BuildValidation'/('vehicle-import-'+uuid.uuid4().hex+'.json'))))
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),models=[])
try:
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    for item in manifest['models']:
        source=(BASE/item['sourceFile']).resolve();prepared=(BASE/item['preparedFile']).resolve()
        if not source.is_relative_to(BASE) or not prepared.is_relative_to(BASE): raise RuntimeError('Path escapes source directory')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']: raise RuntimeError('Source checksum mismatch')
        if hashlib.sha256(prepared.read_bytes()).hexdigest()!=item['preparedSha256']: raise RuntimeError('Prepared checksum mismatch')
        destination=item['objectPath'].split('.')[0]
        existing=unreal.EditorAssetLibrary.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else None
        if existing:
            if not isinstance(existing,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(existing,'AnomaliaZPrigimaliaVehicleSourceSha256')!=item['sha256']:
                raise RuntimeError('Refusing to overwrite an unowned or different vehicle asset: '+destination)
            mesh=existing
        else:
            staging='/Game/Anomalia/Vehicles/Imports/'+item['vehicleId']+'_'+uuid.uuid4().hex
            task=unreal.AssetImportTask()
            task.filename=str(prepared);task.destination_path=staging
            task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            tools.import_asset_tasks([task])
            task.get_objects() # Wait for Interchange completion before inspecting saved assets.
            meshes=[]
            for path in unreal.EditorAssetLibrary.list_assets(staging,recursive=True,include_folder=False):
                asset=unreal.EditorAssetLibrary.load_asset(path)
                if isinstance(asset,unreal.StaticMesh): meshes.append(asset)
            if len(meshes)!=1: raise RuntimeError('Expected one complete static mesh; found '+str(len(meshes)))
            mesh=unreal.EditorAssetLibrary.duplicate_asset(meshes[0].get_path_name(),destination)
            if not mesh: raise RuntimeError('Could not create canonical vehicle asset')
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaZPrigimaliaVehicleSourceSha256',item['sha256'])
            unreal.EditorAssetLibrary.set_metadata_tag(mesh,'AnomaliaZPrigimaliaAttribution',item['author']+' / '+item['license']+' / '+item['source'])
        materials=mesh.get_editor_property('static_materials')
        if not materials or any(not m.material_interface for m in materials): raise RuntimeError('Missing vehicle materials')
        bounds=mesh.get_bounds()
        dimensions=[bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2]
        if item['vehicleId']=='airliner' and not 3000<=max(dimensions)<=5000:
            raise RuntimeError('Airliner scale invalid (centimetres): '+str(dimensions))
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False): raise RuntimeError('Could not save vehicle asset')
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        vehicle_class=unreal.load_class(None,'/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaVehiclePawn')
        if not vehicle_class: raise RuntimeError('Native vehicle class not loaded')
        probe=actors.spawn_actor_from_class(vehicle_class,unreal.Vector(0,0,500),transient=True)
        if not probe: raise RuntimeError('Could not spawn a transient presentation probe')
        try:
            if not probe.configure_vehicle(unreal.Name(item['vehicleId'])): raise RuntimeError('Native vehicle configuration failed')
            body=probe.get_editor_property('body')
            if body.get_editor_property('static_mesh')!=mesh: raise RuntimeError('Model is not bound to native vehicle Body')
        finally:
            actors.destroy_actor(probe) # Only the probe created above; no level is saved.
        report['models'].append(dict(nativePresentationBound=True,vehicleId=item['vehicleId'],objectPath=mesh.get_path_name(),dimensionsCm=dimensions,materials=len(materials),state='IMPORTED_NOT_PLAYTESTED'))
    report['state']='IMPORTED_NOT_PLAYTESTED'
except Exception as error:
    report['error']=str(error)
    raise
finally:
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    unreal.log('ANOMALIA_VEHICLE_IMPORT_REPORT='+str(OUTPUT))
