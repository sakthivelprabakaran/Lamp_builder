import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import frame_lamps as m,numpy as np
from PIL import Image,ImageDraw,ImageFont
root=pathlib.Path(__file__).resolve().parents[1];p=m.resolve({});fv,ff=m.dovetail_female(p);mv,mf=m.dovetail_male(p);mv=mv.copy();mv[:,0]+=12.6;mv[:,2]+=2
im=Image.new('RGB',(1200,760),'#f5f4ec');d=ImageDraw.Draw(im);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16);title=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',26)
d.text((25,18),'LUME / PETG rail dovetail — section and assembly proposal',font=title,fill='#394331');d.text((25,60),'16 male rail shoes + 16 female receivers · 8 rails · dimensions provisional',font=font,fill='#656b5c')
def section(v,f,z,center,scale,color):
 for t in v[f]:
  pts=[]
  for a,b in zip(t,np.roll(t,-1,axis=0)):
   if min(a[2],b[2])<z<max(a[2],b[2]):pts.append(a[:2]+(b[:2]-a[:2])*(z-a[2])/(b[2]-a[2]))
  if len(pts)==2:d.line([tuple(x*scale+center) for x in pts],fill=color,width=3)
center=np.array([65,285]);section(fv,ff,10.8,center,10,'#56624b');section(mv,mf,10.8,center,10,'#c28b52');d.text((25,115),'A / Actual mesh plan section, Z = 10.8',font=font,fill='#394331');d.text((25,430),'Green: female on post face; amber: rail-end male shoe.',font=small,fill='#656b5c');d.text((25,460),'Male head 12 wide; neck 8; receiver allowance 0.3.',font=small,fill='#656b5c');d.text((25,490),'Nominal minimum sloped-face gap ≈ 0.19 mm.',font=small,fill='#656b5c');d.text((25,520),'Male shoe has an open top, rail seat and two fixing holes.',font=small,fill='#656b5c')
d.text((640,115),'B / Same downward direction at both ends',font=font,fill='#394331')
for x in [710,1050]:
 d.rectangle((x,310,x+34,405),outline='#56624b',width=3);d.rectangle((x+5,155,x+29,235),outline='#c28b52',width=3);d.line((x+17,245,x+17,293),fill='#394331',width=3);d.polygon([(x+17,302),(x+9,289),(x+25,289)],fill='#394331')
d.rectangle((734,182,1055,210),fill='#b29a79');d.text((775,260),'Slide both ends down 30 mm',font=small,fill='#656b5c');d.text((640,430),'Closed receiver floor stops downward travel.',font=small,fill='#656b5c');d.text((640,460),'Matching 4.2 mm holes accept a proposed 4 mm cross-pin.',font=small,fill='#656b5c');d.text((640,490),'Pin + removable keeper prevents upward withdrawal.',font=small,fill='#656b5c');d.text((640,520),'Keeper and timber fasteners are hardware decisions.',font=small,fill='#9a5737')
d.text((25,590),'Assembly: attach receivers/male shoes to wood → align four posts → insert eight rails downward → pin each end → fit upper shade.',font=small,fill='#394331');d.text((25,625),'Final rail uses the same vertical path; no opposing sideways slides. Removal clearance below shade is proposed at 50 mm.',font=small,fill='#656b5c');d.text((25,660),'Nominal CAD overlap/motion checks, PETG coupons, actual screw/pin access and physical retention remain separate validations.',font=small,fill='#9a5737');d.text((25,715),'This is a mechanical prototype proposal; neither tool-free locking nor tested rigidity is claimed.',font=small,fill='#656b5c');im.save(root/'output/revamp/standing-dovetail-section.png');print(root/'output/revamp/standing-dovetail-section.png')
