"""Add LUME headings and truthful part labels outside actual CAD renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse
p=argparse.ArgumentParser();p.add_argument('directory');a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=Path(a.directory)
fontroot=root/'tmp/pdfs/manual-assets'
def font(size,bold=False):return ImageFont.truetype(str(fontroot/('Manrope.ttf' if bold else 'DMSans.ttf')),size)
ivory='#F6F5EF';ink='#384333';sage='#727B65';ochre='#C49C63'
specs={
 'assembly-overview':('The tray has a clear support path.','Four reinforced holders carry the tray; two diagonal tongues retain it.','1 ivory tray  /  4 sage holders  /  no separate locking pieces'),
 'corner-exploded':('One corner. An integral snap tongue.','Align the tray hole with the integral tongue, then press down. Tray corner cropped for clarity.','IVORY: flat tray  /  SAGE: holder with integral tongue'),
 'corner-seated':('Supported below. Retained above.','The reinforced seat carries the tray. The holder tongue prevents lift-out.','Illustration colours distinguish parts; choose matching colours for production.'),
 'print-layout':('Designed around the print bed.','Each changed part is shown in its declared manufacturing orientation.','Toolpath checks and physical testing are recorded separately.')}
for name,(title,sub,legend) in specs.items():
 path=out/(name+'.png')
 if not path.exists():continue
 raw=Image.open(path).convert('RGBA');w=raw.width;top=300;bottom=220
 canvas=Image.new('RGB',(w,raw.height+top+bottom),ivory);draw=ImageDraw.Draw(canvas)
 draw.text((100,55),'LUME  /  STANDING LAMP',font=font(30,True),fill=ink)
 draw.text((100,115),title,font=font(62,True),fill=ink)
 draw.text((100,205),sub,font=font(34),fill=ink)
 canvas.paste(raw,(0,top),raw)
 if name=='corner-exploded':
  ax=w-175;ay=top+170
  draw.line((ax,ay,ax,ay+240),fill=ink,width=12)
  draw.polygon([(ax,ay+270),(ax-32,ay+217),(ax+32,ay+217)],fill=ink)
  draw.text((w-435,ay-60),'PRESS DOWN',font=font(33,True),fill=ink)
 y=top+raw.height+35
 draw.line((100,y,w-100,y),fill='#CCD0C4',width=2)
 draw.text((100,y+35),legend,font=font(32),fill=ink)
 draw.text((100,y+100),'V3 review prototype  |  Geometry renders are not physical strength evidence.',font=font(27),fill='#737B6B')
 canvas.save(out/(name+'-labeled.png'),dpi=(300,300))
print('Labeled render pages saved')
