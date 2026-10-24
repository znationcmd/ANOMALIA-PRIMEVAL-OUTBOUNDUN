"""Place verified scanned exteriors inside the existing 50m town parcels.

Pure placement calculations. No file, actor, terrain or player data is modified.
"""
import hashlib
import math

MODELS={'country_house_scan':(22.,22.,7.),'abandoned_brick_house_scan':(34.,30.,10.)}

def model_for(identifier):
    value=int(hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:8],16)%10
    return 'country_house_scan' if value<6 else 'abandoned_brick_house_scan'

def placement(item,origin_cm,extent_cm,surface,envelope):
    """Return a uniformly scaled, centred footprint or a precise rejection reason."""
    model=model_for(item['id']);caps=MODELS[model]
    if len(origin_cm)!=3 or len(extent_cm)!=3 or not all(math.isfinite(x) for x in (*origin_cm,*extent_cm)) or min(extent_cm)<=0:
        raise ValueError('Finite nonempty native mesh bounds required')
    yaw=float(item['yaw'])
    if yaw not in (0.,180.):raise ValueError('Only the owned town parcel orientations are supported')
    scale=min(caps[i]*100/(2*extent_cm[i]) for i in range(3))
    width,depth,height=[2*x*scale/100 for x in extent_cm]
    clearance=25-max(width,depth)/2-4.25
    if clearance<2:raise ValueError('Scan would obstruct the reserved street corridor')
    east,north=item['east'],item['north']
    low,high=envelope(surface,east,north,width,depth)
    if low<5 or high>250:return {'model':model,'rejected':'wet-or-high'}
    if high-low>.12:return {'model':model,'rejected':'expanded-footprint-relief'}
    angle=math.radians(yaw);c,s=math.cos(angle),math.sin(angle)
    ox=(c*origin_cm[0]-s*origin_cm[1])*scale
    oy=(s*origin_cm[0]+c*origin_cm[1])*scale
    bottom=(origin_cm[2]-extent_cm[2])*scale
    return dict(model=model,scale=scale,yaw=yaw,
                locationCm=[east*100-ox,-north*100-oy,high*100-45-bottom],
                footprintMetres=[width,depth],heightMetres=height,
                roadClearanceMetres=clearance,groundReliefMetres=high-low,
                exteriorOnly=True,terrainModified=False)
