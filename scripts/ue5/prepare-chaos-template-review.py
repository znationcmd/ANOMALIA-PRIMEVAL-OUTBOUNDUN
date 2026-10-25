"""Copy installed licensed Epic template art locally, preserving existing project assets.

No engine assets, binaries or private engine source are uploaded by this workflow.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    source=args.engine_root/'Templates/TemplateResources/Standard/Vehicles/Content'
    choices=[('SportsCar','SKM_SportsCar','SportsCar_AnimBP','SM_SportsCar_Tire'),
             ('OffroadCar','SKM_Offroad','Offroad_AnimBP','SM_Offroad_Tire')]
    selected=next((row for row in choices if all((source/row[0]/(name+'.uasset')).is_file() for name in row[1:])),None)
    if not selected:raise RuntimeError('A complete installed vehicle skeletal/animation/tire set is required')
    family,mesh_name,animation_name,tire_name=selected
    mesh=source/family/(mesh_name+'.uasset')
    raw=mesh.read_bytes()
    strings=raw.decode('latin1')+'\n'+raw.decode('utf-16-le',errors='ignore')
    packages=set(re.findall(r'/Game/[A-Za-z0-9_/]+',strings))
    identities={x for x in packages if x.endswith('/'+family+'/'+mesh_name)}
    if len(identities)!=1: raise RuntimeError('Cannot establish unique installed template package: '+str(sorted(identities)))
    package=identities.pop();prefix=package[:-len(family+'/'+mesh_name)]
    relative=prefix.removeprefix('/Game/').strip('/')
    if '..' in relative.split('/'):raise RuntimeError('Invalid template mount prefix')
    destination=ROOT/'unreal/Content'/relative
    copies=[]
    for folder in ('OffroadCar','SportsCar','PhysicsMaterials'):
        origin=source/folder
        if not origin.is_dir():
            raise RuntimeError('Missing template dependency folder '+folder)
        for path in sorted(origin.rglob('*')):
            if path.is_file():
                target=destination/path.relative_to(source)
                if target.exists() and digest(target)!=digest(path):
                    raise RuntimeError('Existing artist asset preserved: '+str(target))
                copies.append((path,target))
    for path,target in copies:
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copy2(path,target)
    args.output.mkdir(parents=True,exist_ok=True)
    report=dict(state='INSTALLED_TEMPLATE_COPIED_FOR_LOCAL_CHAOS_REVIEW',meshPackage=package,
        referenceTemplate=family,animationClass=prefix+family+'/'+animation_name+'.'+animation_name+'_C',
        tirePackage=prefix+family+'/'+tire_name,
        source='Installed Unreal Engine vehicle template; Epic Unreal Engine license',
        engineFilesModified=False,engineAssetsUploaded=False,
        installedTemplateAssets=[str(p.relative_to(source)) for p in sorted(source.rglob('*.uasset'))],
        files=[dict(path=str(b.relative_to(ROOT)),sha256=digest(b)) for a,b in copies])
    (args.output/'template-source.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
