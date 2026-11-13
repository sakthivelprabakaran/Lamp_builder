"""A5 customer assembly review booklet + imposed A4 saddle-stitch PDF."""
import pathlib,json,math,os
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from pypdf import PdfReader,PdfWriter,Transformation
R=pathlib.Path(__file__).resolve().parents[1];A=R/'tmp/pdfs/manual-assets';O=R/'output/pdf';O.mkdir(parents=True,exist_ok=True)
for n,f in [('Manrope','Manrope.ttf'),('DM','DMSans.ttf')]:pdfmetrics.registerFont(TTFont(n,str(A/f)))
W,H=148*mm,210*mm;M=14*mm;CW=W-2*M;INK=HexColor('#282b27');SAGE=HexColor('#555e47');MUTED=HexColor('#787c73');LINE=HexColor('#dfdfd5');PAPER=HexColor('#f6f5ef');SOFT=HexColor('#eeeee5');AMBER=HexColor('#ba925c');BLUE=HexColor('#64879b')
out=(R/'tmp/pdfs/layout-review.pdf') if os.environ.get('LUME_LAYOUT_REVIEW') else O/'LUME_Standing_Lamp_Assembly_Guide.pdf';c=canvas.Canvas(str(out),pagesize=(W,H),pageCompression=1);c.setTitle('LUME | Four-post standing lamp assembly guide');c.setAuthor('LUME');c.setSubject('Wedge sleeve + axial rail screw | pre-production review edition');page=0;used_images=[];layout=[]
def text(s,x,y,size=9.6,font='DM',color=INK):
 t=c.beginText(x,y);t.setFillColor(color);t.setFont(font,size);t.setCharSpace(0);t.textOut(s);c.drawText(t)
def tracked(s,x,y,size=8,space=1.2,color=MUTED,font='DM'):
 t=c.beginText(x,y);t.setFont(font,size);t.setCharSpace(space);t.setFillColor(color);t.textOut(s);c.drawText(t)
def wrap(s,width,size=9.6,font='DM'):
 lines=[];line=''
 for word in s.split():
  proposed=(line+' '+word).strip()
  if pdfmetrics.stringWidth(proposed,font,size)<=width:line=proposed
  else:
   if line:lines.append(line)
   line=word
 if line:lines.append(line)
 return lines

def para(s,x,y,width=CW,size=9.6,leading=14,font='DM',color=INK):
 lines=wrap(s,width,size,font)
 for line in lines:text(line,x,y,size,font,color);y-=leading
 return y

def brand(x=M,y=H-26*mm,size=24,color=INK):
 tracked('LUME',x,y,size,4,color,'Manrope');c.setFillColor(SAGE);c.circle(x+pdfmetrics.stringWidth('LUME','Manrope',size)+16,y+size*.65,2.1,fill=1,stroke=0)
def base(section,title,sub=None,step=None):
 global page
 page+=1;c.bookmarkPage('p'+str(page));c.addOutlineEntry(section+' | '+title,'p'+str(page),0,False);c.setFillColor(Color(1,1,1));c.rect(0,0,W,H,fill=1,stroke=0)
 brand(y=H-21*mm,size=15);tracked(section.upper(),M,H-32*mm,7.4,1.1)
 y=H-44*mm
 for line in wrap(title,CW,24,'Manrope'):text(line,M,y,24,'Manrope');y-=29
 if sub:para(sub,M,y-2,CW,9.5,13,color=MUTED)
 c.setStrokeColor(LINE);c.setLineWidth(.5);c.line(M,17*mm,W-M,17*mm)
 tracked('REVIEW EDITION',M,10*mm,6.5,.8);text(f'{page:02d} / 16',W-M-37,10*mm,7.5,color=MUTED)
 if page>2:c.linkRect('', 'p2',(M,8*mm,M+98,15*mm),relative=0,thickness=0)
 if step:
  for i in range(1,10):
   c.setFillColor(SAGE if i==step else LINE);c.roundRect(W-M-72+(i-1)*8,H-23*mm,5.5,2.4,1,fill=1,stroke=0)
 return y

def img(name,x,y,w,h):
 h=min(h,148*mm-y) if page>1 else h
 p=A/(name+'.png')
 if os.environ.get('LUME_LAYOUT_REVIEW'):
  c.setFillColor(SOFT);c.rect(x,y,w,h,fill=1,stroke=0);text(name,x+12,y+h/2,10);return (x,y,w,h)
 if not p.exists():raise FileNotFoundError(p)
 ir=ImageReader(str(p));iw,ih=ir.getSize();s=min(w/iw,h/ih);dw,dh=iw*s,ih*s;dx=x+(w-dw)/2;dy=y+(h-dh)/2;c.drawImage(ir,dx,dy,dw,dh,mask='auto');used_images.append({'page':page,'name':name,'pixels':[iw,ih],'placed_inches':[dw/72,dh/72],'dpi':min(iw/(dw/72),ih/(dh/72))});return (dx,dy,dw,dh)
def callouts(name,rect,items):
 d=json.loads((A/(name+'.view.json')).read_text()) if (A/(name+'.view.json')).exists() else {'points':{}};x,y,w,h=rect
 for label,key,tx,ty,color in items:
  if key not in d['points']:continue
  px,py=d['points'][key];px=x+px*w;py=y+py*h;c.setStrokeColor(color);c.setLineWidth(.65);c.line(tx,ty,px,py);c.setFillColor(color);c.circle(px,py,2,fill=1,stroke=0);c.roundRect(tx-10,ty-9,20,18,4,fill=1,stroke=0);text(label,tx-3.5,ty-3.5,9,'DM',Color(1,1,1))
def note(title,body,x=M,y=44*mm,w=CW,color=SAGE):
 c.setFillColor(SOFT);c.roundRect(x,y,w,40,5,fill=1,stroke=0);text(title,x+11,y+26,8.3,'DM',color);para(body,x+11,y+13,w-22,8.1,10,color=MUTED)
def bullets(items,y,x=M,width=CW,size=9.4,leading=13):
 for item in items:
  c.setFillColor(SAGE);c.circle(x+2,y+2,1.4,fill=1,stroke=0);ny=para(item,x+13,y,width-13,size,leading);y=ny-9
 return y

def rows(data,y,heights=27):
 for code,name,count in data:
  c.setStrokeColor(LINE);c.setLineWidth(.35);c.line(M,y+8,W-M,y+8);text(code,M,y-5,9.2,'DM',SAGE);text(name,M+27,y-5,9.4);text(str(count),W-M-18,y-5,11,'Manrope');y-=heights
 return y

def end():c.showPage()
# 01 Cover
page+=1;c.bookmarkPage('p1');c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0);brand(y=H-28*mm,size=30);tracked('OBJECTS SHAPED BY LIGHT',M,H-40*mm,7.5,1.2);text('A lamp. A little ritual.',M,H-56*mm,24,'Manrope');para('Your guide to bringing the four-post standing lamp together.',M,H-68*mm,CW,10,14,color=MUTED);img('hero',M,43*mm,CW,95*mm);text('Four-post standing lamp',M,30*mm,12,'Manrope');tracked('ASSEMBLY GUIDE / PRE-PRODUCTION REVIEW',M,20*mm,6.8,.8);end()
# 02 Map
base('Start here','From parts to light.','Follow the sequence. Keep this booklet open beside a soft, level work surface.')
y=H-76*mm
for num,title,detail,target in [('01','Lay everything out','Count the timber and printed pieces.',3),('02','Build the post connections','Feet, female sleeves, pads and wedges.',6),('03','Connect the rail frames','Male cups first; lower frame, then upper.',8),('04','Build the light chamber','Support collars, tray and eight panels.',11),('05','Finish and check','Retainers, cable route and final review.',13)]:
 c.setFillColor(SOFT);c.circle(M+12,y-3,11,fill=1,stroke=0);text(num,M+6,y-6,8.5,'DM',SAGE);text(title,M+34,y,12,'Manrope');text(detail,M+34,y-18,8.7,color=MUTED);text(f'{target:02d}',W-M-15,y,9,color=SAGE);c.linkRect('', 'p'+str(target),(M,y-24,W-M,y+15),relative=0,thickness=0);y-=64
note('One principle','Match parts before applying pressure. If a part binds, stop and check its direction.',y=21*mm);end()
# 03 Parts frame
base('In your box','The frame kit.','Four posts. Two rail frames. One connection system repeated at every corner.')
img('frame-parts',M,118*mm,CW,38*mm)
rows([('W1','Vertical timber post',4),('W2','Horizontal timber rail',8),('A','Female post sleeve',8),('B','Tightening wedge',8),('C','Pressure pad',8),('D','Male rail cup',16),('E','Individual foot cap',4)],109*mm,27)
text('44',M,29*mm,25,'Manrope',SAGE);text('printed frame pieces + 12 timber pieces',M+45,31*mm,9.5)
text('Rail fixings: one axial screw per cup, 16 in total.',M,22*mm,8.6,color=MUTED);end()
# 04 Shade counts
base('In your box','The shade kit.','Four sides, each made from two replaceable panel segments.')
img('shade-parts',M,119*mm,CW,40*mm)
rows([('F','Bottom support collar',4),('G','Through collar: mid + upper',8),('H','Top retaining cap',4),('I','Patterned panel segment',8),('J','Light support tray',1)],110*mm,30)
text('69',M,42*mm,32,'Manrope',SAGE);para('printed core pieces in the complete lamp: 44 frame + 25 shade.',M+63,52*mm,CW-63,9.3,13)
para('Optional cable pack: 7 guides + 7 covers + 1 strain-relief plate for Pearl / Reed. Folio uses 6 guides + 6 covers + 1 plate. Light hardware is counted separately.',M,29*mm,CW,8,10,color=MUTED);end()
# 05 Flat workspace
base('Prepare / 01','Start on a flat surface.','Keep the long posts parallel. Group rails and printed parts before standing the frame.',step=1)
img('flat-layout',M,69*mm,CW,90*mm)
bullets(['Lay out four posts together, with the foot ends pointing the same way.','Make two groups of four rails: one lower frame and one upper frame.','Keep eight A + B + C sleeve sets and sixteen D rail cups in separate trays.','Use a soft mat and enough space for the full post length. Two people should support the tall frame while it is assembled.'],64*mm,size=8.8,leading=12)
end()
# 06 Feet
base('Posts / 02','Fit the four feet.','A foot cap belongs on the bottom of each vertical post.',step=2)
r=img('feet',M,65*mm,CW,96*mm);callouts('feet',r,[('E','foot',M+25,76*mm,SAGE)])
bullets(['Match the square post to the square opening in E.','Press the post fully down to the closed floor of the foot cap.','Repeat on all four posts. Keep the foot ends aligned.'],61*mm,size=9.2,leading=12)
note('Orientation','Closed floor down. Open square socket up.',y=21*mm);end()
# 07 Female
base('Post connections / 03','One sleeve. Three pieces.','A wraps around the post. C faces the wood. B slides in behind C.',step=3)
r=img('female-exploded',M,102*mm,CW,64*mm);callouts('female-exploded',r,[('A','A',M+28,102*mm,SAGE),('B','B',W-M-28,139*mm,AMBER),('C','C',W-M-28,119*mm,BLUE)])
r=img('female-cutaway',M,51*mm,CW,50*mm);callouts('female-cutaway',r,[('B','B',M+16,75*mm,AMBER),('C','C',M+70,54*mm,BLUE)])
para('Slide A onto the post. Place C in the tightening channel with its flat face toward the wood. Insert B behind C and press it down to tighten.',M,45*mm,CW,9.1,13)
para('Use one B and one C for each A. Fit two sleeves per post: lower and upper rail levels. Match the heights across all four posts.',M,29*mm,CW,8.6,12)
end()
# 08 Male
base('Rail connections / 04','Give every rail two ends.','Each timber rail receives one D cup at either end.',step=4)
r=img('male-exploded',M,71*mm,CW,95*mm);callouts('male-exploded',r,[('D','cup',M+20,86*mm,SAGE),('S','screw',M+30,145*mm,MUTED)])
bullets(['Slide the 25 mm rail into the square socket of D until its end reaches the cup floor.','Insert the axial screw through the recessed opening on the dovetail face and into the rail end.','Repeat at the other end. Both tongues must face downward in the final assembly.'],66*mm,size=8.8,leading=12)
note('Before joining','Match screw head and length to the supplied hardware. The screw must sit below the tongue face.',y=21*mm);end()
# 09 Lower frame
base('Lower frame / 05','Build the first square.','Use the four lower sleeve positions and one group of four rails.',step=5)
img('lower-frame',M,69*mm,CW,96*mm)
bullets(['Support all four posts upright on a level surface. Keep the receivers facing inward.','Align both tongues of the first rail above their matching female grooves. Lower both ends together to the receiver floors.','Add the opposite rail, then the remaining two. Keep the square untwisted and all four feet on the floor.'],64*mm,size=9,leading=12)
end()
# 10 Upper frame
base('Upper frame / 06','Repeat above.','The second set of four rails connects the upper sleeves below the shade.',step=6)
img('upper-frame',M,102*mm,CW,62*mm)
r=img('corner-slide',M,65*mm,CW,40*mm)
# Direction arrow is a vector overlay aligned to the raised rail end.
d=json.loads((A/'corner-slide.view.json').read_text()) if (A/'corner-slide.view.json').exists() else {'points':{'insert':[.5,.5]}};px,py=d['points']['insert'];x=r[0]+px*r[2];y=r[1]+py*r[3];c.setStrokeColor(SAGE);c.setLineWidth(1.4);c.line(x+22,y+22,x+22,y-3);c.line(x+18,y+3,x+22,y-3);c.line(x+26,y+3,x+22,y-3)
bullets(['Keep the upper sleeve heights equal on all four posts.','Lower each rail at both ends together. Seat all four rails completely.','Check that both frames are square before adding the light chamber.'],62*mm,size=9.1,leading=12)
para('Current prototype positions: lower rail centre 70 mm above the floor; upper rail centre 65 mm below the shade. Heights must be confirmed for the shipped variant.',M,25*mm,CW,7.8,10,color=MUTED)
end()
# 11 Tray
base('Light chamber / 07','Build its foundation.','Four F collars carry the lower panel edges and support the tray.',step=7)
img('tray',M,74*mm,CW,89*mm)
bullets(['Slide one F collar down each post. Turn the two panel receivers toward the neighbouring posts.','Align the four collars at the bottom of the light chamber.','Seat J on the inward corner shelves. Keep the cable opening accessible.'],69*mm,size=9.1,leading=13)
note('Release check','The positive height-stop method for F is not finalized in this prototype. Confirm it before customer use.',y=24*mm,color=AMBER)
end()
# 12 Panels
base('Shade / 08','Four sides. Two layers.','Install the panels without twisting the frame or forcing an edge.',step=8)
img('panels',M,77*mm,CW,88*mm)
bullets(['Slide each of the four lower I panels into the two neighbouring F receivers.','Lower four G collars to the middle seam and align their slots with the panel edges.','Add the four upper I panels. Keep the patterns facing outward and the seams level.'],72*mm,size=9.1,leading=13)
note('Keep it gentle','Support the panel near its edge. Re-align a tight slot instead of bending the panel.',y=24*mm)
end()
# 13 Top
base('Finish / 09','Close the light chamber.','The final four G collars locate the upper panel edges.',step=9)
img('top',M,72*mm,CW,92*mm)
bullets(['Lower one upper G collar onto each post and align its receivers with the two adjacent panels.','Fit the four H caps at the post tops using the approved retaining arrangement.','Confirm that the panel stack cannot lift out during normal handling.'],67*mm,size=9.1,leading=13)
note('Release check','Top-cap retention is not finalized in this prototype. A loose cap is not a secured retainer.',y=24*mm,color=AMBER)
end()
# 14 Cable
base('Light + cable','A tidy route to light.','Keep the light unplugged while completing the mechanical assembly.')
img('cable',M,87*mm,CW,77*mm)
bullets(['Use the supplied pre-wired light module and its own manufacturer instructions.','Route the cable outside one post, clear of the panel slots and sliding joints.','If the optional guides are supplied, place the cable in each open guide before fitting its cover.','Use the approved strain-relief arrangement near the tray; leave room for the required cable bend.'],83*mm,size=8.9,leading=12)
para('This guide shows mechanical placement only. Actual light-holder mounting, cable-guide attachment and light specifications still require release approval.',M,26*mm,CW,8,10,color=MUTED)
end()
# 15 Check care
base('Before use','A quiet final check.','Give the assembly a complete check before connecting power.')
img('corner-seated',M,108*mm,CW,52*mm)
y=102*mm
for s in ['Four feet are seated and rest evenly.','Both rail frames are square; all eight rails are fully seated.','Eight sleeves are tight; no wedges are loose.','All eight shade panels are supported and retained.','The light module is secure; the cable is clear of moving joints.']:
 c.setStrokeColor(SAGE);c.setLineWidth(.6);c.rect(M,y-2,6,6,fill=0,stroke=1);y=para(s,M+15,y,CW-15,8.8,12)-8
para('To remove a rail: support the frame and lift both rail ends together. To service the shade: unplug the light and release the approved top retainers first. Support the lamp at its wooden posts; do not lift it by the shade or rails.',M,36*mm,CW,8.3,11,color=MUTED)
end()
# 16 Back / review disposition
base('Release notes','Ready for the next chapter.','This edition is a complete visual assembly review, not an approved shipping instruction.')
text('Before this guide goes into the box',M,136*mm,13,'Manrope')
bullets(['Confirm actual timber sizes, printed fits and the wedge grip under sustained load.','Confirm lower shade-collar height fixation and the top-cap retaining method.','Verify frame stability, rail lift-out behaviour and safe handling through physical tests.','Finalize screw specifications, light-holder mounting, cable attachments and thermal clearance.','Confirm the packed contents, product variant and factory-fitted versus customer-fitted parts.'],126*mm,size=9.3,leading=13)
para('Rendered from the current LUME model: wedge-tightened female sleeves and axial-screw male rail cups. Colors and timber finish are illustrative. No locking pin or bolt is fitted to the selected female sleeve.',M,64*mm,CW,8.8,12,color=MUTED)
brand(y=33*mm,size=27);tracked('OBJECTS SHAPED BY LIGHT',M,24*mm,7,.9);end()
assert page==16;c.save()
if os.environ.get('LUME_LAYOUT_REVIEW'):print('Layout review ready');raise SystemExit(0)
# Saddle stitch: four A4 sheets, duplex short edge, nested and folded.
r=PdfReader(str(out));assert len(r.pages)==16;w=PdfWriter();pairs=[(15,0),(1,14),(13,2),(3,12),(11,4),(5,10),(9,6),(7,8)]
for left,right in pairs:
 sheet=w.add_blank_page(width=297*mm,height=210*mm)
 for idx,x in [(left,.5*mm),(right,148.5*mm)]:sheet.merge_transformed_page(r.pages[idx],Transformation().translate(tx=x,ty=0),expand=False)
w.add_metadata({'/Title':'LUME | A4 print booklet | duplex short edge','/Author':'LUME','/Subject':'Print at 100 percent; four A4 sheets; duplex short edge; fold and nest.'})
with open(O/'LUME_Standing_Lamp_Print_Booklet_A4.pdf','wb') as f:w.write(f)
(A/'pdf-image-resolution.json').write_text(json.dumps(used_images,indent=2));assert min(i['dpi'] for i in used_images)>=300
print('16 A5 pages and 8 imposed A4 sides created; minimum image DPI',round(min(i['dpi'] for i in used_images)))
