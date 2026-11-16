#!/usr/bin/env python3
"""VALHALLA EXTINCTION: independent 24 x 24 km Viking/Draugr UE5.8 source kit.

Produces an ORIGINAL 2017x2017 RAW16 landscape, sixteen seamless 505x505
RAW16 tiles, Viking settlement and undead encounter candidates, and SHA256
manifest. It does NOT produce a native .umap or playable game.

Requirements: Python 3.10+, numpy. Never overwrites an existing destination.
python generate_valhalla_extinction.py --output C:/VALHALLA_EXTINCTION_NEW
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

ID = 'valhalla-extinction'
NAME = 'VALHALLA EXTINCTION'
SEED = 'ANOMALIA-VALHALLA-EXTINCTION-2026'
VERSION = 'valhalla-r16-v1'
WIDTH = 24000.0
TILE_METERS = 6000.0
COUNT = 4
TILE_SAMPLES = 505
SAMPLES = COUNT*(TILE_SAMPLES-1)+1  # 2017 x 2017
Z_SCALE_CM = 800.0
X_SCALE_CM = WIDTH * 100 / (SAMPLES-1)
BASE = Path(__file__).resolve().parent

# User's request: a PURE Viking island, with Viking-clothed undead, no modern sites.
VILLAGES = [
 ('valhallborg','Valhallborg','jarl-fortress',-2500, -850),
 ('ravnhavn','Ravnhavn','longship-harbour',-8500,-3900),
 ('frostvik','Frostvik','fishing-village',-5000,6500),
 ('draugheim','Draugheim','undead-ruins',2100,7500),
 ('skjoldgard','Skjoldgard','shield-wall-fort',5100,3100),
 ('blodfjord','Blodfjord','blood-fjord-harbour',-7200,2050),
 ('ulvheim','Ulvheim','hunter-village',4200,-4800),
 ('runestein','Runestein','rune-sanctuary',-900,-6700),
 ('jernvik','Jernvik','smith-village',-4500,-6400),
 ('helgrind','Helgrind','burial-mounds',6700,300),
 ('nattravn','Nattravn','forest-village',1050,4450),
 ('isfjord','Isfjord','ice-coast-outpost',-7000,7900),
]

ZOMBIE_ARCHETYPES = [
 {"id":"draugr-thrall","name":"Draugr Thrall","weight":45,"clothing":["linen_tunic","wool_trousers","leather_boots","torn_cloak"],"weapon":"rusty_axe"},
 {"id":"draugr-huskarl","name":"Draugr Huskarl","weight":20,"clothing":["mail_hauberk","wool_tunic","iron_helmet_no_horns","fur_cloak"],"weapon":"viking_sword"},
 {"id":"draugr-berserker","name":"Draugr Berserker","weight":12,"clothing":["bear_fur","leather_belt","wool_trousers"],"weapon":"two_handed_axe"},
 {"id":"draugr-shieldmaiden","name":"Draugr Shieldmaiden","weight":13,"clothing":["wool_dress","leather_vest","fur_shawl","leather_boots"],"weapon":"round_shield_and_spear"},
 {"id":"draugr-seidr","name":"Draugr Seidr","weight":10,"clothing":["ritual_wool_robe","hood","bone_necklace","leather_boots"],"weapon":"ritual_staff"},
]

BIOMES = ["deep_fjord","rocky_coast","pine_birch_forest","peat_marsh","mountain_tundra","snow_peak","glacial_valley"]


def _gauss(x,y,cx,cy,sx,sy):
    return np.exp(-(((x-cx)/sx)**2 + ((y-cy)/sy)**2))


def terrain(x,y):
    """Original deterministic fictional Norwegian/Norse height field (metres)."""
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    coast=(1.0-((x+400)/11250)**2-((y-300)/10750)**2
           +.13*np.sin(x/2070 + .52*np.sin(y/1630))
           +.063*np.sin(y/890+x/1450)+.022*np.cos(x/410-y/700))
    # Two outer island groups, separated by ocean in the northern and eastern sea.
    outer=np.maximum(.62-((x-8850)/2050)**2-((y-8600)/2400)**2,
                     .52-((x+9200)/2150)**2-((y+8050)/2450)**2)
    shore=np.maximum(coast,outer)
    land=np.clip(shore/.56,0,1)
    floor=(22+215*np.minimum(1,land))
    ridge=(1230*_gauss(x,y,-6000,5100,2050,3100)
           +1310*_gauss(x,y,5600,4300,2350,2600)
           +1050*_gauss(x,y,6100,-4400,2400,2550)
           +910*_gauss(x,y,-3800,-5500,2250,2550)
           +860*_gauss(x,y,-700,8100,2500,1900)
           +510*_gauss(x,y,500,-2400,2800,2300))
    waves=42*np.sin(x/680)*np.cos(y/940)+29*np.sin(x/280+y/345)+16*np.sin(y/135-x/240)
    ground=floor+land*(ridge+waves)
    seafloor=-20.0-np.maximum(0,-shore)*180
    ground=np.where(shore>.025,ground, np.where(shore>-.055, ground * (shore+.055)/.08-25, seafloor))

    # Ancient, deep, connected fjords. Smooth banks, with steep but finite slopes.
    wy=2100+740*np.sin((x+1200)/1800)
    west_channel=np.clip((650-np.abs(y-wy))/400,0,1)*np.clip((-x-500)/2100,0,1)
    sy=-4200+920*np.sin(y/2150)
    south_channel=np.clip((720-np.abs(x-sy))/420,0,1)*np.clip((-y-500)/3000,0,1)
    ey=-2500+590*np.sin(x/1700)
    east_channel=np.clip((560-np.abs(y-ey))/340,0,1)*np.clip((x-700)/2500,0,1)
    fjord=np.maximum(west_channel,np.maximum(south_channel,east_channel))
    ground=ground*(1-fjord)+(-95-70*fjord)*fjord
    # A narrow glacial lake above the mountain valley.
    lake=np.clip((580-np.abs(y-4950))/380,0,1)*np.clip((2400-np.abs(x+1100))/800,0,1)
    ground=ground*(1-lake)+(-12)*lake
    return np.clip(ground,-340,1850)


def height_as_u16(heights):
    # Unreal Landscape: metres = (u16 - 32768) * Z_SCALE_CM / 12800
    enc=np.rint(32768+np.asarray(heights)*12800.0/Z_SCALE_CM)
    if np.any(enc<0) or np.any(enc>65535):
        raise ValueError('Height outside R16 Unreal Landscape Z scale')
    return enc.astype('<u2')


def elevation_at(x,y):
    return float(terrain(float(x),float(y)))


def slope_at(x,y,rad=65):
    return math.hypot(elevation_at(x+rad,y)-elevation_at(x-rad,y),
                      elevation_at(x,y+rad)-elevation_at(x,y-rad))/(2*rad)


def find_land(anchor_x,anchor_y,used,kind):
    # Viking harbours and fishermen MUST have a real nearby sea access.
    coastal=any(k in kind for k in ('harbour','fishing','coast'))
    best=None
    for radius in range(0,7001 if coastal else 4100,250):
        for dy in range(-radius,radius+1,250):
            for dx in range(-radius,radius+1,250):
                if max(abs(dx),abs(dy))!=radius: continue
                x,y=anchor_x+dx,anchor_y+dy
                if not (-11400 < x < 11400 and -11400 < y < 11400):continue
                if any(math.hypot(x-u[0],y-u[1])<1450 for u in used):continue
                z=elevation_at(x,y)
                slope=slope_at(x,y)
                if coastal:
                    # Harbor approach checked against sea level in four directions.
                    if not (12<z<140 and slope<.48):continue
                    if not any(elevation_at(x+ox,y+oy)<0 for ox,oy in
                               ((400,0),(-400,0),(0,400),(0,-400))):continue
                    target=45
                else:
                    if not (18<z<560 and slope<.38):continue
                    target=190
                score=math.hypot(dx,dy)+abs(z-target)*1.8+slope*600
                if best is None or score<best[0]:best=(score,x,y,z)
        if best and radius>max(750,best[0]*.70):break
    if best is None:raise RuntimeError(f'No buildable land for {kind} near {anchor_x},{anchor_y}')
    return best[1],best[2],best[3]


def classify_biome(z,slope,near_water=False):
    if z<=0:return 'deep_fjord'
    if near_water and z<130:return 'rocky_coast'
    if z>880:return 'snow_peak'
    if z>510:return 'mountain_tundra'
    if z<70 and slope<.11:return 'peat_marsh'
    if z<160 and slope<.08:return 'glacial_valley'
    return 'pine_birch_forest'


def build_layout():
    villages=[];used=[]
    for ident,name,kind,x,y in VILLAGES:
        xx,yy,z=find_land(x,y,used,kind)
        used.append((xx,yy))
        villages.append({"id":ident,"name":name,"kind":kind,
            "xMeters":xx,"yMeters":yy,"zMeters":round(z,2),
            "xCm":xx*100,"yCm":yy*100,"zCm":round((z+3)*100),
            "has3DMeshes":False,"hasVikingZombieActors":False,
            "buildingRequirements":(["longhouse","timber_palisade","watchtower","runestone","smithy"] if 'fort' in kind or 'jarl' in kind else
                ["longhouse","boat_shed","drakkar","timber_pier"] if any(k in kind for k in ('harbour','fishing','coast')) else
                ["longhouse","rune_shrine","burial_mound"] if any(k in kind for k in ('sanctuary','burial','ruins')) else
                ["longhouse","smithy","fenced_hut"]),
            "zombieFaction":"draugr-vikings"})
    # Encounters must be on land, separated, and reproducible; all are only spawn CANDIDATES.
    encounters=[]
    for v in villages:
        for k in range(14):
            found=None
            for attempt in range(60):
                angle=2*math.pi*((k*0.61803398875+attempt*.17320508)%1)
                distance=330+((k*307+attempt*197)%1320)
                x=v['xMeters']+math.cos(angle)*distance
                y=v['yMeters']+math.sin(angle)*distance
                if max(abs(x),abs(y))>11500:continue
                z=elevation_at(x,y)
                if z<9 or z>900 or slope_at(x,y)>0.7:continue
                if math.hypot(x-v['xMeters'],y-v['yMeters'])<260:continue
                found=(x,y,z);break
            if found is None:continue
            x,y,z=found
            archetype=ZOMBIE_ARCHETYPES[(k+len(encounters)//17)%len(ZOMBIE_ARCHETYPES)]
            encounters.append({"id":f"draugr-{len(encounters)+1:04d}","villageId":v['id'],
                "archetype":archetype['id'],"xMeters":round(x,2),"yMeters":round(y,2),
                "zMeters":round(z,2),"difficulty":"elite" if k in (6,13) else "normal",
                "status":"spawn-point-only-no-AI"})
    shrines=[]
    for i,v in enumerate(villages[:8]):
        found=None
        for r in (320,560,790,1050,1400):
            x=v['xMeters']+r*math.cos(i*2.4+0.3)
            y=v['yMeters']+r*math.sin(i*2.4+0.3)
            z=elevation_at(x,y)
            if 40<z<800 and slope_at(x,y)<0.45:
                found=(x,y,z);break
        if found:
            x,y,z=found
            shrines.append({"id":f"shrine-{i+1:02d}","name":f"Odin shrine {i+1}",
                "xMeters":round(x,2),"yMeters":round(y,2),"zMeters":round(z,2),
                "requirements":["rune_monolith","altar","torch","grave_stones"],
                "status":"marker-only"})
    routes=[]
    for i,v in enumerate(villages[1:]):
        parent=min(villages[:i+1],key=lambda u:math.hypot(u['xMeters']-v['xMeters'],u['yMeters']-v['yMeters']))
        routes.append({"from":parent['id'],"to":v['id'],"type":"dirt-path-or-fjord-passage",
                       "status":"needs-spline-and-navigation-validation"})
    return {"schemaVersion":1,"worldId":ID,"name":NAME,"seed":SEED,
        "dimensionsKm":[24,24],"areaKm2":576,"theme":"Viking era Nordic dark fantasy + Viking-clothed undead",
        "historicalStyle":"Norse 8th-11th century; no horned helmets, modern roads, vehicles, guns, contemporary clothing or architecture",
        "villages":villages,"runeShrines":shrines,"draugrSpawnCandidates":encounters,
        "zombieArchetypes":ZOMBIE_ARCHETYPES,"biomes":BIOMES,"routeCandidates":routes,
        "requiredAssetTypes":["longhouse","timber_palisade","watchtower","runestone","smithy",
            "boat_shed","drakkar","timber_pier","rune_shrine","burial_mound","fenced_hut",
            "rune_monolith","altar","torch","grave_stones","viking_zombie_skeletal_mesh",
            "viking_zombie_anim_bp","viking_clothing_assets","viking_weapons"],
        "gameplayReady":False,"actorsPlacedInUE5":False,
        "sourceOnly":True}


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def generate(out:Path, max_samples:int=SAMPLES):
    out=out.expanduser().resolve()
    if out.exists():raise FileExistsError(f'Refusing existing destination: {out}')
    if BASE==out or BASE in out.parents:raise ValueError('Output must be outside script directory')
    if max_samples!=SAMPLES:raise ValueError('Only Unreal-compatible 2017x2017 output is supported')
    out.mkdir(parents=True)
    (out/'tiles').mkdir()
    xs=np.linspace(-12000,12000,SAMPLES)
    # north-to-south row ordering, must check Y orientation in editor.
    ys=np.linspace(12000,-12000,SAMPLES)
    terrain_array=height_as_u16(terrain(xs[None,:],ys[:,None]))
    combined=out/'VALHALLA_EXTINCTION_2017x2017.r16'
    combined.write_bytes(terrain_array.tobytes(order='C'))
    tiles=[]
    for row in range(COUNT):
        for col in range(COUNT):
            y=row*(TILE_SAMPLES-1);x=col*(TILE_SAMPLES-1)
            tile=np.ascontiguousarray(terrain_array[y:y+TILE_SAMPLES,x:x+TILE_SAMPLES])
            path=out/'tiles'/f'height_x{col}_y{row}.r16'
            path.write_bytes(tile.tobytes(order='C'))
            tiles.append({'row':row,'column':col,'file':'tiles/'+path.name,
                          'samples':[TILE_SAMPLES,TILE_SAMPLES],
                          'sha256':sha256(path),'bytes':path.stat().st_size})
    layout=build_layout()
    (out/'valhalla-layout.json').write_text(json.dumps(layout,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (out/'valhalla-placements.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.writer(f);wr.writerow(['kind','id','asset_or_blueprint_needed','xCm','yCm','zCm'])
        for v in layout['villages']:
            wr.writerow(['village',v['id'],'viking_longhouse_mesh',v['xCm'],v['yCm'],v['zCm']])
        for s in layout['runeShrines']:
            wr.writerow(['shrine',s['id'],'rune_shrine_mesh',round(s['xMeters']*100),round(s['yMeters']*100),round(s['zMeters']*100)])
        for p in layout['draugrSpawnCandidates']:
            wr.writerow(['zombie',p['id'],p['archetype'],round(p['xMeters']*100),round(p['yMeters']*100),round((p['zMeters']+2)*100)])
    low=float(terrain_array.min()); high=float(terrain_array.max())
    manifest={'schema':'ANOMALIA-VALHALLA-R16-1','worldId':ID,'name':NAME,'seed':SEED,
        'dimensionsKm':[24,24],'areaKm2':576,'outputVersion':VERSION,
        'format':'unsigned little-endian RAW16','resolution':[SAMPLES,SAMPLES],
        'heightmapSha256':sha256(combined),'heightmapBytes':combined.stat().st_size,
        'tileGrid':[COUNT,COUNT],'tileSamples':[TILE_SAMPLES,TILE_SAMPLES],
        'tileMeters':TILE_METERS,'tiles':tiles,
        'landscapeImport':{'sectionQuads':63,'sectionsPerComponent':[2,2],
            'components':[16,16], 'scaleXYZcm':[round(X_SCALE_CM,9),round(X_SCALE_CM,9),Z_SCALE_CM],
            'originCm':[-1200000,-1200000,0],
            'heightEncoding':'R16 32768 = sea level; u16 to meters = (value-32768)*800/12800',
            'flipY':'verify in UE5; source rows run north-to-south'},
        'actualHeightRangeMetres':[round((low-32768)*Z_SCALE_CM/12800,2),round((high-32768)*Z_SCALE_CM/12800,2)],
        'villages':len(layout['villages']),'runeShrines':len(layout['runeShrines']),
        'draugrSpawnCandidates':len(layout['draugrSpawnCandidates']),
        'containsUmap':False,'landscapeImportedInUE':False,
        'hasLicensedVikingMeshes':False,'vikingZombieAIBuilt':False,'playableBuildTested':False,
        'noExistingWorldsModified':True,'status':'REAL TERRAIN SOURCE, NOT YET A UE LEVEL'}
    (out/'terrain-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return manifest


def verify(out:Path):
    m=json.loads((out/'terrain-manifest.json').read_text(encoding='utf-8'))
    assert (out/'VALHALLA_EXTINCTION_2017x2017.r16').stat().st_size == SAMPLES**2 * 2
    assert sha256(out/'VALHALLA_EXTINCTION_2017x2017.r16')==m['heightmapSha256']
    for row in range(COUNT):
        for col in range(COUNT):
            tile=np.fromfile(out/'tiles'/f'height_x{col}_y{row}.r16',dtype='<u2').reshape(TILE_SAMPLES,TILE_SAMPLES)
            if col<COUNT-1:
                r=np.fromfile(out/'tiles'/f'height_x{col+1}_y{row}.r16',dtype='<u2').reshape(TILE_SAMPLES,TILE_SAMPLES)
                assert np.array_equal(tile[:,-1],r[:,0]),'East-west seam mismatch'
            if row<COUNT-1:
                s=np.fromfile(out/'tiles'/f'height_x{col}_y{row+1}.r16',dtype='<u2').reshape(TILE_SAMPLES,TILE_SAMPLES)
                assert np.array_equal(tile[-1,:],s[0,:]),'North-south seam mismatch'
    layout=json.loads((out/'valhalla-layout.json').read_text(encoding='utf-8'))
    assert len(layout['villages']) == 12
    assert len(layout['draugrSpawnCandidates'])>=120
    return {'verified':True,'heightmapMiB':round(SAMPLES*SAMPLES*2/1024**2,2),
        'villages':len(layout['villages']),'draugrSpawns':len(layout['draugrSpawnCandidates']),
        'tiles':COUNT**2,'allTileSeamsMatch':True}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args()
    manifest=generate(args.output)
    print(json.dumps({'built':True,'map':manifest['name'],'dimensionsKm':manifest['dimensionsKm'],
                      'validation':verify(args.output)},indent=2,ensure_ascii=False))

if __name__=='__main__':main()