"""Deterministic placement in metres on the unchanged 3025-sample landscape.
Pure Python; callers supply the authoritative native height function and mesh bounds.
Does not claim finished towns, routes, interiors, or a playable world.
"""
import math
from functools import lru_cache
import importlib.util
from pathlib import Path
_identity_spec=importlib.util.spec_from_file_location('anomalia_place_identity',Path(__file__).with_name('place_identity.py'))
_identity_module=importlib.util.module_from_spec(_identity_spec)
_identity_spec.loader.exec_module(_identity_module)
place_identity=_identity_module.place_identity

HALF=24000.0
STEP=48000.0/3024

def sampled_surface(native_height):
    """Bilinear sample plus an error bound for either landscape cell triangulation."""
    @lru_cache(maxsize=180000)
    def vertex(i,j):
        h=native_height(-HALF+i*STEP,-HALF+j*STEP)
        if not math.isfinite(h):raise ValueError('Nonfinite native terrain height')
        return (min(65535,max(0,math.floor(32768+h*16+.5)))-32768)/16
    def surface(e,n):
        if not all(math.isfinite(v) and -HALF<=v<=HALF for v in (e,n)):
            raise ValueError('Position outside archipelago')
        x=(e+HALF)/STEP;y=(n+HALF)/STEP
        i=min(3023,int(x));j=min(3023,int(y));u=x-i;v=y-j
        a,b,c,d=vertex(i,j),vertex(i+1,j),vertex(i,j+1),vertex(i+1,j+1)
        value=a*(1-u)*(1-v)+b*u*(1-v)+c*(1-u)*v+d*u*v
        # Both diagonal choices differ from bilinear by at most |saddle|/4.
        return value,abs(a-b-c+d)/4
    return surface

def ground_envelope(surface,e,n,width,depth):
    def cuts(center,size):
        lo,hi=center-size/2,center+size/2
        if lo < -HALF or hi > HALF:raise ValueError('Footprint outside archipelago')
        return [lo,hi]+[-HALF+i*STEP for i in range(math.ceil((lo+HALF)/STEP),math.floor((hi+HALF)/STEP)+1)]
    values=[surface(x,y) for x in cuts(e,width) for y in cuts(n,depth)]
    return min(z-error for z,error in values),max(z+error for z,error in values)

def noise(i,j,salt=0):
    value=((i*374761393+j*668265263+salt*1274126177)&0xffffffff)
    value=((value^(value>>13))*1274126177)&0xffffffff
    return (value^(value>>16))/4294967295

def build_plan(native_height,house_dimensions,max_relief=.12,sites=None):
    if len(house_dimensions)!=3 or not all(math.isfinite(v) and 1<v<40 for v in house_dimensions):
        raise ValueError('Expected metre-scale building bounds')
    if not math.isfinite(max_relief) or not 0<max_relief<=.3:raise ValueError('Unsafe building ground tolerance')
    width,height,depth=house_dimensions
    surface=sampled_surface(native_height)
    buildings=[];settlements=[];rejected=dict(noDrySite=0,wetOrHigh=0,slope=0)
    # Each 8km sector gets a separate inhabited centre where terrain allows it.
    # Search the whole sector; disconnected islands may receive independent centres.
    for row,north in enumerate(range(-20000,24000,8000)):
        for col,east in enumerate(range(-20000,24000,8000)):
            candidates=[]
            if sites is not None:
                candidates=[(0,0,e,n) for e,n in sites if east-4000<=e<east+4000 and north-4000<=n<north+4000]
            for dy in ([] if sites is not None else range(-2800,2801,700)):
                for dx in range(-2800,2801,700):
                    e,n=east+dx,north+dy
                    z,_=surface(e,n)
                    if not 6<z<240:continue
                    lo,hi=ground_envelope(surface,e,n,width,depth)
                    candidates.append((hi-lo,abs(dx)+abs(dy),e,n))
            if not candidates:rejected['noDrySite']+=1;continue
            _,_,e0,n0=min(candidates)
            ident=f'settlement_{row}_{col}';start=len(buildings)
            # 50m parcel grid leaves at least 12m corridors for later street authoring.
            for iy in range(-7,7):
                for ix in range(-7,7):
                    e=e0+(ix+.5)*50;n=n0+(iy+.5)*50
                    yaw=0 if (ix+iy)%2 else 180
                    lo,hi=ground_envelope(surface,e,n,width,depth)
                    if lo<5 or hi>250:rejected['wetOrHigh']+=1;continue
                    if hi-lo>max_relief:rejected['slope']+=1;continue
                    # A 10cm ground overlap keeps the lowest slab from hovering.
                    buildings.append(dict(id=f'{ident}_house_{ix+7}_{iy+7}',model='detached_house',east=e,north=n,z=hi-.1,yaw=yaw,width=width,depth=depth,groundMin=lo,groundMax=hi))
            settlements.append(dict(**place_identity(ident, 'city' if len(buildings)-start>=140 else 'village'),east=e0,north=n0,buildingCount=len(buildings)-start))
    # Sparse world-wide vegetation base. Fine biome dressing is a separate stage.
    foliage=[]
    for iy,n in enumerate(range(-23900,24000,140)):
        for ix,e in enumerate(range(-23900,24000,140)):
            h,_=surface(e,n)
            if not 3<h<600:continue
            # Keep urban footprints and reserved street corridors clear.
            if any(abs(e-s['east'])<420 and abs(n-s['north'])<420 for s in settlements):continue
            p=noise(ix,iy,17)
            # Southeastern arid region stays sparse rather than receiving a temperate forest.
            arid=e>3000 and n<-4000
            if p>(.10 if arid else .46):continue
            model='rock_moss_set_01' if p<.035 else 'grass_medium_01' if p<.16 else 'island_tree_02'
            foliage.append(dict(id=f'foliage_{ix}_{iy}',model=model,east=e,north=n,z=h,yaw=noise(ix,iy,19)*360,scale=.85+noise(ix,iy,23)*.3))
    return dict(schemaVersion=1,mapPackage='/Game/Maps/ANOMALIA_Inhabited_v1' if sites is not None else '/Game/Maps/ANOMALIA_Archipelago_v2',state='POPULATION_PLAN_NOT_EXECUTED',worldWidthMeters=48000,terrainModified=sites is not None,buildings=buildings,settlements=settlements,foliage=foliage,rejected=rejected,houseMaxReliefMeters=max_relief,roadsBuilt=False,servicesBuilt=False,playtested=False,photorealismValidated=False)
