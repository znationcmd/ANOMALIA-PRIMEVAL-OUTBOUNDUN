"""Original, fitted V8 S62-inspired engine-bay geometry for the ANOMALIA E39.

Dimensions are in metres. The export's origin is the existing car's chassis
origin; it is a new 3D asset, not an image or an OEM CAD reproduction.
"""
import bpy,math,sys,argparse,json,hashlib
from pathlib import Path
from mathutils import Vector

args=argparse.ArgumentParser();args.add_argument('--output',required=True)
opt=args.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(opt.output);out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def pos(p):return (p[0],-p[1],p[2])
def mat(name,color,metal=0,rough=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
alloy=mat('Cast aluminium',(.30,.32,.34),.78,.48)
steel=mat('Machined steel',(.43,.46,.49),.85,.28)
black=mat('Engine polymer',(.014,.017,.020),.02,.48)
rubber=mat('EPDM hoses',(.009,.011,.013),0,.75)
darkmetal=mat('Mounts and brackets',(.035,.041,.045),.65,.5)
capblue=mat('Coolant cap blue',(.018,.055,.18),.05,.42)
red=mat('Protected positive terminal',(.28,.009,.006),0,.55)
fluid=mat('Reservoir polymer',(.60,.58,.48),0,.38)
label=mat('Raised markings',(.65,.67,.66),.25,.45)
def finish(o,name,m,bevel=0):
 o.name=name;o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Manufactured edge radii','BEVEL');mod.width=bevel;mod.segments=3
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in o.data.polygons:p.use_smooth=True
 n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');n.keep_sharp=True
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=n.name)
 return o
def box(name,p,size,m,bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos(p));o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,m,bevel)
def cylinder(name,p,radius,depth,m,axis=(0,0,1),vertices=24):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos(p));o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(pos(axis)));return finish(o,name,m,.0015)
def pipe(name,points,r,m):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=10;curve.bevel_depth=r;curve.bevel_resolution=3
 spline=curve.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
 for b,p in zip(spline.bezier_points,points):b.co=pos(p);b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
def bolt(name,p,r=.008,depth=.012):
 return cylinder(name,p,r,depth,steel,vertices=6)

# Original S62-inspired V8 layout: two banks of four cylinders and central intake plenum.
box('V8 wet sump',(1.48,0,.30),(.69,.43,.18),darkmetal,.025)
box('V8 crankcase',(1.47,0,.445),(.69,.49,.22),alloy,.022)
for side in [-1,1]:
 for i in range(4):
  x=1.17+i*.18
  cylinder('V8 cylinder bank '+str(side)+' cylinder '+str(i+1),(x,side*.18,.53),.075,.24,alloy,axis=(0,side*.707,.707))
 head=box('V8 cylinder head '+str(side),(1.46,side*.255,.645),(.78,.21,.14),alloy,.018)
 cover=box('Four-cylinder bank valve cover '+str(side),(1.46,side*.29,.735),(.78,.205,.075),black,.018)
 cover.rotation_euler.x=side*.25
 for i in range(4):
  x=1.17+i*.18
  box('Ignition coil bank '+str(side)+' cylinder '+str(i+1),(x,side*.31,.782),(.08,.09,.024),black,.006)
  pipe('Individual intake runner '+str(side)+' '+str(i+1),[(x,side*.13,.70),(x,side*.08,.75),(x,side*.04,.77)],.031,black)
 for x in [1.12,1.29,1.46,1.63,1.80]:bolt('Bank cover fastener',(x,side*.37,.754),.006,.010)
 pipe('Bank ignition loom '+str(side),[(1.08,side*.39,.71),(1.46,side*.39,.72),(1.84,side*.39,.71)],.011,rubber)
box('S62 style central intake plenum',(1.46,0,.785),(.82,.32,.13),black,.035)
for y in [-.07,-.045,-.02]:box('Plenum raised silver rib',(1.52,y,.853),(.44,.006,.006),label,.002)
for side in [-1,1]:
 cylinder('Twin throttle housing '+str(side),(1.91,side*.15,.72),.059,.085,alloy,axis=(1,0,0))
 pipe('Twin air inlet duct '+str(side),[(1.94,side*.15,.72),(2.01,side*.28,.69),(1.86,side*.47,.64),(1.71,side*.53,.64)],.048,rubber)
 box('Twin air filter housing '+str(side),(1.64,side*.53,.60),(.29,.21,.22),black,.018)
 for i in range(9):box('Airbox cooling rib '+str(side),(1.52+i*.027,side*.53,.714),(.008,.18,.007),black,.002)
 cylinder('Exhaust manifold outlet '+str(side),(1.48,side*.34,.42),.045,.57,darkmetal,axis=(1,0,0))
 cylinder('Oil filler cap',(1.20,-.29,.815),.041,.019,black)
for y,z,r in [(0,.40,.095),(-.20,.52,.055),(.17,.48,.050),(-.02,.63,.065)]:
 cylinder('V8 accessory pulley',(1.91,y,z),r,.035,darkmetal,axis=(1,0,0))
 cylinder('Pulley machined centre',(1.935,y,z),r*.34,.038,steel,axis=(1,0,0))
pipe('Auxiliary belt',[(1.935,0,.305),(1.935,-.20,.465),(1.935,-.20,.575),(1.935,-.02,.695),(1.935,.17,.53),(1.935,.17,.43),(1.935,0,.305)],.009,rubber)
cylinder('V8 alternator',(1.82,-.23,.52),.070,.16,alloy,axis=(1,0,0))
cylinder('Mechanical fan hub',(2.02,0,.54),.052,.065,black,axis=(1,0,0))
for i in range(9):
 angle=i*2*math.pi/9
 blade=box('Cooling fan blade '+str(i),(2.04,.12*math.cos(angle),.54+.12*math.sin(angle)),(.026,.075,.22),black,.006);blade.rotation_euler.x=angle

# Radiator core, header tanks, hoses and reservoirs are retained on the chassis.
box('Radiator fin core',(2.16,0,.50),(.045,1.14,.40),darkmetal,.002)
for i in range(44):box('Radiator fin',(2.19,-.54+i*.025,.50),(.005,.006,.37),alloy,.0005)
box('Radiator upper tank',(2.16,0,.72),(.075,1.18,.045),black,.012)
box('Radiator lower tank',(2.16,0,.28),(.075,1.18,.04),black,.010)
pipe('Upper coolant hose',[(1.83,-.13,.67),(1.96,-.20,.72),(2.12,-.36,.72)],.025,rubber)
pipe('Lower coolant hose',[(1.82,.14,.39),(1.99,.35,.31),(2.13,.43,.30)],.025,rubber)
box('Coolant expansion tank',(1.98,.58,.58),(.15,.13,.25),fluid,.015)
cylinder('Expansion tank filler',(1.98,.58,.72),.034,.035,black)
cylinder('Coolant pressure cap',(1.98,.58,.747),.043,.022,capblue)
box('Washer reservoir',(1.90,-.58,.54),(.20,.14,.21),fluid,.025)
pipe('Washer filler neck',[(1.87,-.58,.62),(1.84,-.58,.71)],.026,fluid)
cylinder('Washer cap',(1.84,-.58,.72),.035,.018,capblue)
cylinder('Brake vacuum booster',(1.02,-.49,.66),.105,.055,black,axis=(1,0,0))
box('Brake fluid reservoir',(1.08,-.49,.77),(.10,.08,.07),fluid,.01)
cylinder('Brake reservoir cap',(1.08,-.49,.814),.026,.012,black)
pipe('Vacuum line',[(1.05,-.40,.70),(1.18,-.32,.70),(1.35,-.23,.68)],.009,rubber)
for side in [-1,1]:
 cylinder('Strut tower',(1.52,side*.65,.64),.095,.11,darkmetal)
 cylinder('Strut mount',(1.52,side*.65,.701),.067,.018,black)
 for j in range(3):
  a=j*2*math.pi/3;bolt('Strut mount nut',(1.52+.048*math.cos(a),side*.65+.048*math.sin(a),.718),.008,.016)
box('Protected jump-start terminal',(1.10,.53,.77),(.075,.055,.055),red,.007)
pipe('Protected power loom',[(1.10,.53,.74),(1.06,.40,.68),(1.09,.20,.58)],.012,rubber)
pipe('Engine breather',[(1.07,-.08,.74),(1.02,.14,.72),(1.08,.30,.59)],.012,rubber)

# Export actual geometry; all bevels, normals and tubes are baked into meshes.
for o in list(bpy.context.scene.objects):
 if o.type in {'CURVE','FONT'}:
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
part_count=len(bpy.context.scene.objects)
for o in bpy.context.scene.objects:o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.ops.object.join();bpy.context.object.name='engine_bay'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.export_scene.gltf(filepath=str(out/'engine_bay.glb'),export_format='GLB',export_apply=True,export_yup=True)
data=(out/'engine_bay.glb').read_bytes()
(out/'manifest.json').write_text(json.dumps({'asset':'ANOMALIA E39 M5 original S62-inspired V8 engine bay','geometry':'Original project modelling, not OEM CAD','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'sourceCoordinateSystem':'car chassis centimetres after glTF import','parts':part_count},indent=2),encoding='utf-8')

