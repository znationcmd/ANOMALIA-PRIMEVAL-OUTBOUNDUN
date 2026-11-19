"""Build an original Sprinter T1N GLB in Blender."""
import sys
from math import cos, pi, sin
from pathlib import Path
import bpy
from mathutils import Vector

OUT = Path(sys.argv[sys.argv.index("--") + 1])
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name, color, metal=0., rough=.55):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    pbr = material.node_tree.nodes.get("Principled BSDF")
    pbr.inputs["Base Color"].default_value = (*color, 1)
    pbr.inputs["Metallic"].default_value = metal
    pbr.inputs["Roughness"].default_value = rough
    return material

paint = mat("WhitePaint", (.86,.87,.83), .27, .36)
canvas = mat("LightBeigeCanvas", (.83,.75,.57), 0, .88)
black = mat("Rubber", (.019,.021,.02), 0, .85)
tread = mat("TyreTread", (.027,.028,.025), 0, .89)
iron = mat("Chassis", (.043,.046,.045), .65, .67)
silver = mat("Hardware", (.30,.32,.32), .78, .39)
glass = mat("Windshield", (.055,.12,.14), .27, .20)
seat = mat("Seats", (.13,.085,.048), 0, .82)
wood = mat("CargoBoards", (.19,.132,.074), 0, .84)
lamp = mat("HeadlightGlass", (.79,.83,.83), .32, .2)
red = mat("TailLight", (.44,.028,.017), .14, .29)
amber = mat("Indicator", (.94,.29,.032), .08, .38)
rope = mat("CanvasBindings", (.43,.36,.25), 0, .93)

def finish(obj, name, material, bevel=0.):
    obj.name = name
    obj.data.materials.append(material)
    if bevel:
        edge = obj.modifiers.new("Rounded formed edges", "BEVEL")
        edge.width = bevel
        edge.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj

def box(name, location, size, material, bevel=.025):
    x,y,z=(dimension/2 for dimension in size)
    verts=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
           (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    obj=mesh(name,verts,faces,material)
    obj.location=location
    if bevel:
        edge=obj.modifiers.new("Rounded edges","BEVEL")
        edge.width=bevel
        edge.segments=2
    return obj

def cylinder(name, start, end, radius, material, vertices=24):
    a,b = Vector(start),Vector(end)
    vec = b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=vec.length,location=(a+b)/2)
    obj=bpy.context.object
    obj.rotation_euler = vec.to_track_quat('Z','Y').to_euler()
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices)==4
    return finish(obj,name,material,min(radius*.13,.014))

def mesh(name, vertices, faces, material, smooth=False):
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for face in data.polygons:
        face.use_smooth=smooth
    return obj

def shell(name,xs,profile,material,bevel=0.):
    count=len(profile)
    verts=[(x,y,z) for x in xs for y,z in profile]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    obj=mesh(name, verts, faces, material)
    if bevel:
        mod=obj.modifiers.new("Pressed steel corners","BEVEL")
        mod.width=bevel
        mod.segments=4
        obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return obj


# +X forward. Short van with 3 m axle spacing and low roof.
# The lower edges of each body ring follow the wheel arches.
for x in [-1.48,1.52]:
    cylinder("Axle",(x,-.78,.37),(x,.78,.37),.061,iron)
    for y in [-.78,.78]:
        side=1 if y>0 else -1
        for dy in ([0.,-side*.19] if x<0 else [0.]):
            yc=y+dy
            rings=[(-.099,.235),(-.105,.285),(-.085,.335),(-.055,.352),(.055,.352),
                   (.085,.335),(.105,.285),(.099,.235)]
            verts=[(x+r*cos(j*2*pi/64),yc+w,.36+r*sin(j*2*pi/64))
                   for w,r in rings for j in range(64)]
            faces=[(k*64+j,k*64+(j+1)%64,((k+1)%8)*64+(j+1)%64,((k+1)%8)*64+j)
                   for k in range(8) for j in range(64)]
            mesh("Tyre rounded shoulder",verts,faces,black,True)
            cylinder("Pressed steel rim",(x,yc-.093,.36),(x,yc+.093,.36),.236,silver,48)
            for i in range(8):
                h=i*pi/4
                cylinder("Wheel bolt",(x+.095*cos(h),yc+side*.095,.36+.095*sin(h)),
                         (x+.095*cos(h),yc+side*.114,.36+.095*sin(h)),.011,iron,6)
            for i in range(45):
                t=i*2*pi/45
                o=box("Moulded tread block",(x+.349*cos(t),yc,.36+.349*sin(t)),(.012,.127,.034),tread,.004)
                o.rotation_euler.y=-t
    cylinder("Differential",(x,-.105,.37),(x,.105,.37),.12,iron)

def arch_height(x):
    for axle in (-1.48,1.52):
        if abs(x-axle)<.399:
            return max(.54,.36+(.399**2-(x-axle)**2)**.5)
    return .54

# (x, half-width, roof height), rounded shoulders across each section.
sections=[(-2.39,.86,2.16),(-2.35,.94,2.25),(-2.25,.963,2.32),
          (1.10,.963,2.32),(1.23,.951,2.29),(1.39,.922,2.23),(1.91,.887,1.27),
          (2.17,.875,1.20),(2.43,.821,1.12),(2.47,.76,1.08)]
samples=sorted({x for x,_,_ in sections}|{a+i*.04 for a in (-1.48,1.52) for i in range(-10,11)})
def shape_at(x):
    for (a,w,h),(b,w2,h2) in zip(sections,sections[1:]):
        if a<=x<=b:
            t=(x-a)/(b-a)
            return w+(w2-w)*t,h+(h2-h)*t
    raise ValueError(x)
verts=[]
for x in samples:
    w,h=shape_at(x)
    z=arch_height(x)
    p=[(-w+.079,z),(-w+.022,z+.08),(-w, min(1.05,h-.16)),
       (-w+.011,h-.17),(-w+.061,h-.062),(-w+.150,h-.013),
       (-w+.30,h),(.0,h),(w-.30,h),(w-.15,h-.013),(w-.061,h-.062),
       (w-.011,h-.17),(w,min(1.05,h-.16)),(w-.022,z+.08),(w-.079,z)]
    verts.extend((x,y,zz) for y,zz in p)
n=15
faces=[(i*n+k,(i+1)*n+k,(i+1)*n+(k+1)%n,i*n+(k+1)%n)
       for i in range(len(samples)-1) for k in range(n)]
faces.extend([tuple(range(n-1,-1,-1)),tuple(range((len(samples)-1)*n,len(samples)*n))])
mesh("T1N sculpted van shell",verts,faces,paint,True)

# Thin fitted surfaces for glazing, panel shut lines and model-specific lamps.
wind=[(1.397,-.760,2.144),(1.397,.760,2.144),(1.850,.792,1.365),(1.850,-.792,1.365)]
for name, corners, m in [
    ("Windscreen black seal",[(x+.018,y*1.035,z) for x,y,z in wind],iron),
    ("Tinted laminated windscreen",[(x+.031,y,z) for x,y,z in wind],glass)]:
    panel=mesh(name,corners,[(0,1,2,3),(3,2,1,0)],m)
for side in [-1,1]:
    y=side*.968
    verts=[(.56,y,2.063),(1.35,y,2.057),(1.70,side*.934,1.40),(.56,y,1.40)]
    mesh("Side door window",verts,[(0,1,2,3),(3,2,1,0)],glass)
    for a,b in [((.47,y,.70),(.47,y,2.118)),((.49,y,2.118),(1.33,y,2.118)),
                ((.47,y,.70),(1.08,y,.70))]:
        cylinder("Front door shut line",a,b,.008,iron,10)
    box("Door handle",(.64,side*.979,1.31),(.17,.044,.045),black,.017)
    box("Side protection trim",(-.17,side*.969,.899),(2.36,.043,.10),iron,.030)
    cylinder("Mirror arm",(1.62,side*.899,1.57),(1.57,side*1.143,1.58),.029,black)
    box("Mirror housing",(1.53,side*1.16,1.69),(.131,.234,.247),black,.060)
    box("Mirror glass",(1.459,side*1.16,1.69),(.012,.181,.191),silver,.033)
    # Distinct rounded headlamp lens and amber indicator.
    o=box("Headlamp lens",(2.443,side*.635,1.025),(.105,.39,.178),lamp,.067)
    o.rotation_euler.z=side*.18
    box("Amber indicator",(2.437,side*.770,.955),(.089,.15,.060),amber,.026)
    box("Rear lamp lens",(-2.405,side*.828,1.07),(.065,.120,.34),red,.035)
    box("Rear amber segment",(-2.442,side*.828,1.11),(.015,.112,.063),amber,.010)
    box("Rear reverse lens",(-2.442,side*.828,.988),(.014,.112,.053),lamp,.010)
    cylinder("Rear door seam",(-2.394,side*.756,.735),(-2.394,side*.756,1.956),.006,iron,10)

box("Front moulded bumper",(2.395,0,.693),(.284,1.735,.285),iron,.082)
box("Central lower bumper intake",(2.548,0,.694),(.043,.79,.109),black,.038)
box("Radiator grille black surround",(2.47,0,1.018),(.055,.86,.217),iron,.046)
for i in range(4):
    box("Radiator grille slat",(2.503,0,.951+i*.041),(.028,.793,.016),silver,.006)
for angle in [pi/2,7*pi/6,11*pi/6]:
    cylinder("Three-point star grille badge",(2.527,0,1.040),
             (2.527,.075*cos(angle),1.04+.075*sin(angle)),.009,silver,12)
for i in range(28):
    a,b=i*2*pi/28,(i+1)*2*pi/28
    cylinder("Grille badge ring",(2.529,.077*cos(a),1.04+.077*sin(a)),
             (2.529,.077*cos(b),1.04+.077*sin(b)),.005,silver,8)
for side in [-1,1]:
    cylinder("Windscreen wiper",(1.843,side*.29,1.436),(1.796,side*.60,1.517),.011,black,12)
box("Rear moulded bumper",(-2.367,0,.622),(.252,1.775,.174),iron,.051)
cylinder("Rear centre doors seam",(-2.401,0,.738),(-2.401,0,2.12),.007,iron,12)
box("Rear door pull",(-2.433,.103,1.135),(.049,.161,.060),black,.020)
box("Rear registration recess",(-2.434,0,.906),(.035,.54,.13),iron,.023)
box("Registration blank front",(2.571,0,.803),(.012,.48,.095),paint,.012)
box("Registration blank rear",(-2.457,0,.906),(.011,.48,.095),paint,.012)
# Right slider tracks and seam.
for a,b in [((.39,-.969,.675),(.39,-.969,2.07)),
            ((-.93,-.969,.678),(-.93,-.969,2.07)),
            ((-.93,-.969,2.07),(.39,-.969,2.07)),
            ((-.93,-.969,.678),(.39,-.969,.675))]:
    cylinder("Sliding cargo door seam",a,b,.007,iron,10)
box("Sliding cargo door handle",(.27,-.981,1.21),(.145,.038,.047),black,.016)
box("Sliding door runner",(-1.52,-.969,1.36),(.94,.027,.035),iron,.010)
for y in [-.315,-.105,.105,.315]:
    box("Low roof stiffening rib",(-.58,y,2.324),(3.11,.044,.016),paint,.006)

# Preserve paint, glass and trim as independent material slots in a single UE-ready visual mesh.
sources=tuple(obj for obj in bpy.context.scene.objects if obj.type=="MESH")
bpy.ops.object.select_all(action="DESELECT")
depsgraph=bpy.context.evaluated_depsgraph_get()
baked=[]
for obj in sources:
    data=bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph),depsgraph=depsgraph)
    data.transform(obj.matrix_world)
    baked.append(bpy.data.objects.new(obj.name,data))
for obj in sources:
    bpy.data.objects.remove(obj,do_unlink=True)
for obj in baked:
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
bpy.context.view_layer.objects.active=baked[0]
bpy.ops.object.join()
obj=bpy.context.object
obj.name="Sprinter_416_CDI_2004_L1H1"
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
bpy.ops.export_scene.gltf(filepath=str(OUT/"Sprinter_416_CDI_2004_L1H1_Blanc.glb"),
                         export_format="GLB",use_selection=True)
