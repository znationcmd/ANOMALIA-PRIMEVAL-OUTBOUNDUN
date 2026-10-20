"""Headless Unreal: create ORIGINAL terrain in a separate map, never overwrite a map."""
import json,os,uuid
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
PACKAGE='/Game/Maps/ANOMALIA_Archipelago_v1'
REPORT=Path(os.environ.get('ANOMALIA_WORLD_REPORT',str(ROOT/'Saved/BuildValidation'/('archipelago-'+uuid.uuid4().hex+'.json'))))
result=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),mapPackage=PACKAGE,playtested=False,visualQualityValidated=False)

def material():
    path='/Game/Anomalia/World/Archipelago_v1/M_BiomeBase'
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Refusing to replace an existing material')
    m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_BiomeBase','/Game/Anomalia/World/Archipelago_v1',unreal.Material,unreal.MaterialFactoryNew())
    lib=unreal.MaterialEditingLibrary
    def node(cls,**props):
        n=lib.create_material_expression(m,cls)
        for k,v in props.items(): n.set_editor_property(k,v)
        return n
    def link(a,b,pin):
        if not lib.connect_material_expressions(a,'',b,pin):raise RuntimeError('Material connection failed')
    def color(r,g,b):return node(unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(r,g,b,1))
    pos=node(unreal.MaterialExpressionWorldPosition)
    def ramp(axis,start,width):
        mask=node(unreal.MaterialExpressionComponentMask,r=axis==0,g=axis==1,b=axis==2,a=False);link(pos,mask,'Input')
        sub=node(unreal.MaterialExpressionSubtract,const_b=start);link(mask,sub,'A')
        div=node(unreal.MaterialExpressionDivide,const_b=width);link(sub,div,'A')
        clamp=node(unreal.MaterialExpressionClamp);link(div,clamp,'Input');return clamp
    def mix(a,b,alpha):
        n=node(unreal.MaterialExpressionLinearInterpolate);link(a,n,'A');link(b,n,'B');link(alpha,n,'Alpha');return n
    grass=color(.085,.16,.045);sand=color(.48,.32,.13);rock=color(.19,.19,.17);snow=color(.85,.88,.9)
    dryx=ramp(0,120000,600000);dryy=ramp(1,180000,540000)
    dry=node(unreal.MaterialExpressionMultiply);link(dryx,dry,'A');link(dryy,dry,'B')
    base=mix(grass,sand,dry)
    # Low beaches, then exposed alpine rock and snowy summits.
    base=mix(sand,base,ramp(2,100,1800));base=mix(base,rock,ramp(2,45000,40000));base=mix(base,snow,ramp(2,110000,30000))
    lib.connect_material_property(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=node(unreal.MaterialExpressionConstant,r=.9);lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    lib.recompile_material(m)
    if not unreal.EditorAssetLibrary.save_loaded_asset(m):raise RuntimeError('Material save failed')
    return m

try:
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mapfile=ROOT/'Content/Maps/ANOMALIA_Archipelago_v1.umap'
    # Strictly non-destructive: an existing map is not recreated or saved by this script.
    if mapfile.exists():raise RuntimeError('Map already exists, preserved. Inspect it or choose a new version; no overwrite.')
    if not level.new_level(PACKAGE,is_partitioned_world=True):raise RuntimeError('World Partition map creation failed')
    terrain=unreal.AnomaliaWorldImportLibrary.create_archipelago_landscape()
    if not terrain:raise RuntimeError('Native landscape import failed')
    mat=material()
    proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    count=collision=0
    for a in proxies:
        a.set_editor_property('landscape_material',mat)
        count+=len(a.get_components_by_class(unreal.LandscapeComponent))
        collision+=len(a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent))
    if count!=576 or collision!=576:raise RuntimeError('Incomplete terrain or collision: '+str((count,collision)))
    sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,100000),unreal.Rotator(-45,-25,0));sun.set_actor_label('ANOMALIA_Sun')
    actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,10000))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
    # Choose a dry coastal spawn from native geometry, not a hardcoded sea-floor coordinate.
    spawn=None
    for east in range(-17000,13000,50):
        north=-10000
        height=unreal.AnomaliaWorldImportLibrary.archipelago_height(east,north)
        if 3<height<12:
            spawn=unreal.Vector(east*100,-north*100,height*100+110);break
    if spawn is None:raise RuntimeError('No safe beach spawn found')
    start=actors.spawn_actor_from_class(unreal.PlayerStart,spawn);start.set_actor_label('ANOMALIA_BeachSpawn')
    if not level.save_all_dirty_levels():raise RuntimeError('Map save failed')
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('External actor packages save failed')
    if not mapfile.is_file() or mapfile.stat().st_size<1024:raise RuntimeError('Real .umap not emitted')
    result.update(state='LEVEL_CREATED_NOT_PLAYTESTED',landscapeComponents=count,collisionComponents=collision,landscapeProxies=len(proxies),worldWidthMeters=48000,worldDepthMeters=48000,resolution=3025,vertexSpacingMeters=48000/3024,spawnCm=[spawn.x,spawn.y,spawn.z],worldPartitionRequested=True,streamingPerformanceTested=False)
except Exception as exc:
    result['error']=str(exc)
    raise
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    unreal.log('ANOMALIA_WORLD_REPORT='+str(REPORT))
