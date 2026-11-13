"""Actual-mesh assembly animation with explicitly illustrative snap flex."""
import bpy,sys,pathlib,json,math
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[1]
# Reuse exact mesh loader and brand materials from the still-render pipeline.
source=(R/'tools/render_manual_blender.py').read_text().split('def render(name,spec):')[0]
sys.argv=[sys.argv[0]];exec(compile(source,'render-materials','exec'))
O=R/'output/revamp/retained-tray-v2';O.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for mat in mats.values():mat.diffuse_color=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.4;scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_object_outline=True;scene.display.shading.background_type='WORLD';scene.world.color=(.91,.91,.87);scene.render.film_transparent=False;scene.view_settings.view_transform='Standard'
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.fps=12;scene.frame_start=1;scene.frame_end=264
scene.render.image_settings.file_format='FFMPEG';scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264';scene.render.ffmpeg.constant_rate_factor='HIGH';scene.render.filepath=str(O/'LUME_Tray_Assembly.mp4')
bpy.ops.object.camera_add(location=(4,-5,4));cam=bpy.context.object;target=Vector((0,0,.9));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=9.8;scene.camera=cam
# Screen text stays fixed while parts move.
def textobj(name,y,size):
 c=bpy.data.curves.new(name,'FONT');c.size=size;c.align_x='CENTER';c.body=name;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=cam;o.location=(0,y,-3);c.materials.append(mats['sage']);return o
heading=textobj('LUME | Tray assembly',2.4,.185);sub=textobj('Four reinforced seats. Two integral snap hooks.',2.1,.11);foot=textobj('CAD prototype | Illustrative flex; forces and click not simulated',-2.5,.095)
main=[];holders=[];trayparts=[]
spec=data['scenes']['tray-four-post-support-v2']
for i,item in enumerate(spec['objects']):
 ob=make(item,i);ob.location.z-=984;ob.location*=.01;ob.scale*=.01;main.append(ob)
 if item.get('mesh')=='reinforced-bottom-holder':holders.append(ob)
 if item.get('mesh') in ['tray-integral-latches','B22-M10-adapter']:trayparts.append(ob)
def poskeys(o,frames):
 base=o.location.copy()
 for frame,dz in frames:o.location=base+Vector((0,0,dz));o.keyframe_insert('location',frame=frame)
 if o.animation_data:
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
for ob in holders:poskeys(ob,[(1,1.0),(12,1.0),(48,0),(264,0)])
for ob in trayparts:poskeys(ob,[(1,1.1),(66,1.1),(108,.07),(111,.06),(132,.002),(135,0),(264,0)])
def flexkey(o,section=False):
 o.shape_key_add(name='Basis');key=o.shape_key_add(name='Illustrative inward flex')
 for v,k in zip(o.data.vertices,key.data):
  x,y,z=v.co
  if section:
   sx=1;eligible=65.4<=x<=68.6 and 70.9<=y<=79.1 and -7.1<=z<21
  else:
   sx=1 if x>0 else -1;eligible=(x*y>0 and 65.4<=abs(x)<=68.6 and 70.9<=abs(y)<=79.1 and -7.1<=z<21)
  if eligible:
   weight=min(1,max(0,(21-z)/25))**2;k.co.x-=sx*1.1*weight
 return key
tray=next(o for o in main if o.name.startswith('tray-integral-latches'))
key=flexkey(tray)
for f,v in [(1,0),(108,0),(111,1),(132,1),(135,0),(264,0)]:key.value=v;key.keyframe_insert('value',frame=f)
# Switch to actual cutaway meshes for the retention and release explanation.
section=[];sectiontray=None
for i,item in enumerate(data['scenes']['snap-hook-section']['objects']):
 ob=make(item,100+i);ob.location=Vector((-85,-90,-3))*.055;ob.scale*=.055;section.append(ob)
 if item['mesh'].startswith('tray'):sectiontray=ob
for ob in main:
 for f,v in [(1,False),(160,False),(161,True),(264,True)]:ob.hide_render=v;ob.keyframe_insert('hide_render',frame=f)
for ob in section:
 for f,v in [(1,True),(160,True),(161,False),(264,False)]:ob.hide_render=v;ob.keyframe_insert('hide_render',frame=f)
sk=flexkey(sectiontray,True)
for f,v in [(1,0),(188,0),(200,1),(264,1)]:sk.value=v;sk.keyframe_insert('value',frame=f)
poskeys(sectiontray,[(1,0),(204,0),(240,1.1),(264,1.1)])
# The cutaway is viewed square-on, making the hook and underside visible.
cam.location=Vector((.7,-6,2.3));cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
for f in [1,160]:
 cam.location=Vector((4,-5,4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
for f in [161,264]:
 cam.location=Vector((.7,-6,2.3));cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
for fc in cam.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='CONSTANT'
def captions(scene):
 f=scene.frame_current
 if f<=48:heading.data.body='1 | Slide holders onto the posts';sub.data.body='Each holder rests on its upper rail sleeve.'
 elif f<=135:heading.data.body='2 | Lower the tray onto four seats';sub.data.body='Tapered hooks flex inward, then catch below the seats.'
 elif f<=160:heading.data.body='3 | Check both hooks are engaged';sub.data.body='Four seats carry the load. Two hooks resist lifting.'
 elif f<=188:heading.data.body='Close-up | Hook under the seat';sub.data.body='White = integral tray latch. Green = reinforced holder.'
 elif f<=204:heading.data.body='Release | Press BOTH tabs inward';sub.data.body='Two diagonal tabs. No loose locking pieces.'
 else:heading.data.body='Lift the tray with the tabs pressed';sub.data.body='Cutaway shows one of the two release tabs.'
bpy.app.handlers.frame_change_pre.append(captions)
video_path=scene.render.filepath
scene.render.image_settings.file_format='PNG'
for preview in [1,144,176,220]:
 scene.frame_set(preview);captions(scene);scene.render.filepath=str(O/('animation-preview-'+str(preview)+'.png'));bpy.ops.render.render(write_still=True)
scene.render.image_settings.file_format='FFMPEG';scene.render.filepath=video_path
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(O/'LUME_Tray_Assembly.blend'));bpy.ops.render.render(animation=True)
print('FINISHED assembly video',flush=True)
