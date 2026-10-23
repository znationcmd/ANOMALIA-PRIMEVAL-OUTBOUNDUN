"""Original urban test block, in metres. No changes to production geography or saves."""


def layout():
    buildings=[]
    for x in [-120,-40]:
        for y in [30,90]:buildings.append(dict(id=f'hlm_{x}_{y}',model='hlm_8floors_v1',x=x,y=y,width=18.6,depth=13.8))
    for x in [40,120]:
        for y in [30,90]:buildings.append(dict(id=f'residence_{x}_{y}',model='residence_4floors',x=x,y=y,width=16.5,depth=14))
    for x in [-140,-115,-60,-35]:
        for y in [-30,-90,-150]:buildings.append(dict(id=f'house_{x}_{y}',model='townhouse',x=x,y=y,width=10.5,depth=10.7))
    for x in [40,120]:
        for y in [-30,-90]:buildings.append(dict(id=f'villa_{x}_{y}',model='beach_villa_pool_v1',x=x,y=y,width=10.75,depth=16.95))
    for model,x,y,width,depth in [('hospital',40,150,20.5,15.7),('police_station',120,150,10.5,10.7),('fire_station',40,-150,20.5,14.5),('farm_barn',120,-150,10.5,9.5)]:
        buildings.append(dict(id=model,model=model,x=x,y=y,width=width,depth=depth))
    roads=[dict(id=f'road_h_{y}',x=0,y=y,width=360,depth=7) for y in [-180,-120,-60,0,60,120,180]]
    roads += [dict(id=f'road_v_{x}',x=x,y=0,width=7,depth=400) for x in [-80,0,80]]
    # Source villa bounds centre is (0, -4.325m) in its horizontal plane;
    # the pool is centred at local depth -10m. Preserve its below-grade basin.
    pools=[dict(x=b['x'],y=b['y']-5.675,width=8.4,depth=4.4) for b in buildings if b['model']=='beach_villa_pool_v1']
    return dict(schemaVersion=1,buildings=buildings,roads=roads,pools=pools,groundBounds=[-190,-210,190,210],state='URBAN_TEST_LAYOUT_NOT_PRODUCTION_WORLD')


def rectangle(item,margin=0):
    return [item['x']-item['width']/2-margin,item['y']-item['depth']/2-margin,item['x']+item['width']/2+margin,item['y']+item['depth']/2+margin]


def overlaps(a,b):
    return min(a[2],b[2])-max(a[0],b[0])>1e-7 and min(a[3],b[3])-max(a[1],b[1])>1e-7


def ground_rectangles(bounds,pools):
    """Partition a flat ground surface into rectangles with exact open pool recesses."""
    holes=[rectangle(p) for p in pools]
    xs=sorted({bounds[0],bounds[2],*(v for h in holes for v in [h[0],h[2]])})
    ys=sorted({bounds[1],bounds[3],*(v for h in holes for v in [h[1],h[3]])})
    result=[]
    for x0,x1 in zip(xs,xs[1:]):
        for y0,y1 in zip(ys,ys[1:]):
            rect=[x0,y0,x1,y1]
            if not any(overlaps(rect,h) for h in holes):result.append(rect)
    return result


def service_fleet():
    """Off-street parking for possessable service vehicles, metres in the urban review."""
    return [
        dict(id='police_patrol',model='police',x=120,y=135,width=8,depth=4,service='police_station'),
        dict(id='fire_response',model='fire_engine',x=40,y=-165,width=12,depth=4,service='fire_station'),
        dict(id='medical_response',model='ambulance',x=40,y=135,width=9,depth=4,service='hospital'),
    ]
