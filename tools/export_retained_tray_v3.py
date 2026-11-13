import sys
sys.path.insert(0,'/Applications/VibeCAD.app/Contents/Resources/lib')
import FreeCAD as A,Part
import sys,json,hashlib,os
import numpy as np
sys.path.insert(0,os.getcwd());sys.path.insert(0,os.getcwd()+'/tools')
from retained_tray_v3_cad import build,MODEL_VERSION
from lamp_engine import verify_mesh,write_binary_stl
out='output/revamp/retained-tray-v3';os.makedirs(out,exist_ok=True)
tray,plain,lock,mask=build();report={'revision':MODEL_VERSION,'parts':{},'physical_verified':False,'slicer_verified':False}
def export(name,s):
 s=s.removeSplitter(); assert s.isValid() and len(s.Solids)==1,(name,s.isValid(),len(s.Solids))
 s.exportStep(out+'/'+name+'.step'); rt=Part.read(out+'/'+name+'.step');assert abs(rt.Volume-s.Volume)<.001
 vs,fs=s.tessellate(.08);vs=np.array([[v.x,v.y,v.z]for v in vs]);fs=np.array(fs)
 v,ix=np.unique(np.round(vs,7),axis=0,return_inverse=True);f=ix[fs];ok,r=verify_mesh(v,f);assert ok,(name,r)
 write_binary_stl(out+'/'+name+'.stl',v,f);np.savez(out+'/'+name+'.npz',v=v,f=f)
 report['parts'][name]={'volume_mm3':s.Volume,'mesh':r,'sha256':hashlib.sha256(open(out+'/'+name+'.stl','rb').read()).hexdigest()}
 return s
tray=export('flat-tray',tray);plain=export('plain-reinforced-holder',plain);lock=export('snap-reinforced-holder',lock)
# diagonal locks; actual four-post layout, seat z0
holders=[];masks=[]
for x,y,angle in [(-97.5,-97.5,0),(-97.5,97.5,270),(97.5,-97.5,90),(97.5,97.5,180)]:
 s=lock.copy();s.rotate(A.Vector(),A.Vector(0,0,1),angle);s.translate(A.Vector(x,y,-52.8));holders.append(s)
 if x*y>0:
  m=mask.copy();m.rotate(A.Vector(),A.Vector(0,0,1),angle);m.translate(A.Vector(x,y,-52.8));masks.append(m)
fixed=Part.makeCompound(holders);flex=Part.makeCompound(masks);rigid=fixed.cut(flex)
rows=[]
for z in np.arange(0,25.01,.5):
 t=tray.copy();t.translate(A.Vector(0,0,float(z)));rows.append({'z_mm':float(z),'forbidden_mm3':t.common(rigid).Volume,'flex_mm3':t.common(flex).Volume})
report['insertion']=rows;report['insertion_pass']=max(r['forbidden_mm3']for r in rows)<1e-6
report['seated_overlap_mm3']=tray.common(fixed).Volume
up=tray.copy();up.translate(A.Vector(0,0,1));report['lift_1mm_overlap_mm3']=up.common(fixed).Volume
# release displace free beam outwards .9mm; conservative rigid translated envelope
released=[]
for i,h in enumerate(holders):
 if i in [0,3]:
  m=masks[0 if i==0 else 1];free=h.common(m);body=h.cut(m);free.translate(A.Vector(.9 if i==0 else -.9,0,0));released.extend([body,free])
 else:released.append(h)
rfix=Part.makeCompound(released);report['release']=[]
for z in np.arange(0,25.01,.5):
 t=tray.copy();t.translate(A.Vector(0,0,float(z)));report['release'].append({'z_mm':float(z),'overlap_mm3':t.common(rfix).Volume})
report['release_pass']=max(r['overlap_mm3']for r in report['release'])<1e-6
report['offset_insertion']=[]
for dx in [-.1,0,.1]:
 for dy in [-.1,0,.1]:
  worst=0
  for z in np.arange(0,12.01,1):
   t=tray.copy();t.translate(A.Vector(dx,dy,float(z)));worst=max(worst,t.common(rigid).Volume)
  report['offset_insertion'].append({'offset_xy_mm':[dx,dy],'max_forbidden_mm3':worst})
report['offset_insertion_pass']=max(r['max_forbidden_mm3']for r in report['offset_insertion'])<1e-6
report['seat_contact_mm2_each']=[196,196,196,196]
report['seat_contact_basis']='14x14mm actual tray overlap on each16x16mm seat; apertures are wholly inward of bearing patch.'
report['source_sha256']=hashlib.sha256(open('tools/retained_tray_v3_cad.py','rb').read()).hexdigest()
report['tolerances']={'nominal_hole_beam_catch_side_clearance_mm':.35,'hook_top_clearance_mm':.3,'release_displacement_mm':.9,'physical_grip_verified':False,'continuous_deformation_simulated':False}
crop=tray.common(Part.makeBox(31,23,5,A.Vector(-83,-83,-1)))
vs,fs=crop.tessellate(.08);np.savez(out+'/tray-corner-crop.npz',v=np.array([[v.x,v.y,v.z]for v in vs]),f=np.array(fs))
json.dump(report,open(out+'/verification.json','w'),indent=2)
print(json.dumps({k:v for k,v in report.items()if k not in ['parts','insertion','release','offset_insertion']}))
