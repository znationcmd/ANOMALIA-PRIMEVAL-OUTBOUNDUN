"""Author an original metal road sign in metres, glTF Y-up. No downloaded artwork."""
import importlib.util
import json
import math
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('sign_geometry',Path(__file__).with_name('settlement_roads.py'))
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)

def build():
    mesh=geometry.Geometry()
    def triangle(a,b,c,material):
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        length=math.sqrt(sum(x*x for x in n))
        if length<1e-12: raise ValueError('Degenerate sign geometry')
        group=mesh.groups[material];base=len(group['positions'])//3
        for p in (a,b,c):
            group['positions'].extend(p);group['normals'].extend(x/length for x in n);group['uv'].extend((p[0],p[1]))
        group['indices'].extend((base,base+1,base+2))
    def ring(width,height,radius,z):
        points=[]
        for cx,cy,start in [(width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,90),(-width/2+radius,-height/2+radius,180),(width/2-radius,-height/2+radius,270)]:
            for i in range(9):
                a=math.radians(start+i*90/8)
                points.append((cx+radius*math.cos(a),2+cy+radius*math.sin(a),z))
        return points
    outer_front=ring(2.8,.65,.09,.025);inner_front=ring(2.7,.55,.06,.027)
    outer_back=ring(2.8,.65,.09,-.025);inner_back=ring(2.7,.55,.06,-.027)
    for i in range(len(outer_front)):
        j=(i+1)%len(outer_front)
        for outer,inner,reverse in [(outer_front,inner_front,False),(outer_back,inner_back,True)]:
            tri=[(outer[i],outer[j],inner[i]),(inner[i],outer[j],inner[j])]
            for a,b,c in tri: triangle(a,c,b,1) if reverse else triangle(a,b,c,1)
            centre=(0,2,inner[i][2])
            triangle(centre,inner[j],inner[i],0) if reverse else triangle(centre,inner[i],inner[j],0)
        triangle(outer_front[i],outer_back[i],outer_front[j],2)
        triangle(outer_back[i],outer_back[j],outer_front[j],2)
    def cylinder(x,y0,y1,z,radius,segments=24):
        for i in range(segments):
            a=i*2*math.pi/segments;b=(i+1)*2*math.pi/segments
            p=(x+radius*math.cos(a),y0,z+radius*math.sin(a));q=(x+radius*math.cos(b),y0,z+radius*math.sin(b))
            r=(p[0],y1,p[2]);s=(q[0],y1,q[2])
            triangle(p,r,q,2);triangle(q,r,s,2)
            triangle((x,y0,z),p,q,2);triangle((x,y1,z),s,r,2)
    for x in [-.9,.9]:
        cylinder(x,0,2.15,-.075,.032)
        cylinder(x,0,.025,-.075,.12)
        # Visible small fastener caps at top and bottom of each mounting line.
        for y in [1.8,2.2]: cylinder(x,y-.012,y+.012,.038,.016,12)
    raw=mesh.glb('ANOMALIA_Original_Road_Sign')
    json_length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+json_length])
    materials=[('Reflective enamel',[.92,.94,.91,1],.2,.28),('Red border',[.55,.015,.012,1],.15,.32),('Galvanized steel',[.38,.42,.45,1],.9,.38)]
    doc['materials']=[dict(name=name,pbrMetallicRoughness=dict(baseColorFactor=color,metallicFactor=metal,roughnessFactor=rough)) for name,color,metal,rough in materials]
    doc['asset']['generator']='Original ANOMALIA road sign with rounded plate, double face, posts, feet and fasteners'
    header=json.dumps(doc,separators=(',',':')).encode();header+=b' '*(-len(header)%4)
    binary_chunk=raw[20+json_length:]
    return struct.pack('<III',0x46546c67,2,20+len(header)+len(binary_chunk))+struct.pack('<II',len(header),0x4e4f534a)+header+binary_chunk

if __name__=='__main__':
    output=Path(__file__).resolve().parents[2]/'unreal/SourceAssets/OriginalSigns_v1/sign.glb'
    output.parent.mkdir(parents=True,exist_ok=True)
    data=build()
    if output.exists() and output.read_bytes()!=data: raise SystemExit('Existing edited source preserved')
    output.write_bytes(data)
    print(f'Authored original sign: {output} ({len(data)} bytes)')
