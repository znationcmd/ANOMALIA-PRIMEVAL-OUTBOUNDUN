"""Stable original ANOMALIA names. Coordinates and existing IDs are never changed."""
import hashlib
import re

NAMES = (
    'Asterive', 'Valdoria', 'Montbrume', 'Rocheval', 'Norcombe', 'Hautes-Rives',
    'Brumeterre', 'Orsalia', 'Valcendre', 'Claireroche', 'Vespera', 'Bellorage',
    'Boisvermeil', 'Cendreval', 'Lacombre', 'Sylverive', 'Auralis', 'Rocheselve',
    'Valmeris', 'Montserein', 'Aiguebrume', 'Lornac', 'Vallombre', 'Solmara',
    'Terrebrune', 'Castelbrume', 'Lysandre', 'Brisemer', 'Noirval', 'Ventoria',
    'Sablegris', 'Portelune', 'Asterac', 'Calderive', 'Falcombre', 'Primevaux',
)

def place_identity(stable_id, kind='settlement'):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', stable_id):
        raise ValueError('A stable place ID is required')
    match = re.fullmatch(r'settlement_([0-5])_([0-5])', stable_id)
    if match:
        name = NAMES[int(match[1])*6+int(match[2])]
    else:
        digest = hashlib.sha256(stable_id.encode()).hexdigest()
        name = NAMES[int(digest[:8], 16) % len(NAMES)]+' '+digest[:6].upper()
    prefix = {'settlement':'', 'city':'', 'village':'', 'military':'Base militaire de ', 'port':'Port de '}
    if kind not in prefix: raise ValueError('Unsupported place category')
    return dict(id=stable_id, name=prefix[kind]+name, kind=kind)

def settlement_signs(plan):
    result = []
    seen = set()
    for site in plan['settlements']:
        if site['id'] in seen: raise ValueError('Duplicate place identity')
        seen.add(site['id'])
        if site['buildingCount'] < 1: continue
        identity = place_identity(site['id'], 'city' if site['buildingCount']>=140 else 'village')
        # Entrance proposals only. Native terrain/collision validation must approve each one.
        for edge, offset, yaw in [('north',410,90), ('south',-410,-90)]:
            result.append(dict(**identity, signId=site['id']+'-'+edge,
                               east=site['east']+12, north=site['north']+offset, yaw=yaw))
    return result

def sign_candidates(item, buildings=()):
    """Prefer the entrance, then seek a dry reserved corridor inside the same town."""
    direction=1 if item['signId'].endswith('-north') else -1
    centre_east=item['east']-12
    centre_north=item['north']-direction*410
    for distance in [410,375,350,300,250,200,150,100,50,0]:
        for lateral in [12,-12,18,-18]:
            yield dict(east=centre_east+lateral,north=centre_north+direction*distance)
    # A coastal settlement can have dry parcels only on one side of its centre.
    # In that case stay beside a real parcel in this town, never invent a land surface.
    local=[b for b in buildings if b['id'].startswith(item['id']+'_house_')]
    local.sort(key=lambda b: -direction*b['north'])
    for building in local:
        for side in [-1,1]:
            yield dict(east=building['east']+side*(building['width']/2+4.5),north=building['north'])
            yield dict(east=building['east'],north=building['north']+side*(building['depth']/2+4.5))
