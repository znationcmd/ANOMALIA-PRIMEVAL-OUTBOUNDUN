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
