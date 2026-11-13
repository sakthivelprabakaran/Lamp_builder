"""Wedge female sleeve without the legacy cross-pin holes."""
import math
import FreeCAD as A, Part
V=A.Vector
MODEL_VERSION='frame-cad-sleeve-v3'
def build(p):
 def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
 def fuse(s):return s[0].multiFuse(s[1:]).removeSplitter()
 def poly(points):return Part.makePolygon([V(*q) for q in points]+[V(*points[0])])
 def xy(points,z,h):return Part.Face(poly([(x,y,z) for x,y in points])).extrude(V(0,0,h))
 def hole(u,z,r):
  a=V(u-r*math.sqrt(3)/2,-25,z+r/2);b=V(u,-25,z-r);c=V(u+r*math.sqrt(3)/2,-25,z+r/2);t=V(u,-25,z+2*r)
  return Part.Face(Part.Wire([Part.Arc(a,b,c).toShape(),Part.makeLine(c,t),Part.makeLine(t,a)])).extrude(V(0,50,0))
 c=p['dovetail_clearance'];d=p['dovetail_depth'];head=p['dovetail_head']/2;neck=p['dovetail_neck']/2;front=6+d;h=p['receiver_height'];half=p['socket_mm']/2;o=half+p['socket_wall'];anchor=o-1;w=max(10,head+c+3.7)
 cavity=xy([(4,-head-c),(4+d,-neck-c),(front+1,-neck-c),(front+1,neck+c),(4+d,neck+c),(4,head+c)],2,h+1)
 receiver=box(0,-w,0,front,2*w,h).cut(cavity)
 rx=receiver.copy();rx.translate(V(anchor,0,0));ry=receiver.copy();ry.rotate(V(),V(0,0,1),90);ry.translate(V(0,anchor,0))
 ring=box(-o,-o,0,2*o,2*o,h).cut(box(-half,-half,-1,2*half,2*half,h+2))
 # Sliding pressure pad and tapered captive key; final pose has nominal wood contact.
 housing=box(-o-6,-8,0,7,16,h)
 slot=[(-o-6.2,-3.5),(-half+.4,-5.5),(-half+.4,5.5),(-o-6.2,3.5)]
 female=fuse([ring,rx,ry,housing]).cut(xy(slot,-1,h+2)).removeSplitter()
 def postwire(z):
  back=-(half+2.9)+(z-3)*1.2/(h-6)-.05
  return poly([(-o-5.6,-3.2,z),(back,-4.5,z),(back,4.5,z),(-o-5.6,3.2,z)])
 key=Part.makeLoft([postwire(3),postwire(h+3)],True,False)
 key=fuse([key,box(-o-8,-4,h+2,6,8,3)])
 def padwire(z):
  back=-(half+2.9)+(z-3)*1.2/(h-6)
  return poly([(back,-4.2,z),(-p['rod_mm']/2,-4.2,z),(-p['rod_mm']/2,4.2,z),(back,4.2,z)])
 postpad=Part.makeLoft([padwire(3),padwire(h-3)],True,False)
 return {'female':female,'post-wedge':key,'post-pad':postpad}
