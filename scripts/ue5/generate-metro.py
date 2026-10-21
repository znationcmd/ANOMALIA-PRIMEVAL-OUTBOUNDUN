"""Original CMD metro lead car and passenger coach; metres/Y-up, no copied train art."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('original_mesh',ROOT/'scripts/ue5/generate-assets-expansion.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def model(driver):
    m=module.Mesh();length=18.;width=2.75;floor=.95;roof=3.8
    m.box((length,.18,width),(0,floor-.09,0),2)
    m.hull([(-9,3.6,3.8,1.25,1.12),(-8.5,3.6,3.92,1.37,1.22),(8.5,3.6,3.92,1.37,1.22),(9,3.6,3.8,1.25,1.12)],8)
    doors=[-5.5,0,5.5]
    for side in [-1,1]:
        z=side*width/2
        # Three open double-door bays per side. No solid box closes the passenger interior.
        ends=[-9,-6.2,-4.8,-.7,.7,4.8,6.2,9]
        for index,(a,b) in enumerate(zip(ends,ends[1:])):
            if index%2:continue
            mid=(a+b)/2;span=b-a
            m.box((span,.55,.065),(mid,floor+.275,z),0)
            m.box((span,.65,.065),(mid,roof-.325,z),8)
            m.box((span-.15,1.6,.018),(mid,2.3,z),4)
            for x in [a+.04,b-.04]:m.box((.08,1.6,.08),(x,2.3,z),8)
            m.box((span,.16,.07),(mid,1.4,z),7)
        for x in doors:
            for dx in [-.7,.7]:m.box((.08,2.35,.09),(x+dx,floor+1.175,z),2)
            m.box((1.48,.08,.1),(x,floor+2.35,z),2)
            # Yellow threshold and paired handrails, visible in the boarding aperture.
            m.box((1.4,.025,.12),(x,floor+.015,z),5)
            m.cylinder((x-.6,1.2,z-side*.12),(x-.6,2.8,z-side*.12),.025)
        for x in [-7.5,-3,2.8,7.5]:
            if driver and x>7:continue
            # Longitudinal passenger benches, leaving the central aisle open.
            m.box((1.7,.12,.46),(x,1.38,side*.98),7)
            m.box((1.7,.6,.08),(x,1.68,side*1.2),7)
        m.cylinder((-7,2.85,side*.75),(7,2.85,side*.75),.025)
    for x in [-6.25,6.25]:
        m.box((2.1,.24,1.65),(x,.55,0),1)
        for dx in [-.65,.65]:
            m.cylinder((x+dx,.36,-.77),(x+dx,.36,.77),.07)
            for side in [-1,1]:m.wheel(x+dx,.36,side*.77,.36,.11)
        for side in [-1,1]:m.box((2.0,.18,.1),(x,.58,side*.94),2)
    for x in [-9,9]:
        # Open gangway for the coach; lead car has a separate glazed driver cab.
        if driver and x>0:
            m.box((.08,.8,2.5),(x,1.35,0),8)
            m.box((.025,1.45,2.35),(x,2.45,0),4)
            m.box((.08,.55,2.5),(x,3.5,0),8)
            m.box((.3,.18,2.2),(8.6,1.9,0),3)
            m.seat(8.1,1.45,-.5);m.steering(8.55,2.1,-.5)
            for z in [-.9,.9]:m.box((.08,.16,.28),(9.08,1.25,z),5)
        else:
            for side in [-1,1]:m.box((.1,2.7,.7),(x,2.3,side*1.02),8)
            m.box((.1,.5,1.4),(x,3.55,0),8)
        m.cylinder((x,.7,0),(x+(1 if x>0 else -1)*.25,.7,0),.08)
    for x in [-3,3]:m.cylinder((x,floor+.1,0),(x,3.4,0),.025)
    return m


def generate(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);models=[]
    for name,driver in [('metro',True),('metro_wagon',False)]:
        data,dims,triangles=model(driver).export(name);file=output/(name+'.glb')
        if file.exists() and file.read_bytes()!=data:raise RuntimeError('Existing metro art preserved: '+str(file))
        if not file.exists():file.write_bytes(data)
        models.append(dict(id=name,kind='vehicle' if driver else 'prop',file=file.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),triangles=triangles,dimensionsMetresYUp=dims,objectPath='/Game/Anomalia/'+('Vehicles/metro/SM_metro' if driver else 'Props/Metro1/SM_metro_wagon'),state='ORIGINAL_GEOMETRY_PROTOTYPE',drivingTested=False,manufacturerReplica=False))
    manifest=dict(schemaVersion=1,author='CMD / ANOMALIA',models=models,notes='Original metro prototype with open boarding bays, aisle, seats, bogies and couplers. No operational doors, passengers or final suspension yet.')
    raw=json.dumps(manifest,indent=2)+'\n';target=output/'manifest.json'
    if target.exists() and target.read_text()!=raw:raise RuntimeError('Existing metro manifest preserved')
    target.write_text(raw);return manifest


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'unreal/SourceAssets/Metro1');args=p.parse_args();print(json.dumps(generate(args.output)))
