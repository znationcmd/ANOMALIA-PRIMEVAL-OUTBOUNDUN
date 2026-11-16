"""ANOMALIA'Z PRIGIMALIA / UE5.8 -- VALHALLA EXTINCTION high-res bridge.

Builds a NEW World Partition map and source target points from the actual
VALHALLA 4033x4033 Drive ZIP (28 settlements / 374 Draugr positions).
No creation on this machine: run in the actual UE5.8 Editor with the Python
Editor Script Plugin, on a BACKED-UP COPY of the project.

Important: this creates a native *empty* World Partition .umap + marker actors,
NOT a Landscape, Viking houses, zombie meshes, AI or a packaged playable game.

The detailed terrain comes from the ZIP's 4033x4033 16-bit heightmap and needs
Landscape > Import from File in that new level. Use X/Y 595.238095 cm,
Z=500 cm, 63 quads/section, 2x2 sections per component, 32x32 components.
The source raster has its first row at SOUTH; confirm / adjust Flip Y in UE.

Use in UE5 Python console (on game project's backup):
  import stage_valhalla_extinction_4033 as v
  kit = r'C:\\VALHALLA\\ANOMALIAZ_VALHALLA_EXTINCTION_24x24_UE58_SOURCE.zip'
  print(v.create_level(kit))  # Dry run
  print(v.create_level(kit, confirm_create=True))
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import zipfile

MAP_NAME='VALHALLA_EXTINCTION'
ASSET='/Game/Maps/VALHALLA_EXTINCTION'
PREFIX='VALHALLA_EXTINCTION_24x24_UE58/'
REQUIRED={
    'VALHALLA_EXTINCTION_MANIFEST.json',
    'Terrain/VALHALLA_EXTINCTION_4033x4033.r16',
    'GameData/valhalla_settlements.json',
    'GameData/valhalla_architecture_placements.json',
    'GameData/valhalla_draugr_spawn_anchors.json',
    'GameData/valhalla_viking_draugr_variants.json',
}
ARCH_TYPES=frozenset(('longhouse','watch_tower','boathouse','smithy',
    'wooden_jetty','palisade_section','feasting_hall','guard_house',
    'fish_smokehouse','turf_house','rune_stone','market_stall','burial_mound',
    'forge','wood_store','shield_rack'))
ZOMBIE_TYPES=frozenset(('draugr_raider','draugr_farmer','draugr_shieldmaiden',
    'draugr_fisher','draugr_berserkr','draugr_guard','draugr_seer','draugr_jarl'))


def check_source(zip_path:str|Path, verify_raw_sha:bool=False)->dict:
    path=Path(zip_path).expanduser().resolve()
    if not path.is_file():raise FileNotFoundError(path)
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        absent=sorted(PREFIX+n for n in REQUIRED if PREFIX+n not in names)
        if absent:raise ValueError('Incomplete Valhalla high-resolution ZIP: '+str(absent))
        man=json.loads(z.read(PREFIX+'VALHALLA_EXTINCTION_MANIFEST.json'))
        if man.get('map')!='VALHALLA EXTINCTION' or man.get('size_km')!=[24,24] or man.get('landscape_resolution')!=[4033,4033]:
            raise ValueError('Wrong map/size/heightmap schema')
        terrain_info=z.getinfo(PREFIX+'Terrain/VALHALLA_EXTINCTION_4033x4033.r16')
        if terrain_info.file_size!=4033*4033*2:raise ValueError('Corrupt 4033 RAW16 byte length')
        sites=json.loads(z.read(PREFIX+'GameData/valhalla_settlements.json'))
        architecture=json.loads(z.read(PREFIX+'GameData/valhalla_architecture_placements.json'))
        zombies=json.loads(z.read(PREFIX+'GameData/valhalla_draugr_spawn_anchors.json'))
        variants=json.loads(z.read(PREFIX+'GameData/valhalla_viking_draugr_variants.json'))
        if len(sites)!=28 or len(architecture)!=555 or len(zombies)!=374:
            raise ValueError('Expected 28 settlements, 555 structures, 374 Draugr markers')
        if set(variants)!=ZOMBIE_TYPES:
            raise ValueError('Missing Viking-clothed Draugr variants')
        if set(x.get('archetype') for x in architecture)!=ARCH_TYPES:
            raise ValueError('Unexpected non-Viking architecture archetypes')
        if not all(p.get('class') in ZOMBIE_TYPES for p in zombies):
            raise ValueError('Unknown or modern zombie class')
        for s in sites:
            if max(abs(float(s['x_m'])),abs(float(s['y_m'])))>12000:raise ValueError('Village outside landscape')
        for zed in zombies:
            if max(abs(float(zed['x_cm'])),abs(float(zed['y_cm'])))>1_200_000:
                raise ValueError('Draugr outside landscape')
        if verify_raw_sha:
            # Streaming verify on demand; avoids unnecessarily reading the whole terrain.
            with z.open(PREFIX+'Terrain/VALHALLA_EXTINCTION_4033x4033.r16') as f:
                h=hashlib.sha256()
                for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
            terrain_sha=h.hexdigest()
        else:terrain_sha=None
    return {'map':MAP_NAME,'dimensionsKm':[24,24], 'terrainResolution':[4033,4033],
        'landscapeScaleCm':[595.238095238,595.238095238,500],
        'settlements':sites,'architecture':architecture,'draugr':zombies,
        'archetypes':variants,'rawSha256':terrain_sha,'nativeMapBuilt':False,
        'nativeLandscapeImported':False,'AIConfigured':False}


def _ue():
    try:import unreal
    except ImportError as e:raise RuntimeError('Only available in actual Unreal Engine 5.8 Python Editor') from e
    return unreal


def _mark(u,actors,label,x,y,z,tag):
    actor=actors.spawn_actor_from_class(u.TargetPoint,u.Vector(x,y,z),u.Rotator())
    if not actor:raise RuntimeError('Could not create '+label)
    actor.set_actor_label(label)
    actor.set_editor_property('tags',[u.Name('AZ_VALHALLA_EXTINCTION'),u.Name(tag)])
    return actor


def create_level(zip_path:str|Path,confirm_create:bool=False,include_draugr_markers:bool=True)->dict:
    """Create new World Partition level and TargetPoints. Refuses to overwrite."""
    kit=check_source(zip_path)
    out={'mapAsset':ASSET,'dimensionsKm':[24,24],'settlements':len(kit['settlements']),
         'draugrMarkers':len(kit['draugr']) if include_draugr_markers else 0,
         'landscapeImported':False,'architectureMeshesPlaced':False,
         'zombieAIWorking':False,'gamePlayable':False}
    if not confirm_create:return {'dryRun':True,**out}
    u=_ue();lv=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if lv.is_in_play_in_editor():raise RuntimeError('Cannot edit during PIE')
    physical=Path(u.Paths.project_content_dir()).resolve()/'Maps'/'VALHALLA_EXTINCTION.umap'
    if physical.exists() or u.EditorAssetLibrary.does_asset_exist(ASSET):
        raise FileExistsError('A Valhalla level exists already; will not overwrite')
    if not lv.new_level(ASSET,is_partitioned_world=True):raise RuntimeError('Cannot create partitioned native level')
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    for s in kit['settlements']:
        _mark(u,actors,'VE_SETTLEMENT_'+s['id'],float(s['x_m'])*100,float(s['y_m'])*100,float(s['z_m'])*100,'VIKING_SETTLEMENT')
    if include_draugr_markers:
        for z in kit['draugr']:
            _mark(u,actors,z['id'],float(z['x_cm']),float(z['y_cm']),float(z['z_cm']),'VIKING_DRAUGR_SPAWN')
    if not lv.save_current_level():raise RuntimeError('Could not save Valhalla level')
    return {'dryRun':False,**out}


def check_asset_bindings(zip_path:str|Path,bindings_path:str|Path)->dict:
    kit=check_source(zip_path)
    paths=json.loads(Path(bindings_path).read_text(encoding='utf-8'))
    needed=sorted(set(x['archetype'] for x in kit['architecture'])|set(x['class'] for x in kit['draugr']))
    missing=[k for k in needed if not isinstance(paths.get(k),str) or not paths[k].startswith('/Game/')]
    return {'required':len(needed),'missing':missing,'bound':{k:paths[k] for k in needed if k not in missing}}


def place_licensed_content(zip_path:str|Path,bindings_path:str|Path,confirm_place:bool=False)->dict:
    """On the actual imported Valhalla level only, spawn user-owned real assets.

    This is NOT a full Viking AI system: pre-existing blueprint must already
    contain a rigged Viking-clothed Draugr, AIController/BehaviorTree/AnimBP.
    """
    kit=check_source(zip_path)
    result=check_asset_bindings(zip_path,bindings_path)
    if result['missing']:return {'dryRun':True,'missingAssetBindings':result['missing']}
    if not confirm_place:return {'dryRun':True,'placementsAvailable':555,'draugrAvailable':374,
                                 'warning':'Requires imported Landscape and tested asset transforms; never a proxy.'}
    u=_ue();lv=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if lv.is_in_play_in_editor():raise RuntimeError('Stop Play In Editor first')
    if not u.EditorAssetLibrary.does_asset_exist(ASSET):raise FileNotFoundError('Valhalla level not created')
    # Validate all resources before even opening the target level.
    loaded={}
    for kind,path in result['bound'].items():
        loaded[kind]=(u.EditorAssetLibrary.load_blueprint_class(path)
                      if kind.startswith('draugr_') else u.EditorAssetLibrary.load_asset(path))
        if not loaded[kind]:raise FileNotFoundError(f'Missing actual UE asset {kind}: {path}')
    if not lv.load_level(ASSET):raise RuntimeError('Failed to switch to isolated Valhalla world')
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    existing_actors=actors.get_all_level_actors()
    if not any(str(a.get_class().get_name()).startswith('Landscape') for a in existing_actors):
        raise RuntimeError('No actual Landscape in VALHALLA_EXTINCTION. Import the 4033x4033 heightmap first.')
    already={a.get_actor_label() for a in existing_actors}
    made=0
    for a in kit['architecture']:
        label='VE_BUILDING_'+a['id']
        if label in already:continue
        rot=u.Rotator(0,float(a.get('yaw_deg',0)),0)
        pos=u.Vector(float(a['x_cm']),float(a['y_cm']),float(a['z_cm']))
        spawned=actors.spawn_actor_from_object(loaded[a['archetype']],pos,rot)
        if not spawned:raise RuntimeError('Failed Viking structure '+label)
        spawned.set_actor_label(label);made+=1;already.add(label)
    zombies=0
    for e in kit['draugr']:
        label='VE_ZOMBIE_'+e['id']
        if label in already:continue
        pos=u.Vector(float(e['x_cm']),float(e['y_cm']),float(e['z_cm']))
        spawned=actors.spawn_actor_from_class(loaded[e['class']],pos,u.Rotator())
        if not spawned:raise RuntimeError('Failed Viking Draugr '+label)
        spawned.set_actor_label(label);zombies+=1;already.add(label)
    if not lv.save_current_level():raise RuntimeError('Native level could not be saved')
    return {'realArchitectureActorsPlaced':made,'preexistingDraugrBlueprintActorsPlaced':zombies,
            'zombieAnimationOrAIValidated':False,'requiresPIEAndPackagedBuildTest':True}

if __name__=='__main__':print('Import from Unreal Python console, run create_level(zip) before confirm_create=True')