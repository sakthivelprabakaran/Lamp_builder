"""Simple v4: split post clamp + male rail cup with one axial fixing."""
import math
import FreeCAD as A,Part
V=A.Vector
MODEL_VERSION='frame-cad-clamp-v4'
def build(p):
 def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
 def fuse(s):return s[0].multiFuse(s[1:]).removeSplitter()
 def poly(pts):return Part.makePolygon([V(*q) for q in pts]+[V(*pts[0])])
 def xy(pts,z,h):return Part.Face(poly([(x,y,z) for x,y in pts])).extrude(V(0,0,h))
 c=p['dovetail_clearance'];d=p['dovetail_depth'];head=p['dovetail_head']/2;neck=p['dovetail_neck']/2;front=6+d;h=p['receiver_height'];half=p['socket_mm']/2;o=half+p['socket_wall'];anchor=o-1;w=max(10,head+c+3.7)
 cavity=xy([(4,-head-c),(4+d,-neck-c),(front+1,-neck-c),(front+1,neck+c),(4+d,neck+c),(4,head+c)],2,h+1)
 receiver=box(0,-w,0,front,2*w,h).cut(cavity)
 rx=receiver.copy();rx.translate(V(anchor,0,0));ry=receiver.copy();ry.rotate(V(),V(0,0,1),90);ry.translate(V(0,anchor,0))
 ring=box(-o,-o,0,2*o,2*o,h).cut(box(-half,-half,-1,2*half,2*half,h+2))
 # One accessible bolt closes the split; captive nut sits outside the post bore.
 ears=box(-o-8,-9,h/2-6,9,18,12)
 female=fuse([ring,rx,ry,ears]).cut(box(-o-9,-1.2,-1,10+p['socket_wall'],2.4,h+2))
 cx=-o-4;cz=h/2;r=2.15
 bore=Part.makeCylinder(r,24,V(cx,-12,cz),V(0,1,0))
 af=7.2;R=af/math.sqrt(3);hexpts=[(cx+R*math.cos(k*math.pi/3),5.6,cz+R*math.sin(k*math.pi/3)) for k in range(6)]
 nut=Part.Face(poly(hexpts)).extrude(V(0,5,0))
 female=female.cut(bore.fuse(nut)).removeSplitter()
 rh=(p['rail_mm']+p['rod_clearance'])/2;ro=rh+2.8;zc=3+rh;top=zc+rh+2.8;placement=front+.6;hx=4+.3-placement;nx=4+d+.3-placement
 tongue=xy([(hx,-head),(nx,-neck),(0,-neck),(0,neck),(nx,neck),(hx,head)],0,p['dovetail_height'])
 cup=box(0,-ro,0,28,2*ro,top).cut(box(3,-rh,3,27,2*rh,2*rh))
 male=fuse([cup,tongue])
 # Recessed head on the tongue face; single screw runs axially into timber end.
 shaft=Part.makeCylinder(2.15,45,V(hx-1,0,zc),V(1,0,0))
 headseat=Part.makeCylinder(4,3,V(hx-.1,0,zc),V(1,0,0))
 male=male.cut(shaft.fuse(headseat)).removeSplitter()
 return {'female':female,'male':male}
