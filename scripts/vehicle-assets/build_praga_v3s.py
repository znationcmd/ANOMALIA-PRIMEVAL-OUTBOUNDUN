"""Build six original Praga V3S cargo-truck GLBs in Blender."""
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

paint = mat("BodyPaint", (.035,.075,.027), .42, .44)
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

# +X is the front, in metres. Separate driveline and 10 tyres including rear duals.
for y in [-.36,.36]:
    box("Chassis longitudinal",(-.07,y,.86),(6.05,.12,.24),iron,.015)
for x in [-2.96,-2.32,-1.2,0.,1.18,2.4,2.92]:
    box("Chassis crossmember",(x,0,.85),(.15,.86,.19),iron)
for x in [1.96,-1.05,-2.12]:
    cylinder("Portal axle beam",(x,-1.01,.54),(x,1.01,.54),.068,iron)
    for side in [-1,1]:
        for layer in range(4):
            cylinder("Leaf spring", (x-.36+layer*.04,side*.42,.69+layer*.019),
                     (x+.36-layer*.04,side*.42,.69+layer*.019),.014,iron,12)
    for side in [-1,1]:
        for wheel_y in ([.92] if x>0 else [.68,.965]):
            y=wheel_y*side
            name=f"Tyre_{x}_{y}"
            verts=[]
            rings=[(-.145,.37),(-.152,.43),(-.134,.487),(-.085,.52),(.085,.52),(.134,.487),(.152,.43),(.145,.37)]
            for dy,r in rings:
                verts.extend((x+r*cos(2*pi*j/56),y+dy,.53+r*sin(2*pi*j/56)) for j in range(56))
            faces=[(k*56+j,(k+1)%len(rings)*56+j,(k+1)%len(rings)*56+(j+1)%56,k*56+(j+1)%56)
                   for k in range(len(rings)) for j in range(56)]
            mesh(name,verts,faces,black,True)
            cylinder("Steel wheel rim",(x,y-.135,.53),(x,y+.135,.53),.355,iron,40)
            outer=y+side*.149
            cylinder("Wheel hub",(x,outer,.53),(x,outer+side*.037,.53),.16,silver)
            for i in range(8):
                a=i*pi/4
                hx,hz=x+.226*cos(a),.53+.226*sin(a)
                cylinder("Wheel lug",(hx,outer,hz),(hx,outer+side*.017,hz),.017,silver,6)
            for i in range(34):
                a=i*2*pi/34
                for offset in [-.065,.065]:
                    obj=box("Tyre chevron",(x+.518*cos(a),y+offset,.53+.518*sin(a)),(.025,.116,.067),tread,.006)
                    obj.rotation_euler.y=-a
                    obj.rotation_euler.x=offset*4
cylinder("Drive shaft",(-2.2,0,.54),(1.8,0,.72),.052,iron)
box("Fuel tank",(.48,-.58,.70),(.72,.30,.43),iron,.09)
box("Battery box",(.45,.59,.68),(.57,.33,.36),iron,.045)
cylinder("Exhaust",(.68,.55,.54),(-2.8,.58,.51),.033,silver)

# Cab structure, split windscreen, rounded bonnet and exposed grille.
box("Cab floor",(1.30,0,1.23),(1.48,1.88,.18),paint,.06)
box("Rear cab wall",(.60,0,1.92),(.09,1.85,1.31),paint,.035)
profile=[(-.98,2.44),(-.94,2.62),(-.75,2.72),(-.36,2.76),
         (.36,2.76),(.75,2.72),(.94,2.62),(.98,2.44)]
shell("Curved pressed cab roof",[.60,1.89],profile,paint,.037)
for side in [-1,1]:
    y=side*.915
    box("Cab door pressed panel",(1.19,y,1.58),(1.03,.091,.65),paint,.063)
    box("Cab door glass",(1.18,y,2.15),(.84,.026,.43),glass,.06)
    for x in [.66,1.72]:
        box("Cab door pillar",(x,y,2.13),(.095,.10,.70),paint,.028)
    box("Door handle",(1.05,side*.976,1.80),(.22,.055,.045),silver)
    box("Cab step",(1.08,side*.99,1.00),(.72,.31,.065),iron)
    cylinder("Mirror arm",(1.70,side*.94,2.18),(1.79,side*1.20,2.25),.015,silver)
    box("Mirror back",(1.80,side*1.20,2.28),(.054,.14,.22),iron,.04)
    box("Mirror glass",(1.77,side*1.20,2.28),(.012,.116,.18),silver,.03)
    box("Cab seat",(1.12,side*.43,1.52),(.53,.58,.17),seat,.065)
    box("Cab seat back",(.92,side*.43,1.82),(.17,.58,.56),seat,.065)
    windshield=box("Split windscreen",(1.88,side*.43,2.19),(.051,.81,.47),glass,.035)
    windshield.rotation_euler.y=-.16
    cylinder("Windscreen wiper",(1.912,side*.63,2.01),(1.90,side*.29,2.14),.012,iron,12)
box("Windscreen vertical divider",(1.88,0,2.18),(.073,.063,.56),paint)
box("Cab dashboard",(1.72,0,1.77),(.22,1.66,.15),iron,.04)
bpy.ops.mesh.primitive_torus_add(location=(1.50,-.44,1.88),major_radius=.19,minor_radius=.018,
                                 major_segments=40,minor_segments=10)
steering=bpy.context.object
steering.rotation_euler.y=.54
finish(steering,"Steering wheel",black)
cylinder("Steering column",(1.70,-.44,1.68),(1.50,-.44,1.88),.021,iron)
box("Cab front cowl",(1.84,0,1.70),(.23,1.83,.33),paint,.075)
shell("Rounded long hood",[1.91,2.96],[(-.64,1.29),(.64,1.29),(.61,1.79),(.52,1.91),(.31,1.96),(-.31,1.96),(-.52,1.91),(-.61,1.79)],paint,.05)
box("Radiator body",(2.965,0,1.59),(.13,1.17,.62),paint,.07)
box("Radiator recess",(3.037,0,1.59),(.035,1.02,.47),iron,.035)
for i in range(9):
    box("Radiator horizontal grille",(3.064,0,1.39+i*.050),(.055,1.025,.018),silver,.008)
for side in [-1,1]:
    for i in range(10):
        box("Bonnet side vent",(2.02+i*.071,side*.627,1.61),(.039,.012,.096),iron,.005)
    # Rolled semicircular wheel arch, separate from the tyre.
    verts=[]
    for i in range(29):
        a=(-.12+i*(pi+.24)/28)
        for dy,r in [(-.26,.555),(-.26,.59),(.26,.59),(.26,.555)]:
            verts.append((1.96+r*cos(a),side*.90+dy,.53+r*sin(a)))
    faces=[(4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j) for i in range(28) for j in range(4)]
    faces.extend([(0,3,2,1),(112,113,114,115)])
    mesh("Pressed front wing",verts,faces,paint,True)
    cylinder("Headlight housing",(2.66,side*.78,1.28),(2.86,side*.78,1.28),.137,paint,40)
    cylinder("Headlight lens",(2.86,side*.78,1.28),(2.889,side*.78,1.28),.108,lamp,40)
    cylinder("Front indicator",(2.69,side*.99,1.23),(2.74,side*.99,1.23),.056,amber)
    box("Rear light lens",(-3.11,side*.91,1.01),(.034,.20,.103),red)
    box("Mudflap",(-2.62,side*.91,.46),(.055,.39,.45),black,.017)
box("Front bumper",(3.067,0,.97),(.16,2.10,.22),iron,.047)
box("Rear bumper",(-3.05,0,.83),(.20,1.86,.20),iron)
box("Cargo floor",(-1.37,0,1.29),(3.43,2.10,.18),iron)
for y in [-.91,-.65,-.39,-.13,.13,.39,.65,.91]:
    box("Timber cargo floor board",(-1.37,y,1.39),(3.40,.25,.035),wood,.008)
for side in [-1,1]:
    for i in range(4):
        box("Cargo side plank",(-1.37,side*1.048,1.48+i*.13),(3.43,.066,.12),paint,.012)
    for x in [-3.04,-2.25,-1.40,-.56,.30]:
        box("Cargo side stake",(x,side*1.087,1.67),(.084,.068,.59),iron,.011)
        cylinder("Canvas hook",(x,side*1.09,1.84),(x,side*1.12,1.89),.019,silver,12)
for i in range(4):
    box("Rear tailgate board",(-3.10,0,1.48+i*.13),(.078,2.08,.118),paint,.012)
box("Front cargo headboard",(.35,0,1.64),(.094,2.08,.53),paint)
# Curved fabric, compression folds between hoops, separate rolled hems.
x0,x1=-3.14,.38
def cover(x,t):
    arch=sin(t)
    ridge=(.5+.5*cos((x-x0)*2*pi/.70))**8
    pleat=.010*sin(21*t+8*x)+.006*sin(42*t-6*x)
    z=1.91+.99*max(0.,arch)**.61+(.023*ridge+pleat)*arch
    y=(1.095+.012*ridge+.008*sin(37*x+5*t))*cos(t)
    return (x,y,z)
verts=[cover(x0+(x1-x0)*i/96,pi*j/42) for i in range(97) for j in range(43)]
faces=[(i*43+j,i*43+j+1,(i+1)*43+j+1,(i+1)*43+j) for i in range(96) for j in range(42)]
cover_mesh=mesh("Tailored light beige canvas",verts,faces,canvas,True)
solid=cover_mesh.modifiers.new("Fabric thickness","SOLIDIFY")
solid.thickness=.008
for x in [x0,x1]:
    edge=[cover(x,pi*j/42) for j in range(43)]
    curtain=mesh("Canvas end curtain",edge,[tuple(range(len(edge))) if x==x0 else tuple(reversed(range(len(edge))))],canvas)
    curtain.modifiers.new("Curtain thickness","SOLIDIFY").thickness=.008
for side in [-1,1]:
    cylinder("Rolled canvas hem",(x0,side*1.097,1.916),(x1,side*1.097,1.916),.019,canvas)
    for x in [-2.98,-2.55,-2.12,-1.69,-1.26,-.83,-.40,.20]:
        cylinder("Laced canvas tie",(x-.035,side*1.109,1.940),(x+.035,side*1.126,1.843),.008,rope,10)

variants={
    "Vert_Fonce":(.035,.075,.027), "Bleu":(.032,.115,.29), "Beige":(.48,.36,.22),
    "Blanc":(.84,.85,.82), "Rouge_Fonce":(.25,.025,.021), "Gris":(.25,.28,.30),
}
# Join by material to avoid hundreds of Static Mesh imports while retaining slots.
bpy.ops.object.select_all(action="DESELECT")
sources = tuple(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
depsgraph = bpy.context.evaluated_depsgraph_get()
baked = []
for obj in sources:
    evaluated = obj.evaluated_get(depsgraph)
    data = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    data.transform(obj.matrix_world)
    baked.append(bpy.data.objects.new(obj.name + "_baked", data))
for obj in sources:
    bpy.data.objects.remove(obj, do_unlink=True)
for obj in baked:
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
bpy.context.view_layer.objects.active=baked[0]
bpy.ops.object.join()
bpy.context.object.name="Praga_V3S_6x6"
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
bpy.context.object.scale.x = 1.10
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for name,color in variants.items():
    paint.diffuse_color=(*color,1)
    paint.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(*color,1)
    bpy.ops.export_scene.gltf(filepath=str(OUT/f"Praga_V3S_{name}.glb"),export_format="GLB",use_selection=True)
