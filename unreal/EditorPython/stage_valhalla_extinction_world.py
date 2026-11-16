"""ANOMALIA'Z PRIGIMALIA -- UE 5.8 Editor-only VALHALLA EXTINCTION bridge.

SAFETY:
- On a backed-up COPY of the actual game project only.
- Creates a wholly new World Partition level; refuses to overwrite any map.
- Initial call places Viking settlement/shrine and Draugr target-point markers.
- To populate actual Viking buildings and zombies, import heightmap THEN supply
  valid asset references in valhalla-assets.json, and use place_real_assets().
- NO automatic costume conversion: Draugr BP needs SkeletalMesh, Viking clothes,
  Animation Blueprint, AI Controller, Behavior Tree, damage and navmesh.

Open UE Python console:
  import stage_valhalla_extinction_world as ve
  print(ve.create_level(r'C:\\VALHALLA_EXTINCTION_24x24_SOURCE\\valhalla-layout.json'))
  print(ve.create_level(r'C:\\VALHALLA_EXTINCTION_24x24_SOURCE\\valhalla-layout.json', confirm_create=True))
"""
from __future__ import annotations
import json
import math
from pathlib import Path

LEVEL_PATH = '/Game/Maps/VALHALLA_EXTINCTION_24KM'
LEVEL_FILENAME = 'VALHALLA_EXTINCTION_24KM.umap'
WORLD_ID = 'valhalla-extinction'
MARKER_TAG = 'AZ_VALHALLA_EXTINCTION'


def check_layout(path: str | Path) -> dict:
    layout=json.loads(Path(path).read_text(encoding='utf-8'))
    if layout.get('schemaVersion')!=1 or layout.get('worldId')!=WORLD_ID or layout.get('dimensionsKm')!=[24,24]:
        raise ValueError('This is not the VALHALLA EXTINCTION 24x24 layout')
    villages=layout.get('villages',[])
    shrines=layout.get('runeShrines',[])
    enemies=layout.get('draugrSpawnCandidates',[])
    if len(villages)!=12 or len(shrines)<4 or len(enemies)<120:
        raise ValueError('Missing Viking settlements, shrines, or Draugr spawn markers')
    known=set()
    for item in [*villages,*shrines,*enemies]:
        if item.get('id') in known:raise ValueError('Duplicated marker ID: '+item['id'])
        known.add(item['id'])
        for key in ('xMeters','yMeters','zMeters'):
            v=item.get(key)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
                raise ValueError(f'Invalid {key} in {item.get("id")}')
        if max(abs(item['xMeters']),abs(item['yMeters']))>11990:
            raise ValueError('Marker outside 24x24 km map')
    return layout


def _ue():
    try:import unreal
    except ImportError as error:raise RuntimeError('Unreal Engine 5.8 Python Editor Script Plugin required') from error
    return unreal


def _pos(u,p,up=0):
    return u.Vector(float(p['xMeters'])*100,float(p['yMeters'])*100,(float(p['zMeters'])+up)*100)


def _marker(u,sub,p,kind):
    a=sub.spawn_actor_from_class(u.TargetPoint,_pos(u,p,2.0),u.Rotator())
    if not a:raise RuntimeError('Failed to spawn '+p['id'])
    a.set_actor_label(('AZ_VALHALLA_'+kind+'_'+p['id'])[:110])
    a.set_editor_property('tags',[u.Name(MARKER_TAG),u.Name('VIKING_'+kind)])
    return a


def create_level(layout_path:str|Path, confirm_create:bool=False, with_enemy_markers:bool=True)->dict:
    """Create a partitioned level once; does NOT import Landscape or real art."""
    layout=check_layout(layout_path)
    result={'level':LEVEL_PATH,'dimensionsKm':[24,24],
            'vikingSettlementMarkers':len(layout['villages']),
            'runeShrineMarkers':len(layout['runeShrines']),
            'draugrSpawnMarkers':len(layout['draugrSpawnCandidates']) if with_enemy_markers else 0,
            'landscapeImported':False,'vikingMeshesPlaced':False,
            'vikingZombieAIWorking':False,'playableBuildTested':False}
    if not confirm_create:return {'dryRun':True,**result}
    u=_ue()
    target=Path(u.Paths.project_content_dir()).resolve()/'Maps'/LEVEL_FILENAME
    if target.exists() or u.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        raise FileExistsError('VALHALLA EXTINCTION level already exists. Refusing overwrite.')
    level=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if level.is_in_play_in_editor():raise RuntimeError('Cannot author a level during PIE')
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    if not level.new_level(LEVEL_PATH,is_partitioned_world=True):
        raise RuntimeError('Unreal failed to create a new World Partition level')
    try:
        for v in layout['villages']:_marker(u,actors,v,'SETTLEMENT')
        for s in layout['runeShrines']:_marker(u,actors,s,'RUNE_SHRINE')
        if with_enemy_markers:
            for e in layout['draugrSpawnCandidates']:_marker(u,actors,e,'DRAUGR')
        if not level.save_current_level():raise RuntimeError('Save failed')
    except Exception:
        # Do not erase the new level or mutate another world. Report partial state.
        raise
    return {'dryRun':False,**result}


def place_real_assets(layout_path:str|Path, asset_bindings_path:str|Path,
                      confirm_place:bool=False)->dict:
    """Spawn real game assets only when EVERY required path is explicitly bound.

    Requires a previously created level with imported, visually validated
    Landscape and all source assets. Only creates actors in VALHALLA map.
    This does not itself build AI behavior, inventory, navmesh or clothing.
    """
    layout=check_layout(layout_path)
    bindings=json.loads(Path(asset_bindings_path).read_text(encoding='utf-8'))
    names=('longhouse','rune_shrine','timber_palisade','drakkar','draugr-thrall',
           'draugr-huskarl','draugr-berserker','draugr-shieldmaiden','draugr-seidr')
    required={n:bindings.get(n) for n in names}
    invalid=[n for n,p in required.items() if not isinstance(p,str) or not p.startswith('/Game/')]
    if invalid:return {'dryRun':True,'ready':False,'missingAssetBindings':invalid}
    if not confirm_place:return {'dryRun':True,'ready':False,'suppliedAssets':required,
                                  'warning':'Verify all existing UE5 assets, clothing rigs and Landscape before placement.'}
    u=_ue()
    level=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if level.is_in_play_in_editor():raise RuntimeError('Cannot edit during PIE')
    world=level.get_current_level() if hasattr(level,'get_current_level') else None
    # Require correct loaded World by strict long package check where available.
    if not u.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        raise FileNotFoundError('Create and save VALHALLA_EXTINCTION_24KM map first')
    loaded={}
    for n,p in required.items():
        loaded[n]=u.EditorAssetLibrary.load_blueprint_class(p) if n.startswith('draugr-') else u.EditorAssetLibrary.load_asset(p)
        if not loaded[n]:raise FileNotFoundError('Missing game asset '+n+' at '+p)
    # Do not load/modify any other map. Verify and load the isolated level.
    if not level.load_level(LEVEL_PATH):raise RuntimeError('Could not load Valhalla isolated level')
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    existing={str(a.get_actor_label()) for a in sub.get_all_level_actors()}
    placements=0
    def spawn(name,loc,rot,label,blueprint=False):
        nonlocal placements
        if label in existing:return
        a=(sub.spawn_actor_from_class(loaded[name],loc,rot)
           if blueprint else sub.spawn_actor_from_object(loaded[name],loc,rot))
        if not a:raise RuntimeError('Unable to spawn '+label)
        a.set_actor_label(label)
        a.set_editor_property('tags',[u.Name(MARKER_TAG),u.Name('VIKING_REAL_ASSET')])
        existing.add(label)
        placements+=1
    for v in layout['villages']:
        # A 2D village layout with 3D meshes from the *actual game asset registry*.
        cx,cy,z=float(v['xMeters'])*100,float(v['yMeters'])*100,float(v['zMeters'])*100
        for i in range(7):
            theta=i*2*math.pi/7
            x=cx+math.cos(theta)*11000;y=cy+math.sin(theta)*11000
            # Land is not flat; actors may need adjustment before release.
            spawn('longhouse',u.Vector(x,y,z),u.Rotator(0,i*360/7,0),f'AZ_VALHALLA_LONGHOUSE_{v["id"]}_{i+1}')
        if 'fort' in v['kind'] or 'jarl' in v['kind']:
            for i in range(16):
                theta=i*2*math.pi/16
                spawn('timber_palisade',u.Vector(cx+math.cos(theta)*15500,cy+math.sin(theta)*15500,z),
                      u.Rotator(0,i*360/16+90,0),f'AZ_VALHALLA_WALL_{v["id"]}_{i+1}')
        if any(k in v['kind'] for k in ('harbour','fishing','coast')):
            spawn('drakkar',u.Vector(cx+24000,cy-12000,z),u.Rotator(),f'AZ_VALHALLA_LONGSHIP_{v["id"]}')
    for s in layout['runeShrines']:
        spawn('rune_shrine',_pos(u,s),u.Rotator(),f'AZ_VALHALLA_RUNESTONE_{s["id"]}')
    for e in layout['draugrSpawnCandidates']:
        spawn(e['archetype'],_pos(u,e,1),u.Rotator(),f'AZ_VALHALLA_DRAUGR_{e["id"]}',blueprint=True)
    if not level.save_current_level():raise RuntimeError('Save of Valhalla after actor placement failed')
    return {'dryRun':False,'actorsPlaced':placements,
            'requiresReview':['mesh scales','slope alignment','Viking clothing per BP',
                              'AI/navmesh','world partition streaming','PIE','packaging']}

if __name__=='__main__':
    print('Use Unreal Editor Python console and check_layout/create_level/ place_real_assets')