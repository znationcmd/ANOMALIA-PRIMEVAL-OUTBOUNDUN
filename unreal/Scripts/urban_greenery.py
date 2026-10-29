"""Deterministic planting around saved buildings and reserved town streets.

All coordinates are metres east/north, all returned transforms centimetres UE.
No terrain, house, street or existing foliage is edited by this planner.
"""
import hashlib,math
from collections import defaultdict

PREFIX='ANOMALIA_UrbanGreenery_v1_'

def unit(key,salt):return int(hashlib.sha256((key+':'+salt).encode()).hexdigest()[:8],16)/4294967295

def boxes_from_descriptors(descriptors):
    boxes=[]
    for d in descriptors:
        if d['label'].startswith(('ANOMALIA_Streets_',PREFIX)):continue
        cls=d['nativeClass']
        # Existing broad foliage cluster bounds and world lighting/water aren't
        # structures. Unknown user actors with valid bounds are reserved.
        if cls in {'/Script/Landscape.Landscape','/Script/Landscape.LandscapeStreamingProxy',
                   '/Script/AnomaliaZPrigimalia.AnomaliaSceneryCluster','/Script/AnomaliaZPrigimalia.AnomaliaNavigableWater',
                   '/Script/Engine.DirectionalLight','/Script/Engine.SkyLight','/Script/Engine.SkyAtmosphere',
                   '/Script/Engine.WorldSettings','/Script/Engine.LevelBounds','/Script/Engine.PlayerStart'}:continue
        if not d.get('boundsValid'):
            if cls=='/Script/Engine.StaticMeshActor':raise ValueError('Unknown structure bounds: '+d['label'])
            continue # Non-geometric editor helpers have no placement footprint.
        lo,hi=d['boundsMinCm'],d['boundsMaxCm']
        if not all(math.isfinite(v) for v in (*lo,*hi)) or any(a>b for a,b in zip(lo,hi)):raise ValueError('Invalid actor bounds')
        boxes.append((lo[0]/100,hi[0]/100,-hi[1]/100,-lo[1]/100))
    return boxes

def clear_circle(e,n,r,boxes,margin=1.):
    for x0,x1,y0,y1 in boxes:
        dx=max(x0-e,0,e-x1);dy=max(y0-n,0,n-y1)
        if dx*dx+dy*dy<(r+margin)**2:return False
    return True

def street_clear(e,n,r,site):
    # Cross streets repeat every 50m. The original mesh has 4.25m half width.
    distance=lambda value:abs((value+25)%50-25)
    return min(distance(e-site['east']),distance(n-site['north']))>=4.25+r+.75

def plan_greenery(population,descriptors,models,surface,envelope):
    if population['mapPackage']!='/Game/Maps/ANOMALIA_Inhabited_v2':raise ValueError('Wrong world')
    sites={s['id']:s for s in population['settlements']}
    boxes=boxes_from_descriptors(descriptors);index=defaultdict(list)
    for box in boxes:
        x0,x1,y0,y1=box
        for x in range(math.floor(x0/100),math.floor(x1/100)+1):
            for y in range(math.floor(y0/100),math.floor(y1/100)+1):index[x,y].append(box)
    clusters=defaultdict(list);counts=defaultdict(int);rejected=defaultdict(int);planted=[]
    def plant(model_id,e,n,site,key):
        model=models[model_id];origin,extent=model['origin'],model['extent']
        if min(extent)<=0 or not all(math.isfinite(v) for v in (*origin,*extent)):raise ValueError('Invalid vegetation bounds')
        # Conservative yaw-independent full crown radius, not just trunk size.
        radius_cap=2.6 if model_id=='island_tree_02' else .48
        height_cap=950 if model_id=='island_tree_02' else 85
        scale=min(1.,radius_cap*100/math.hypot(extent[0],extent[1]),height_cap/(2*extent[2]))*(.9+.1*unit(key,'scale'))
        radius=math.hypot(extent[0],extent[1])*scale/100
        if not street_clear(e,n,radius,site):rejected['street']+=1;return False
        nearby={b for x in range(math.floor((e-8)/100),math.floor((e+8)/100)+1) for y in range(math.floor((n-8)/100),math.floor((n+8)/100)+1) for b in index[x,y]}
        if not clear_circle(e,n,radius,nearby):rejected['structure']+=1;return False
        lo,hi=envelope(surface,e,n,radius*2,radius*2)
        if lo<5 or hi>250 or hi-lo>(.35 if model_id=='island_tree_02' else .12):rejected['ground']+=1;return False
        if model_id=='island_tree_02' and any(math.hypot(e-x,n-y)<radius+r+.5 for x,y,r in planted):rejected['other_tree']+=1;return False
        z,error=surface(e,n);yaw=360*unit(key,'yaw');angle=math.radians(yaw);c,s=math.cos(angle),math.sin(angle)
        offsetx=(c*origin[0]-s*origin[1])*scale;offsety=(s*origin[0]+c*origin[1])*scale
        location=[e*100-offsetx,-n*100-offsety,(z+error-.04)*100-(origin[2]-extent[2])*scale]
        cx,cy=math.floor(e/1000),math.floor(n/1000)
        label=PREFIX+model_id+'_'+str(cx)+'_'+str(cy)
        clusters[label].append(dict(key=key,model=model_id,east=e,north=n,locationCm=location,scale=scale,yaw=yaw,crownRadiusMeters=radius))
        counts[model_id]+=1
        if model_id=='island_tree_02':planted.append((e,n,radius))
        return True
    for house in sorted(population['buildings'],key=lambda h:h['id']):
        key=house['id']
        if unit(key,'choose')>.25:continue
        site=sites[key.split('_house_')[0]]
        quadrant=int(unit(key,'corner')*4)%4
        corners=[(1,1),(1,-1),(-1,1),(-1,-1)]
        for attempt in range(4):
            dx,dy=corners[(quadrant+attempt)%4]
            e=house['east']+dx*(16+.4*unit(key,'east'));n=house['north']+dy*(16+.4*unit(key,'north'))
            if plant('island_tree_02',e,n,site,key):
                for i in range(3):
                    angle=(i*120+unit(key,'grass')*360)*math.pi/180
                    plant('grass_medium_01',e+1.6*math.cos(angle),n+1.6*math.sin(angle),site,key+'_grass_'+str(i))
                break
    return dict(schemaVersion=1,mapPackage=population['mapPackage'],state='PLANTING_PLAN_NOT_EXECUTED',
                counts=dict(counts),rejected=dict(rejected),clusters=[dict(label=k,instances=v) for k,v in sorted(clusters.items())],
                terrainModified=False,housesModified=False,streetsModified=False,fullMapComplete=False)
