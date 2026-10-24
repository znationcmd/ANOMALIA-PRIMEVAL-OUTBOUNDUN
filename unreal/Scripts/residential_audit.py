"""Pure verifier for copied saved-world values; no Unreal wrappers or authoring."""
import math

def close(a,b,tolerance):
    return len(a)==len(b) and all(math.isfinite(x) and math.isfinite(y) and abs(x-y)<=tolerance for x,y in zip(a,b))

def verify(native,items,models,original,layout,surface,envelope):
    if native.get('state')!='NATIVE_RESIDENTIAL_VALUES_COPIED':raise ValueError('Incomplete native snapshot')
    if native.get('packagesSaved') is not False or native.get('terrainModified') is not False:raise ValueError('Audit must not author world')
    # Asset object paths may be package-only in manifests; normalize without changing case.
    def object_path(path):return path if '.' in path.rsplit('/',1)[-1] else path+'.'+path.rsplit('/',1)[-1]
    assets={m['path']:m for m in native['meshes']}
    if len(assets)!=3:raise ValueError('Three distinct meshes required')
    for model in models.values():
        asset=assets[object_path(model['objectPath'])]
        if asset['sourceSha']!=model['sha256'] or not asset['materialsReady']:raise ValueError('Scan metadata or material mismatch')
    if assets[object_path(original['objectPath'])]['originalSha']!=original['sha256']:raise ValueError('Original mesh provenance mismatch')
    actors={a['label']:a for a in native['actors']}
    if len(actors)!=len(native['actors']) or set(actors)!=set(items) or native['houseCount']!=len(items):raise ValueError('Missing or duplicate house identities')
    counts={'upgraded':0,'originalsRetained':0}
    for label,item in items.items():
        actor=actors[label];model=models[layout.model_for(item['id'])]
        asset=assets[object_path(model['objectPath'])]
        target=layout.placement(item,asset['origin'],asset['extent'],surface,envelope)
        if 'ANOMALIA_Inhabited_v1' not in actor['tags'] or actor['materialOverrides']:raise ValueError('Ownership or material changed: '+label)
        if target.get('rejected'):
            expected=original['objectPath'];location=[item['east']*100,-item['north']*100,item['z']*100];scale=[1.,1.,1.];yaw=item['yaw']
            counts['originalsRetained']+=1
        else:
            expected=model['objectPath'];location=target['locationCm'];scale=[target['scale']]*3;yaw=target['yaw']
            if 'ANOMALIA_ResidentialUpgrade_v1' not in actor['tags']:raise ValueError('Upgrade tag missing: '+label)
            counts['upgraded']+=1
        if actor['mesh']!=object_path(expected) or not close(actor['location'],location,.5) or not close(actor['scale'],scale,.0001):raise ValueError('Saved mesh or transform mismatch: '+label)
        if not math.isfinite(actor['yaw']) or abs((actor['yaw']-yaw+180)%360-180)>.01:raise ValueError('Saved rotation mismatch: '+label)
    if counts['upgraded']<4000:raise ValueError('Insufficient verified scanned houses')
    return counts
