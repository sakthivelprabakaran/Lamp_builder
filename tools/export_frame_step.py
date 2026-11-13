"""Construct genuine FreeCAD B-rep solids; STEP has no parametric feature history.
Run with installed VibeCAD bundled Python. Regenerate using params.json/script.
"""
import sys,pathlib,json,math,zipfile
sys.path.insert(0,'/Applications/VibeCAD.app/Contents/Resources/lib')
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import FreeCAD as A,Part
import sys,pathlib,json,math,zipfile,numpy as np,frame_lamps as m
params=json.loads(pathlib.Path(sys.argv[1]).read_text());p=m.resolve(params);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
V=A.Vector
def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
def fuse(shapes):return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes)>1 else shapes[0]
def profile(points,z,h):return Part.Face(Part.makePolygon([V(x,y,z) for x,y in points]+[V(*points[0],z)])).extrude(V(0,0,h))
def hole(axis,u,z,r=2.1):
 def v(x,y):return V(-2,u+x,z+y) if axis=='X' else V(u+x,-20,z+y)
 left,bottom,right,tip=v(-r*math.sqrt(3)/2,r/2),v(0,-r),v(r*math.sqrt(3)/2,r/2),v(0,2*r)
 wire=Part.Wire([Part.Arc(left,bottom,right).toShape(),Part.makeLine(right,tip),Part.makeLine(tip,left)])
 return Part.Face(wire).extrude(V(45,0,0) if axis=='X' else V(0,40,0))
def panel(segment):
 v,f,_=m.panel(p,segment);top=f[np.all(np.isclose(v[f,2],p['panel_mm']),axis=1)]
 edges=np.concatenate([top[:,[0,1]],top[:,[1,2]],top[:,[2,0]]]);_,ix,counts=np.unique(np.sort(edges,axis=1),axis=0,return_index=True,return_counts=True);boundary=edges[ix[counts==1]];nextedge={int(a):int(b) for a,b in boundary};loops=[]
 while nextedge:
  start=next(iter(nextedge));loop=[start];cur=nextedge.pop(start)
  while cur!=start:loop.append(cur);cur=nextedge.pop(cur)
  pts=v[loop,:2];area=np.sum(pts[:,0]*np.roll(pts[:,1],-1)-pts[:,1]*np.roll(pts[:,0],-1))/2;loops.append((abs(area),pts))
 loops.sort(key=lambda x:-x[0]);wires=[]
 for _,pts in loops:wires.append(Part.makePolygon([V(float(x),float(y),0) for x,y in pts]+[V(float(pts[0,0]),float(pts[0,1]),0)]))
 return Part.Face(wires).extrude(V(0,0,p['panel_mm']))
def collar(through=False,coupon=False):
 half=p['socket_mm']/2;o=half+p['socket_wall'];h=8 if coupon else 24;ring=box(-o,-o,0,2*o,2*o,h).cut(box(-half,-half,-1,2*half,2*half,h+2))
 if coupon:return ring
 slot=p['slot_mm'];length=p['receiver_length'];floor=0 if through else 1.2
 arms=[box(o-1,-slot/2-2.4,0,length+1,slot+4.8,24).cut(box(o,-slot/2,floor,length+2,slot,25)),box(-slot/2-2.4,o-1,0,slot+4.8,length+1,24).cut(box(-slot/2,o,floor,slot,length+2,25))]
 wire=p['cable_mm']+.6;arms.append(box(-o-wire-2.4,-wire/2-2.4,0,wire+3.4,wire+4.8,24).cut(box(-o-wire-3,-wire/2,-1,wire+3,wire,26)))
 if not through:arms.append(box(o-1.8,o-1.8,0,8.8,8.8,1.2))
 return fuse([ring]+arms)
from frame_joint_cad import build,MODEL_VERSION
joint_parts=build(p)
def cached(name,create):
 path=out/(name+'.step')
 return Part.read(str(path)) if '--reuse-static' in sys.argv and path.exists() else create()
parts={f'panel-{i+1}':cached(f'panel-{i+1}',lambda:panel(i)) for i in range(p['segments'])};parts.update({'corner-bottom':cached('corner-bottom',lambda:collar()),'corner-through':cached('corner-through',lambda:collar(True)),'rod-fit-coupon':cached('rod-fit-coupon',lambda:collar(coupon=True))})
length=min(220,p['height']/math.ceil(p['height']/220));inside=p['cable_mm']+.6;w=inside+4.8
parts['cable-guide']=fuse([box(0,-w/2,0,length,w,1.2),box(0,-w/2,1.2,length,2.4,p['cable_mm']+.8),box(0,inside/2,1.2,length,2.4,p['cable_mm']+.8)]);parts['cable-cover']=box(0,0,0,length,w,1.2)
half=p['socket_mm']/2;o=half+p['foot_wall'];parts['foot-cap']=box(-o,-o,0,2*o,2*o,p['foot_height']).cut(box(-half,-half,p['foot_floor'],2*half,2*half,p['foot_height']))
w=p['panel_width'];tray=box(0,0,0,w,w,3);holes=[box(w/2-2,w/2+9,-1,4,6,5),box(w/2-2,w/2-15,-1,4,6,5),box(w/2-2,-1,-1,4,13,5)]
if p['light_type'] in ('B22','E27'):holes.append(Part.makeCylinder(p['holder_bore']/2,5,V(w/2,w/2,-1)))
parts['light-tray']=tray.cut(Part.makeCompound(holes));o=(p['socket_mm']+2*p['socket_wall']+18)/2;parts['top-retaining-cap']=box(-o,-o,0,2*o,2*o,p['cap_mm']).cut(Part.makeCylinder(2.2,p['cap_mm']+2,V(0,0,-1)))
s=fuse([box(0,0,0,60,30,2)]+[Part.makeCylinder(6,8,V(x,15,2)) for x in [10.8,30,49.2]]);parts['strain-relief']=s.cut(Part.makeCompound([box(x-1.6,y-1.6,-1,3.2,3.2,12) for x in [8,52] for y in [6,24]]))
if p['standing'] and p['rails']:parts.update({'dovetail-'+n:shape for n,shape in joint_parts.items()})
reports={}
for name,s in parts.items():
 if not s.isValid() or not s.Solids or s.Volume<=0:raise ValueError('Invalid solid '+name)
 if not ('--reuse-static' in sys.argv and (out/(name+'.step')).exists() and not name.startswith('dovetail')):s.exportStep(str(out/(name+'.step')))
 loaded=Part.read(str(out/(name+'.step')))
 if not loaded.isValid() or abs(loaded.Volume-s.Volume)>max(1e-4,s.Volume*1e-6):raise ValueError('STEP roundtrip mismatch '+name)
 reports[name]={'valid':True,'solids':len(s.Solids),'volume_mm3':s.Volume,'bounds_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength],'step_roundtrip_valid':True}
 print('STEP',name,flush=True)

# Named assembly solids; unfinished light hardware/cable installation excluded.
objects=[];assembly_names=[]
def place(name,shape,angle=0,xyz=(0,0,0),axis=V(0,0,1)):
 s=shape.copy();s.rotate(V(0,0,0),axis,angle);s.translate(V(*xyz));objects.append(s);assembly_names.append(name);return s

q=p['post_center'];rail_s=[];receiver_s=[];shoe_s=[];post_s=[];panel_s=[];collar_s=[];foot_s=[]
for x in [-q,q]:
 for y in [-q,q]:
  post_s.append(place('25 mm wood post',box(-p['rod_mm']/2,-p['rod_mm']/2,p['foot_floor'],p['rod_mm'],p['rod_mm'],p['height']-p['foot_floor']),xyz=(x,y,0)))
  if p['standing']:foot_s.append(place('PETG foot cap',parts['foot-cap'],xyz=(x,y,0)))
  # XY rotation points the two receivers inward.
  angle=0 if x<0 and y<0 else 90 if x>0 and y<0 else 180 if x>0 else 270
  for j in range(p['segments']+1):
   z=p['panel_bottom']-1.2 if j==0 else p['height']-24 if j==p['segments'] else p['panel_bottom']+j*p['segment_height']-12
   collar_s.append(place('Bottom shade collar' if j==0 else 'Through shade collar',parts['corner-bottom' if j==0 else 'corner-through'],angle,(x,y,z)))
  place('Top retaining cap',parts['top-retaining-cap'],xyz=(x,y,p['height']))
if p['standing'] and p['rails']:
 for ins in m.joint_instances(p,legacy=True):
  shape=place('Printed '+ins['part'],parts['dovetail-'+ins['part']],math.degrees(ins['angle']),ins['xyz'])
  if ins['part']=='female':receiver_s.append(shape)
  elif ins['part']=='male':shoe_s.append(shape)
for side in range(4):
 for segment in range(p['segments']):
  s=parts[f'panel-{segment+1}'].copy();s.rotate(V(),V(1,0,0),90);s.translate(V(-p['panel_width']/2,-q+p['panel_mm']/2,p['panel_bottom']+segment*p['segment_height']));panel_s.append(place('Shade panel',s,side*90))
place('Light support tray',parts['light-tray'],xyz=(-p['panel_width']/2,-p['panel_width']/2,p['panel_bottom']))
if p['standing']:
 for r in m.standing_structure(p)['wood_rails']:
  a=np.array(r['start']);b=np.array(r['end']);length=np.linalg.norm(b-a);s=box(0,-p['rail_mm']/2,-p['rail_mm']/2,length,p['rail_mm'],p['rail_mm']);angle=0 if b[0]>a[0] else 90;rail_s.append(place('Proposed wood rail',s,angle,tuple(a)))
Part.makeCompound(objects).exportStep(str(out/'assembly.step'));(out/'assembly-components.json').write_text(json.dumps(assembly_names,indent=2))
# Common-volume tests on nominal B-reps, omitting unresolved fasteners/light hardware.
checks=[]
for title,aa,bb in [('post/collar',post_s,collar_s),('post/foot',post_s,foot_s),('panel/collar',panel_s,collar_s),('panel/post',panel_s,post_s),('dovetail pair',receiver_s,shoe_s),('rail/shoe',rail_s,shoe_s),('rail/post',rail_s,post_s)]:
 maximum=0
 for a in aa:
  for b in bb:
   ba,bbx=a.BoundBox,b.BoundBox
   if min(ba.XMax,bbx.XMax)-max(ba.XMin,bbx.XMin)<=1e-7 or min(ba.YMax,bbx.YMax)-max(ba.YMin,bbx.YMin)<=1e-7 or min(ba.ZMax,bbx.ZMax)-max(ba.ZMin,bbx.ZMin)<=1e-7:continue
   proxy=box(ba.XMin,ba.YMin,ba.ZMin,ba.XLength,ba.YLength,ba.ZLength) if title.startswith('panel/') else a
   volume=proxy.common(b).Volume
   if volume>1e-5 and title.startswith('panel/'):volume=a.common(b).Volume
   maximum=max(maximum,volume)
 print('Checked',title,maximum,flush=True)
 checks.append({'interface':title,'maximum_overlap_mm3':maximum,'passed_nominal_volume':maximum<1e-5})
reports['model_version']=MODEL_VERSION;reports['assembly_interfaces']=checks;reports['limitations']=['STEP is B-rep geometry, not a retained parametric feature history; regenerate using inputs and script.','Panel holes use original polygon profiles extruded as B-reps; not STL triangle wrappers.','Wedge-tightened female sleeves and axially fixed male rail cups. Hardware, wedge grip, PETG creep, lift-out retention, actual holder and shade-collar fixation remain unvalidated.','Nominal common-volume checks do not validate physical fit, load, heat or full motion paths.']
(out/'cad-validation.json').write_text(json.dumps(reports,indent=2));(out/'params.json').write_text(json.dumps(p,indent=2))
with zipfile.ZipFile(out/'cad-parts.zip','w',zipfile.ZIP_DEFLATED) as z:
 for path in out.iterdir():
  if path.suffix in ['.step','.FCStd','.json']:z.write(path,path.name)
 z.write(__file__,'regenerate.py')
 for module in ['frame_lamps.py','lamp_engine.py','print_geometry.py']:z.write(pathlib.Path(__file__).resolve().parents[1]/module,module)
 for module in ['frame_joint_cad.py','frame_joint_clamp_cad.py','frame_joint_wedge_cad.py']:z.write(pathlib.Path(__file__).with_name(module),module)
print(out/'cad-parts.zip',flush=True)
