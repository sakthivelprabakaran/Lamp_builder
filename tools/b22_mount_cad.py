"""B22 M10-entry mounting adapter; hardware-specific review prototype."""
import sys
sys.path.insert(0,'/Applications/VibeCAD.app/Contents/Resources/lib')
import FreeCAD as A, Part
import pathlib,json,numpy as np,sys
R=pathlib.Path.cwd();sys.path.insert(0,str(R));from lamp_engine import verify_mesh,write_binary_stl
O=R/'output/revamp/b22-mount';O.mkdir(parents=True,exist_ok=True)
def cyl(r,h,z=0):return Part.makeCylinder(r,h,A.Vector(0,0,z))
tray=Part.makeBox(163.4,163.4,3,A.Vector(-81.7,-81.7,0)).cut(cyl(16,3))
adapter=cyl(15.8,3).fuse(cyl(22.5,3,3)).cut(cyl(5.2,6)).removeSplitter()
checks=[]
def check(name,vol):
 checks.append(dict(name=name,forbidden_overlap_mm3=vol));assert vol<1e-6,(name,vol)
for z in np.arange(0,61,2):
 a=adapter.copy();a.translate(A.Vector(0,0,float(z)));check('adapter insertion z='+str(z),a.common(tray).Volume)
for z in np.arange(-30,31,2):check('M10 envelope through adapter z='+str(z),cyl(5,20,float(z)).common(adapter).Volume)
check('seated adapter / tray',adapter.common(tray).Volume)
assert adapter.distToShape(tray)[0]<1e-6
meshes={}
for name,s in [('B22-tray-32mm',tray),('B22-M10-adapter',adapter)]:
 assert s.isValid() and len(s.Solids)==1
 s.exportStep(str(O/(name+'.step')));assert Part.read(str(O/(name+'.step'))).isValid()
 v,f=s.tessellate(.03);v=np.array([[x.x,x.y,x.z] for x in v]);f=np.array(f);v,idx=np.unique(np.round(v,6),axis=0,return_inverse=True);f=idx[f]
 ok,report=verify_mesh(v,f);assert ok,report;write_binary_stl(O/(name+'.stl'),v,f);meshes[name]=report
(O/'verification.json').write_text(json.dumps(dict(revision='b22-m10-mount-v1-review',checks=checks,meshes=meshes,limits=['M10 hardware envelope only; actual nut/washer/holder sample not verified','No thermal, electrical, load or physical fit certification','Not integrated into existing lamp exports']),indent=2))
print('PASS',len(checks),'sampled interface checks; two watertight meshes',flush=True)
