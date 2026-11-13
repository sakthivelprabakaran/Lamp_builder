"""Studio-lit print illustrations from exact generated lamp meshes, no AI imagery."""
import bpy,sys,pathlib,json,math,argparse
from mathutils import Vector,Matrix,Euler
from bpy_extras.object_utils import world_to_camera_view
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];parser=argparse.ArgumentParser();parser.add_argument('--only');parser.add_argument('--quick',action='store_true');parser.add_argument('--eevee',action='store_true');a=parser.parse_args(args)
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/pdfs/manual-assets';data=json.loads((OUT/'geometry.json').read_text());meshdata=data['meshes']
def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def rgba(h):return tuple(lin(int(h[i:i+2],16)/255) for i in [0,2,4])+(1,)
def material(name,color,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=rgba(color);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
mats={'sage':material('LUME | sage','727B65',.44),'shade':material('LUME | ivory shade','E8E1D1',.62),'ochre':material('Instruction highlight | wedge','C49C63',.46),'blue':material('Instruction highlight | pressure pad','7498AB',.48),'metal':material('Reference hardware | satin','B2B3AE',.26,.75),'wood':material('Reference timber | warm oak','B59C7B',.6),'floor':material('Studio shadow surface','F6F5EF',.72)}
wood=mats['wood'];nt=wood.node_tree;n=nt.nodes;l=nt.links;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=4;tex.inputs['Detail'].default_value=2;coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(8,8,.25);l.new(coord.outputs['Generated'],mapping.inputs[0]);l.new(mapping.outputs['Vector'],tex.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[0].color=rgba('A38C70');ramp.color_ramp.elements[1].position=.9;ramp.color_ramp.elements[1].color=rgba('C2AA88');l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])

def make(item,idx):
 if 'mesh' in item:
  d=meshdata[item['mesh']];mesh=bpy.data.meshes.new(item['mesh']);mesh.from_pydata(d['v'],[],d['f']);mesh.update();o=bpy.data.objects.new(item['mesh'],mesh);bpy.context.collection.objects.link(o)
 elif 'box' in item:
  bpy.ops.mesh.primitive_cube_add();o=bpy.context.object;o.name='Timber reference';o.dimensions=item['box'];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 elif 'cylinder' in item:
  r,length,axis=item['cylinder'];bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=length);o=bpy.context.object
  # Cylinder spec places the start at xyz; shift to its midpoint.
  if axis=='X':o.rotation_euler[1]=math.pi/2;o.location.x=length/2
  elif axis=='Y':o.rotation_euler[0]=math.pi/2;o.location.y=length/2
  else:o.location.z=length/2
  bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 o.location+=Vector(item['xyz']);o.rotation_euler[2]+=item.get('angle',0);o.rotation_euler[0]+=item.get('rotate_x',0);o.rotation_euler[1]+=item.get('rotate_y',0);o.data.materials.append(mats[item.get('material','sage')]);return o

def render(name,spec):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for mesh in list(bpy.data.meshes):
  if mesh.users==0:bpy.data.meshes.remove(mesh)
 objects=[make(item,i) for i,item in enumerate(spec['objects'])];bpy.context.view_layer.update();bounds=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box];lo=Vector([min(v[k] for v in bounds) for k in range(3)]);hi=Vector([max(v[k] for v in bounds) for k in range(3)]);factor=2/max(hi-lo)
 for o in objects:
  o.location*=factor;o.scale*=factor
  if o.name.startswith('Timber'):
   bevel=o.modifiers.new('Soft timber edges','BEVEL');bevel.width=.14*factor;bevel.segments=3;bevel.limit_method='ANGLE'
  elif o.data.materials[0] in [mats['sage'],mats['ochre'],mats['blue']]:
   bevel=o.modifiers.new('Edge highlight','BEVEL');bevel.width=.045*factor;bevel.segments=2;bevel.limit_method='ANGLE'
   norm=o.modifiers.new('Weighted studio normals','WEIGHTED_NORMAL');norm.keep_sharp=True
 bpy.context.view_layer.update();bounds=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box];lo=Vector([min(v[k] for v in bounds) for k in range(3)]);hi=Vector([max(v[k] for v in bounds) for k in range(3)]);center=(lo+hi)/2;direction=Vector(spec['view']).normalized()
 bpy.ops.object.camera_add(location=center+direction*7);cam=bpy.context.object;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';scene=bpy.context.scene;scene.camera=cam
 width,height=spec['size'];width=1000 if a.quick else 1800;height=round(width*spec['size'][1]/spec['size'][0]);scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100
 right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));us=[(v-center).dot(up) for v in bounds];rs=[(v-center).dot(right) for v in bounds];cam.data.ortho_scale=max(max(rs)-min(rs),(max(us)-min(us))*width/height)*1.15
 center+=right*((max(rs)+min(rs))/2)+up*((max(us)+min(us))/2);cam.location=center+direction*7
 bpy.context.view_layer.update()
 for fit in range(3):
  projected=[world_to_camera_view(scene,cam,v) for v in bounds]
  extent=max(max(abs(p.x-.5),abs(p.y-.5)) for p in projected)
  if extent<=.435:break
  cam.data.ortho_scale*=extent/.435
  bpy.context.view_layer.update()
 # Shadow catcher produces a clean transparent object with a soft contact shadow.
 bpy.ops.mesh.primitive_plane_add(size=200,location=(center.x,center.y,lo.z-.005));floor=bpy.context.object;floor.data.materials.append(mats['floor']);floor.is_shadow_catcher=True
 for loc,power,size in [((-3,-4,6),650,4),((4,1,4),420,3),((-1,4,5),550,3)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(loc));light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='BLENDER_EEVEE_NEXT' if a.eevee else 'CYCLES';
 if a.eevee:
  floor.is_shadow_catcher=False
  if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
  if hasattr(scene.eevee,'use_raytracing'):scene.eevee.use_raytracing=False
 scene.cycles.device='CPU';scene.cycles.samples=12 if a.quick else 40;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.05;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.8,.8,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;scene.render.film_transparent=True;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.filepath=str(OUT/(name+('-quick' if a.quick else '')+'.png'));scene.render.threads_mode='FIXED';scene.render.threads=8
 bpy.ops.render.render(write_still=True)
 points={}
 for key,point in spec.get('points',{}).items():
  c=world_to_camera_view(scene,cam,Vector(point)*factor);points[key]=[c.x,c.y]
 (OUT/(name+'.view.json')).write_text(json.dumps({'points':points,'width':width,'height':height}));print('FINISHED',name,flush=True)
for name,spec in data['scenes'].items():
 if not a.only or name in a.only.split(','):render(name,spec)
