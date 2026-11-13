"""One-piece friction sleeve prototype; two integrated spring tongues, no loose locks."""
import FreeCAD as A,Part
V=A.Vector
MODEL_VERSION='female-integral-ribs-prototype-v3'
def build(p):
 def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
 def poly(points):return Part.makePolygon([V(*q) for q in points]+[V(*points[0])])
 def xy(points,z,h):return Part.Face(poly([(x,y,z) for x,y in points])).extrude(V(0,0,h))
 c=p['dovetail_clearance'];d=p['dovetail_depth'];head=p['dovetail_head']/2;neck=p['dovetail_neck']/2;front=6+d;h=p['receiver_height'];half=p['socket_mm']/2;o=half+p['socket_wall'];anchor=o-1;w=max(10,head+c+3.7)
 cavity=xy([(4,-head-c),(4+d,-neck-c),(front+1,-neck-c),(front+1,neck+c),(4+d,neck+c),(4,head+c)],2,h+1)
 receiver=box(0,-w,0,front,2*w,h).cut(cavity)
 rx=receiver.copy();rx.translate(V(anchor,0,0));ry=receiver.copy();ry.rotate(V(),V(0,0,1),90);ry.translate(V(0,anchor,0))
 ring=box(-o,-o,0,2*o,2*o,h).cut(box(-half,-half,-1,2*half,2*half,h+2))
 # Open relief behind each cantilever; base remains bonded to the sleeve.
 slot=box(-half-2.05,-5,3,2.8,10,h)
 s2=slot.copy();s2.rotate(V(),V(0,0,1),180)
 ring=ring.multiFuse([rx,ry]).cut(slot.fuse(s2))
 # 2 mm tongue with a shorter free span; 0.25 mm nominal interference per face.
 contact=-p['rod_mm']/2+.25;back=contact-2.0
 outline=[(back,-4,1),(-half-.05,-4,1),(-half-.05,-4,3),(-half+.05,-4,8),(contact-.2,-4,12),(contact,-4,14),(contact,-4,15),(-half-.05,-4,18),(back,-4,18)]
 tongue=Part.Face(poly(outline)).extrude(V(0,8,0));t2=tongue.copy();t2.rotate(V(),V(0,0,1),180)
 return {'female':ring.multiFuse([tongue,t2]).removeSplitter()}
