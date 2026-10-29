"""Create a separate 48km world using verified prepared art and native terrain pads.
No existing map is replaced. This is world assembly, not a playtest or finished-map claim.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import uuid
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE='/Game/Maps/ANOMALIA_Inhabited_v2'
ART='/Game/Anomalia/Inhabited_v2'
OUT=Path(os.environ.get('ANOMALIA_POPULATION_REPORT',str(ROOT/'Saved/Population'/('run-'+uuid.uuid4().hex+'.json'))))
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),mapPackage=PACKAGE,playtested=False,photorealismValidated=False,originalArchipelagoModified=False,roadsBuilt=False,servicesBuilt=False)
try:
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # Never duplicate a World Partition .umap without its external actors or replace an existing world.
    if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE) or (ROOT/'Content/Maps/ANOMALIA_Inhabited_v2.umap').exists():
        raise RuntimeError('Existing populated world preserved; inspect it before authoring a new version')
    spec=importlib.util.spec_from_file_location('population',ROOT/'Scripts/archipelago_population.py')
    population=importlib.util.module_from_spec(spec);spec.loader.exec_module(population)
    manifest=json.loads((ROOT/'SourceAssets/RealismValidation_v2/manifest.json').read_text())
    catalogue={m['id']:m for m in manifest['models']};meshes={}
    for ident in ('detached_house','island_tree_02','grass_medium_01','rock_moss_set_01'):
        model=catalogue[ident];source=(ROOT/'SourceAssets/RealismValidation_v2'/model['file']).resolve()
        if not source.is_relative_to(ROOT/'SourceAssets/RealismValidation_v2') or hashlib.sha256(source.read_bytes()).hexdigest()!=model['sha256']:
            raise RuntimeError('Prepared source integrity failed: '+ident)
        mesh=unreal.load_asset(model['objectPath']+'_r2')
        if not isinstance(mesh,unreal.StaticMesh) or unreal.EditorAssetLibrary.get_metadata_tag(mesh,'AnomaliaRealismSha256')!=model['sha256']:
            raise RuntimeError('Import and verify real art first: '+ident)
        if not mesh.get_editor_property('static_materials') or any(not slot.material_interface for slot in mesh.get_editor_property('static_materials')):
            raise RuntimeError('Missing real-art material: '+ident)
        meshes[ident]=mesh
    cluster_class=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaSceneryCluster')
    water_class=unreal.load_class(None,'/Script/AnomaliaPrimeval.AnomaliaNavigableWater')
    if not cluster_class or not water_class:raise RuntimeError('Compile native world components first')
    sites=[(p.x,p.y) for p in unreal.AnomaliaWorldImportLibrary.inhabited_settlement_sites()]
    bounds=meshes['detached_house'].get_bounds()
    dims=[bounds.box_extent.x*.02,bounds.box_extent.z*.02,bounds.box_extent.y*.02]
    plan=population.build_plan(unreal.AnomaliaWorldImportLibrary.inhabited_archipelago_height,dims,sites=sites)
    plan['mapPackage']=PACKAGE
    if len(plan['buildings'])<100:raise RuntimeError('Population plan unexpectedly incomplete')
    report['planCounts']=dict(settlements=len(plan['settlements']),houses=len(plan['buildings']),foliage=len(plan['foliage']))
    # Source-verified PBR ground textures; world-space UVs prevent per-component stretching.
    registry=json.loads((ROOT.parent/'docs/art/realism-validation-sources.json').read_text())
    ground=next(m for m in registry['models'] if m['id']=='forest_ground_04')
    tools=unreal.AssetToolsHelpers.get_asset_tools();textures={}
    for channel,suffix in [('base','diff_2k.jpg'),('normal','nor_gl_2k.jpg'),('rough','rough_2k.jpg')]:
        entry=next(f for f in ground['files'] if f['path'].endswith(suffix))
        source=ROOT/'Saved/RealismSourceCache'/ground['id']/entry['path']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('Ground texture checksum failed')
        task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=ART+'/Ground';task.automated=True;task.replace_existing=False;task.save=True
        if unreal.EditorAssetLibrary.does_asset_exist(task.destination_path+'/'+source.stem):raise RuntimeError('Existing material namespace preserved')
        tools.import_asset_tasks([task]);objects=task.get_objects()
        texture=next((o for o in objects if isinstance(o,unreal.Texture2D)),None)
        if not texture:raise RuntimeError('Ground texture import failed')
        if channel!='base':texture.set_editor_property('srgb',False)
        if channel=='normal':
            texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property('flip_green_channel',True)
        unreal.EditorAssetLibrary.save_loaded_asset(texture);textures[channel]=texture
    mat=tools.create_asset('M_PBRGround',ART,unreal.Material,unreal.MaterialFactoryNew())
    lib=unreal.MaterialEditingLibrary
    position=lib.create_material_expression(mat,unreal.MaterialExpressionWorldPosition)
    mask=lib.create_material_expression(mat,unreal.MaterialExpressionComponentMask);mask.set_editor_property('r',True);mask.set_editor_property('g',True);mask.set_editor_property('b',False)
    divide=lib.create_material_expression(mat,unreal.MaterialExpressionDivide);divide.set_editor_property('const_b',300)
    lib.connect_material_expressions(position,'',mask,'Input');lib.connect_material_expressions(mask,'',divide,'A')
    for channel,prop in [('base',unreal.MaterialProperty.MP_BASE_COLOR),('normal',unreal.MaterialProperty.MP_NORMAL),('rough',unreal.MaterialProperty.MP_ROUGHNESS)]:
        sample=lib.create_material_expression(mat,unreal.MaterialExpressionTextureSample);sample.set_editor_property('texture',textures[channel])
        if channel=='normal':sample.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif channel=='rough':sample.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        lib.connect_material_expressions(divide,'',sample,'UVs');lib.connect_material_property(sample,'RGB' if channel!='rough' else 'R',prop)
    lib.recompile_material(mat)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mat):raise RuntimeError('Ground material save failed')
    if not level.new_level(PACKAGE,is_partitioned_world=True):raise RuntimeError('New World Partition map creation failed')
    terrain=unreal.AnomaliaWorldImportLibrary.create_inhabited_archipelago_landscape()
    if not terrain:raise RuntimeError('Inhabited landscape creation failed')
    proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    if sum(len(a.get_components_by_class(unreal.LandscapeComponent)) for a in proxies)!=576:raise RuntimeError('Incomplete populated terrain')
    for a in proxies:a.set_editor_property('landscape_material',mat)
    def place(cls,label,e,n,z):
        actor=actors.spawn_actor_from_class(cls,unreal.Vector(e*100,-n*100,z*100))
        if not actor:raise RuntimeError('Actor creation failed: '+label)
        actor.set_actor_label('ANOMALIA_Inhabited1_'+label);actor.tags=[unreal.Name('ANOMALIA_Inhabited_v1')]
        actor.set_editor_property('is_spatially_loaded',True)
        return actor
    for item in plan['buildings']:
        a=place(unreal.StaticMeshActor,item['id'],item['east'],item['north'],item['z'])
        c=a.get_component_by_class(unreal.StaticMeshComponent);c.set_static_mesh(meshes[item['model']]);c.set_collision_profile_name('BlockAll')
        # Prepared house is bottom centred; no scale or tilted floor is used to mask slopes.
        a.set_actor_rotation(unreal.Rotator(yaw=item['yaw']),False)
    clusters={}
    for item in plan['foliage']:
        key=(item['model'],int(item['east']//1000),int(item['north']//1000))
        if key not in clusters:
            a=place(cluster_class,'_'.join(map(str,key)),key[1]*1000+500,key[2]*1000+500,0)
            c=a.get_editor_property('instances');c.set_static_mesh(meshes[item['model']]);clusters[key]=c
        # World-space transforms are converted into the local kilometre cluster by Unreal.
        transform=unreal.Transform(location=unreal.Vector(item['east']*100,-item['north']*100,item['z']*100),rotation=unreal.Rotator(yaw=item['yaw']),scale=unreal.Vector(item['scale'],item['scale'],item['scale']))
        if clusters[key].add_instance(transform,world_space=True)<0:raise RuntimeError('Foliage instance failed')
    sea=place(water_class,'NavigableSea',0,0,-300)
    sea.set_editor_property('surface_offset',30000);sea.get_editor_property('bounds').set_box_extent(unreal.Vector(2400000,2400000,30400),False)
    sea.set_editor_property('is_spatially_loaded',False)
    # Retain the existing ocean rendering if present; require it rather than make a flat primitive ocean.
    # World population does not imply that a realistic ocean renderer is installed.
    sun=place(unreal.DirectionalLight,'Sun',0,0,1000);sun.set_actor_rotation(unreal.Rotator(pitch=-40,yaw=-25),False);sun.set_editor_property('is_spatially_loaded',False)
    for cls,name in [(unreal.SkyLight,'Ambient'),(unreal.SkyAtmosphere,'Sky')]:
        a=place(cls,name,0,0,100);a.set_editor_property('is_spatially_loaded',False)
    first=plan['buildings'][0]
    # Spawn in the reserved 50m lot corridor, on the real native terrain at that point.
    e,n=first['east']+22,first['north']
    surface=population.sampled_surface(unreal.AnomaliaWorldImportLibrary.inhabited_archipelago_height)
    z,error=surface(e,n)
    start=place(unreal.PlayerStart,'PlayerStart',e,n,z+error+1.2)
    # GameMode must find this actor before a player exists to drive spatial streaming.
    start.set_editor_property('is_spatially_loaded',False)
    if not level.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Population or external actor save failed')
    OUT.parent.mkdir(parents=True,exist_ok=True);(OUT.parent/'population-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    report.update(state='POPULATED_WORLD_CREATED_NOT_PLAYTESTED',houses=len(plan['buildings']),foliageInstances=len(plan['foliage']),foliageClusters=len(clusters),terrainComponents=576,rejected=plan['rejected'],oceanRenderingImplemented=False)
except Exception as error:
    report['error']=str(error)
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n');unreal.log('ANOMALIA_POPULATION_REPORT='+str(OUT))
