"""Exact B-rep dovetail profiles and cross-holes, tessellated for STL checks."""
import sys
sys.path.insert(0,'/Applications/VibeCAD.app/Contents/Resources/lib')
import FreeCAD as A,Part
import sys,json,pathlib,math,numpy as np
p=json.loads(pathlib.Path(sys.argv[1]).read_text())
V=A.Vector
def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
def fuse(shapes):return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes)>1 else shapes[0]
def profile(points,z,h):return Part.Face(Part.makePolygon([V(x,y,z) for x,y in points]+[V(*points[0],z)])).extrude(V(0,0,h))
def hole(axis,u,z,r=2.1):
 def v(x,y):return V(-2,u+x,z+y) if axis=='X' else V(u+x,-20,z+y)
 left,bottom,right,tip=v(-r*math.sqrt(3)/2,r/2),v(0,-r),v(r*math.sqrt(3)/2,r/2),v(0,2*r)
 wire=Part.Wire([Part.Arc(left,bottom,right).toShape(),Part.makeLine(right,tip),Part.makeLine(tip,left)])
 return Part.Face(wire).extrude(V(45,0,0) if axis=='X' else V(0,40,0))
def female():
 c=p['dovetail_clearance'];depth=p['dovetail_depth'];head=p['dovetail_head']/2;neck=p['dovetail_neck']/2;front=6+depth;width=max(10,head+c+3.7);height=p['receiver_height'];pinx=4+depth*.55;pinz=p['dovetail_height']/2+2
 cavity=profile([(4,-head-c),(4+depth,-neck-c),(front+1,-neck-c),(front+1,neck+c),(4+depth,neck+c),(4,head+c)],2,height+1)
 s=box(0,-width,0,front,width*2,height).cut(cavity)
 return s.cut(Part.makeCompound([hole('Y',pinx,pinz,(p['locking_pin_mm']+.2)/2),hole('X',0,6,p['wood_fixing_hole_mm']/2),hole('X',0,20,p['wood_fixing_hole_mm']/2)])).removeSplitter()
def male():
 half=(p['rail_mm']+p['rod_clearance'])/2;o=half+2.8;depth=p['dovetail_depth'];front=6+depth;placement=front+.6;headx=4+.3-placement;neckx=4+depth+.3-placement;head=p['dovetail_head']/2;neck=p['dovetail_neck']/2;top=p['rail_mm']+5
 s=fuse([box(0,-o,0,23,2*o,3),box(0,-o,0,3,2*o,top),box(3,-o,0,20,2.8,p['rail_mm']+3.6),box(3,half,0,20,2.8,p['rail_mm']+3.6),profile([(headx,-head),(neckx,-neck),(0,-neck),(0,neck),(neckx,neck),(headx,head)],0,p['dovetail_height'])])
 return s.cut(Part.makeCompound([Part.makeCylinder(p['wood_fixing_hole_mm']/2,top+2,V(x,0,-1)) for x in [9,17]]+[hole('Y',4+depth*.55-placement,p['dovetail_height']/2,(p['locking_pin_mm']+.2)/2)])).removeSplitter()

from frame_joint_cad import build
output=pathlib.Path(sys.argv[2]);key=output.stem.rsplit('-',1)[1]
for name,shape in build(p).items():
 if not shape.isValid():raise ValueError('Invalid dovetail solid '+name)
 v,f=shape.tessellate(.04);v=np.array([[a.x,a.y,a.z] for a in v],dtype='float32');f=np.asarray(f,dtype='int32');v,inv=np.unique(np.round(v,6),axis=0,return_inverse=True);f=inv[f]
 np.savez(output.with_name(name+'-'+key+'.npz'),v=v,f=f)
