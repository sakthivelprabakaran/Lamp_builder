"""Flat tray and upward holder-integral snap tongues; PETG prototype."""
import FreeCAD as A, Part
V=A.Vector
MODEL_VERSION='retained-tray-v3-holder-integral-tongues'
def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
def build():
 tray=box(-81.7,-81.7,0,163.4,163.4,3).cut(Part.makeCylinder(16,3))
 import frame_lamps
 namespace={}
 source=open('tools/shade_support_reinforced_cad.py').read().replace('support=support.cut(pocket.fuse(pocket2)).removeSplitter()','support=support.removeSplitter()')
 exec(compile(source,'unrelieved_support','exec'),namespace)
 p=frame_lamps.resolve(dict(standing=True,width=220,height=1371.6))
 old=namespace['build'](p)[0]['bottom-shade-support']
 # Model corner (-97.5,-97.5), whose local shelf extends toward centre.
 # Tongue x32.5..34.1, corresponding global x -65..-63.4.
 # Make the stronger seat support grow from sleeve with a sloped lower face.
 def rect(x,y,z,w,d):
  pts=[V(x,y,z),V(x+w,y,z),V(x+w,y+d,z),V(x,y+d,z)]
  return Part.makePolygon(pts+[pts[0]])
 brace=Part.makeLoft([rect(13.8,13.8,21.8,2,2),rect(13.8,13.8,43.8,20.3,12.7)],True)
 # 1.6mm beam, 15.5mm free span above 3mm solid root; top ramp feeds aperture.
 beam=box(32.5,18.5,43.8,1.6,8,16.8)
 pts=[V(32.5,18.5,55.7),V(32.1,18.5,56.1),V(31.7,18.5,56.1),V(31.7,18.5,57.3),V(32.5,18.5,60.6)]
 hook=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,8,0))
 locked=old.multiFuse([brace,beam,hook]).removeSplitter()
 mask=box(31.6,18.4,46.8,2.6,8.2,14)
 # Apertures at all corners maintain rotation symmetry and the plate prints flat.
 for angle in [0,90,180,270]:
  catching=angle in [0,180]
  hole=box(-65.35 if catching else -66.1,-79.4,-1,3.15 if catching else 3.9,8.8,5)
  hole.rotate(V(),V(0,0,1),angle)
  tray=tray.cut(hole)
 return tray,old,locked,mask
