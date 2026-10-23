import hashlib,json,pathlib,sys,os
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

ROOT=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parent
OUT=ROOT/'ready_glb';OUT.mkdir(exist_ok=True)
models=[]
only=os.environ.get('ANOMALIA_CONVERT_ONLY')
for group in sorted((ROOT/'extracted').iterdir()):
    metadata={}
    for p in group.glob('packs/*.json'):metadata.update(json.loads(p.read_text()))
    for obj in sorted(group.rglob('*.obj')):
        relative=obj.relative_to(group)
        model_id=group.name+'__'+(obj.parent.name if group.name.startswith('mh_') else obj.stem)
        if only and model_id!=only:continue
        row=dict(id=model_id,sourceId=group.name,original=str(obj.relative_to(ROOT)),unrealImported=False,gameplayVerified=False,rigged=False,qualityApproved=False)
        warnings=[]
        try:
            scene=trimesh.load(obj,force='scene',process=False)
            options={};mhmat=next(obj.parent.glob('*.mhmat'),None)
            if mhmat:
                for line in mhmat.read_text(errors='replace').splitlines():
                    parts=line.split(maxsplit=1)
                    if len(parts)==2 and not parts[0].startswith(('#','//')):options[parts[0]]=parts[1].strip()
            meta=metadata.get(obj.parent.name,{})
            row.update(author=meta.get('author'),individualSource=meta.get('source'),license=meta.get('license','CC0'))
            mhclo=next(obj.parent.glob('*.mhclo'),None)
            headers=[l.strip() for l in mhclo.read_text(errors='replace').splitlines()[:40] if 'license' in l.lower()] if mhclo else []
            row['originalLicenseHeaders']=headers
            row['licenseReviewRequired']=any('agpl' in l.lower() for l in headers)
            def texture(key, fallback=None):
                value=options.get(key,fallback)
                if not value:return None
                p=obj.parent/value
                if not p.exists():
                    warnings.append('Missing texture: '+value);return None
                with Image.open(p) as im:return im.convert('RGBA').copy()
            if mhmat:
                color=[float(x) for x in options.get('diffuseColor','1 1 1').split()]+[float(options.get('opacity','1'))]
                material=PBRMaterial(name=model_id,baseColorFactor=color,baseColorTexture=texture('diffuseTexture'),normalTexture=texture('normalmapTexture'),occlusionTexture=texture('aomapTexture'),metallicFactor=0,roughnessFactor=0.8,doubleSided=options.get('backfaceCull','true').lower()=='false',alphaMode='BLEND' if color[3]<1 else 'OPAQUE')
                warnings.append('Phong to PBR approximation; original mhmat retained')
            elif group.name in ['oga_money_yughues','oga_cannabis_yughues']:
                material=PBRMaterial(name=model_id,baseColorTexture=texture('diffuseTexture','diffuse.tga'),normalTexture=texture('normalmapTexture','normal.tga'),metallicFactor=0,roughnessFactor=0.8,doubleSided=True,alphaMode='MASK',alphaCutoff=0.5)
            else:material=None
            for geometry in scene.geometry.values():
                assert len(geometry.vertices)>0 and len(geometry.faces)>0
                assert np.isfinite(geometry.vertices).all()
                assert geometry.faces.min()>=0 and geometry.faces.max()<len(geometry.vertices)
                if material is not None:
                    uv=getattr(geometry.visual,'uv',None)
                    if uv is None:warnings.append('UV absent')
                    geometry.visual=TextureVisuals(uv=uv,material=material)
            if group.name.startswith('mh_'):
                scene.apply_scale(0.1)
                row['unitConversion']='MakeHuman decimeters to glTF meters (0.1)'
            else:row['unitConversion']='Source coordinates preserved; physical size unverified'
            output=OUT/(model_id+'.glb');output.write_bytes(scene.export(file_type='glb'))
            check=trimesh.load(output,force='scene',process=False)
            assert sum(len(g.faces) for g in check.geometry.values())==sum(len(g.faces) for g in scene.geometry.values())
            row.update(status='CONVERTED_STATIC_REVIEW_REQUIRED',file=str(output.relative_to(ROOT)),bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),triangles=sum(len(g.faces) for g in scene.geometry.values()),warnings=warnings,bounds=check.bounds.tolist())
        except Exception as e:row.update(status='FAILED',error=str(e))
        models.append(row)
        print(json.dumps({k:row[k] for k in ['id','status','error'] if k in row}),flush=True)
if only:
    old=json.loads((ROOT/'conversion-receipt.json').read_text())['models']
    replacements={m['id']:m for m in models}
    models=[replacements.get(m['id'],m) for m in old]
(ROOT/'conversion-receipt.json').write_text(json.dumps(dict(schemaVersion=1,date='2026-10-23',models=models),indent=2))
print(json.dumps({'models':len(models),'converted':sum(m['status'].startswith('CONVERTED') for m in models),'licenseReview':sum(m.get('licenseReviewRequired',False) for m in models)}),flush=True)
