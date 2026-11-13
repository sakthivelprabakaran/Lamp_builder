"""Dimensioned sections of actual NumPy connector/cap meshes; nominal fit checks."""
import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import frame_lamps as m,numpy as np
from PIL import Image,ImageDraw,ImageFont
root=pathlib.Path(__file__).resolve().parents[1];p=m.resolve(dict(standing=True,exposed_leg_height=1066.8));out=root/'output/revamp'
def segments(v,f,z):
 lines=[]
 for t in v[f]:
  points=[]
  for a,b in zip(t,np.roll(t,-1,axis=0)):
   if (a[2]<z<b[2]) or (b[2]<z<a[2]):points.append(a[:2]+(b[:2]-a[:2])*(z-a[2])/(b[2]-a[2]))
  if len(points)==2:lines.append(points)
 return np.array(lines)
collar=segments(*m.connector(p),10);foot=segments(*m.foot_cap(p),10)
im=Image.new('RGB',(1200,1060),'#f5f4ec');d=ImageDraw.Draw(im);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',15);title=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',27)
d.text((24,18),'LUME / 25 mm post — assembly section review',font=title,fill='#394331');d.text((24,55),'Mesh sections in plan; dimensions in mm. Nominal clearance is not measured print fit.',font=font,fill='#656b5c')
def plot(lines,center,scale):
 for line in lines:
  uv=line*scale+center;d.line([tuple(x) for x in uv],fill='#56624b',width=2)
def rect(x,y,w,h,center,scale,color):
 a=np.array([x,y])*scale+center;b=np.array([x+w,y+h])*scale+center;d.rectangle((*a,*b),fill=color)
for ix,(name,lines) in enumerate([('A / Collar + two panel receivers',collar),('B / Foot cap + timber',foot)]):
 cx=300+600*ix;cy=305;scale=7;center=np.array([cx,cy]);d.text((30+600*ix,100),name,font=font,fill='#394331');rect(-12.5,-12.5,25,25,center,scale,'#b29a79');plot(lines,center,scale)
 if ix==0:
  start=p['receiver_back']+.2;rect(start,-p['panel_mm']/2,12,p['panel_mm'],center,scale,'#dfa772');rect(-p['panel_mm']/2,start,p['panel_mm'],12,center,scale,'#dfa772');plot(lines,center,scale)
  text=['Timber 25 × 25; nominal socket 25.6','Panel 2.0 centered in slot 2.4: 0.2 each side','Insertion 8.8; back clearance 0.2','Two panels remain separated by timber corner.']
 else:text=['Timber 25 × 25; nominal socket 25.6','PETG wall 3.0; socket height 17.6','Closed floor 2.4; overall height 20.0','Floor/rod contact intended; side clearance 0.3.']
 for j,line in enumerate(text):d.text((30+600*ix,480+j*24),line,font=small,fill='#656b5c')
# Vertical interface diagrams are dimensioned layout sections, not mesh Boolean tests.
x0=60;y0=920;scale=3
# panel floor, panel, cap schematic
rect(0,0,50,1.2,np.array([x0,y0]),scale,'#56624b');rect(8,-30,2,30,np.array([x0,y0]),scale,'#dfa772');d.text((30,615),'C / Bottom support + tray (layout section)',font=font,fill='#394331');d.text((30,650),'Panel underside seats on 1.2 mm receiver floor.',font=small,fill='#656b5c');d.text((30,675),'Tray bears on inward shelves; nominal corner bearing 6.8 × 6.8.',font=small,fill='#656b5c');d.text((30,700),'BOTTOM COLLAR HEIGHT FIXATION IS NOT YET DESIGNED.',font=small,fill='#9a5737')
d.text((630,615),'D / Seam + removable top stop (layout section)',font=font,fill='#394331');d.text((630,650),'Two 152.4 mm panels: flush face contact, no overlapping volume.',font=small,fill='#656b5c');d.text((630,675),'Top collar ends at wood end; 3 mm cap bears above it.',font=small,fill='#656b5c');d.text((630,700),'Cap hole 4.4; fastener, vertical play and removal path pending.',font=small,fill='#9a5737')
rect(0,-30,2,30,np.array([740,880]),scale,'#dfa772');rect(0,0,2,30,np.array([740,880]),scale,'#dfa772');rect(-3,-32,16,2,np.array([740,880]),scale,'#56624b');d.text((760,870),'seam',font=small,fill='#656b5c');d.text((820,790),'top retaining cap',font=small,fill='#656b5c')
d.text((24,1015),'A/B: actual mesh boundaries. C/D: nominal layout sections. Full solid interference and motion tests remain pending.',font=small,fill='#656b5c');im.save(out/'standing-assembly-sections.png')
checks=dict(rod_mm=p['rod_mm'],socket_nominal_mm=p['socket_mm'],rod_side_clearance_mm=(p['socket_mm']-p['rod_mm'])/2,panel_mm=p['panel_mm'],slot_nominal_mm=p['slot_mm'],panel_side_clearance_mm=(p['slot_mm']-p['panel_mm'])/2,panel_centering_fix='Panel thickness now centered on receiver plane; previous one-sided placement overlapped receiver wall by 0.8 mm nominal.',panel_engagement_mm=8.8,receiver_back_clearance_mm=.2,nominal_tray_corner_bearing_mm=[6.8,6.8],seam_contact='intentional face contact, zero nominal gap',bottom_collar_positive_fixation=False,full_solid_interference_verified=False,physical_fit_verified=False)
(out/'standing-assembly-clearances.json').write_text(json.dumps(checks,indent=2));print(out/'standing-assembly-sections.png',flush=True)
