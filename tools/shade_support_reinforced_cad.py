"""Integrated upper rail/shade support, mid guide and closed top grip cap prototypes."""
import FreeCAD as A,Part
from frame_joint_friction_cad import build as rail_sleeve
V=A.Vector
MODEL_VERSION='shade-reinforced-support-v2-integral-tray-latches'
def build(p):
 half=p['socket_mm']/2;o=half+p['socket_wall'];slot=p['slot_mm'];length=p['receiver_length']
 def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
 def ring(z,h):return box(-o,-o,z,2*o,2*o,h).cut(box(-half,-half,z-1,2*half,2*half,h+2))
 def collar(floor):
  a=box(o-1,-slot/2-2.4,0,length+1,slot+4.8,24).cut(box(o,-slot/2,floor,length+2,slot,25));b=a.copy();b.rotate(V(),V(0,0,1),90);parts=[ring(0,24),a,b]
  if floor:parts.append(box(o-1.8,o-1.8,0,8.8,8.8,floor))
  return parts[0].multiFuse(parts[1:]).removeSplitter()
 def grips(s,flip=False):
  def transform(shape):
   if flip:shape.rotate(V(0,0,12),V(1,0,0),180)
   return shape
  gap=box(-half-2.05,-5,3,2.8,10,15);g=gap.copy();g.rotate(V(),V(0,0,1),180);s=s.cut(transform(gap).fuse(transform(g)))
  contact=-p['rod_mm']/2+.25;back=contact-2;points=[(back,-4,1),(-half-.05,-4,1),(-half-.05,-4,3),(-half+.05,-4,8),(contact-.2,-4,12),(contact,-4,14),(contact,-4,15),(-half-.05,-4,18),(back,-4,18)]
  wire=Part.makePolygon([V(*q) for q in points]+[V(*points[0])]);t=Part.Face(wire).extrude(V(0,8,0));t2=t.copy();t2.rotate(V(),V(0,0,1),180);return s.multiFuse([transform(t),transform(t2)]).removeSplitter()
 # The bottom holder's integral standoff seats on the upper sleeve's top face.
 zc=3+(p['rail_mm']+p['rod_clearance'])/2;gap=float(p['upper_rail_gap']);stem=gap+2+zc-p['receiver_height']-1.2
 bottom=collar(1.2);bottom.translate(V(0,0,stem));support=ring(0,stem+.1).fuse(bottom)
 # Preserve the tray seating height; reinforce below it, not above it.
 seat_z=stem+1.2
 ledge=box(o-1.8,o-1.8,seat_z-4,16,16,4)
 # A 45-degree solid gusset backs the ledge and joins both sleeve walls.
 def rect(x,y,z,w):
  pts=[V(x,y,z),V(x+w,y,z),V(x+w,y+w,z),V(x,y+w,z)]
  return Part.makePolygon(pts+[pts[0]])
 gusset=Part.makeLoft([rect(o-1.8,o-1.8,seat_z-20,2),rect(o-1.8,o-1.8,seat_z-4,16)],True)
 pts=[V(o-1,-slot/2-2.4,stem-10),V(o+length,-slot/2-2.4,stem),V(o-1,-slot/2-2.4,stem)]
 rib=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,slot+4.8,0));rib2=rib.copy();rib2.rotate(V(),V(0,0,1),90)
 support=support.multiFuse([ledge,gusset,rib,rib2]).removeSplitter()
 # Relief below the ledge leaves room for the tray hooks at the seated pose.
 pocket=box(o+11.2,o-2,seat_z-8.2,4,16.4,4.2);pocket2=box(o-2,o+11.2,seat_z-8.2,16.4,4,4.2)
 support=support.cut(pocket.fuse(pocket2)).removeSplitter()
 middle=grips(collar(0),True)
 top=grips(collar(0),True).fuse(box(-o,-o,24,2*o+length,2*o+length,p['cap_mm'])).removeSplitter()
 return {'bottom-shade-support':support,'mid-panel-guide':middle,'top-panel-grip-cap':top},dict(upper_rail_gap_mm=gap,rail_center_local_mm=2+zc,standoff_height_mm=stem,panel_bottom_above_sleeve_top_mm=stem+1.2)
