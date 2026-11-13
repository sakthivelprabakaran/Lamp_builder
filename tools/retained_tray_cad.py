"""Two integral diagonal long-arm corner latches; prototype, forces unverified."""
import FreeCAD as A,Part
V=A.Vector
MODEL_VERSION='retained-tray-v2'
def build():
 def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
 tray=box(-81.7,-81.7,0,163.4,163.4,3).cut(Part.makeCylinder(16,3))
 latches=[];masks=[]
 for sx in [-1,1]:
  for sy in [-1,1]:
   if sx!=sy:continue
   # Model the +X,+Y corner, then mirror to the other corners.
   def pose(s):
    mat=A.Matrix();mat.A11=sx;mat.A22=sy
    return s.transformGeometry(mat)
   tray=tray.cut(pose(box(64.5,70.5,-1,4.5,9,5)))
   tower=box(60.5,71,2,3,8,21)
   cap=box(60.5,71,21,6.2,8,2)
   beam=box(65.5,71,-5.8,1.2,8,27.8)
   pts=[V(66.5,71,-7),V(68.5,71,-5.8),V(68.5,71,-4.2),V(66.5,71,-4.2)]
   hook=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,8,0))
   latch=tower.multiFuse([cap,beam,hook]);latches.append(pose(latch))
   # Root/cap and tower are deliberately excluded from flexible-contact mask.
   masks.append(pose(box(65.45,70.9,-7.1,3.15,8.2,26.1)))
 tray=tray.multiFuse(latches).removeSplitter()
 return tray,masks,dict(tray_mm=[163.4,163.4,3],latches=2,beam_thickness_mm=1.2,beam_width_mm=8,hook_under_shelf_clearance_mm=.2,free_length_approx_mm=24,extra_loose_lock_parts=0)
