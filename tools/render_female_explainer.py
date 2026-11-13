import pathlib,sys,numpy as np,xml.etree.ElementTree as ET,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw,ImageFont
from joint_render_utils import box,render
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'output/revamp/female-wedge-review'
FONT=lambda n:ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
colors={'female':[82,111,94],'post-wedge':[211,159,77],'post-pad':[93,153,189]};WOOD=[180,144,103]
def mesh(n,cut=False,shift=(0,0,0)):
 a=np.load(OUT/(n+('-cutaway' if cut else '')+'.npz'));return a['v']+shift,a['f'],colors[n]
im=Image.new('RGB',(1600,1100),(247,246,240));d=ImageDraw.Draw(im);d.text((40,25),'A + B + C = ONE FEMALE CONNECTOR',font=FONT(32),fill='#263c30');d.text((40,74),'One sleeve, one tightening wedge, one pressure pad per post connection.',font=FONT(22),fill='#53685b')
for i,(n,label) in enumerate([('female','A · Female sleeve'),('post-wedge','B · Tightening wedge'),('post-pad','C · Pressure pad')]):
 x=30+i*525;d.rounded_rectangle((x,128,x+510,445),16,fill='#e6ebe2');render(im,(x+15,142,480,245),[mesh(n)],view=(-.65,-.9,.6) if n=='female' else (.7,-1,.5));d.text((x+25,397),label,font=FONT(24),fill='#293f33')
d.rounded_rectangle((30,475,790,1015),16,fill='#e6ebe2');d.rounded_rectangle((810,475,1570,1015),16,fill='#e6ebe2');d.text((55,490),'WHERE C GOES — CUTAWAY',font=FONT(23),fill='#263c30');d.text((835,490),'ASSEMBLY ORDER — EXPLODED',font=FONT(23),fill='#263c30')
objects=[mesh(n,True) for n in ['female','post-wedge','post-pad']]+[(*box(0,6.25,18,25,12.5,46),WOOD)]
project=render(im,(52,558,714,360),objects,view=(-.15,-1,.4),margin=28)
for label,target,y in [('B · wedge',[-18.5,0,13],928),('C · pad',[-13.3,0,17],960)]:
 point=project(target);start=np.array([235 if label.startswith('B') else 540,y]);d.line([tuple(start),tuple(point)],fill='#334b3c',width=2);d.ellipse((point[0]-4,point[1]-4,point[0]+4,point[1]+4),fill='#334b3c');d.text((start[0]-90,y+5),label,font=FONT(20),fill='#334b3c')
objects=[mesh('female'),mesh('post-pad',shift=(-20,0,0)),mesh('post-wedge',shift=(-45,0,0)),(*box(0,0,18,25,25,46),WOOD)]
render(im,(835,558,710,358),objects,view=(-.25,-1,.4),margin=25)
d.text((835,937),'1  Put C into A, with its flat face toward the post.',font=FONT(20),fill='#334b3c');d.text((835,972),'2  Slide B into the same channel, behind C.',font=FONT(20),fill='#334b3c')
d.text((40,1042),'Blue C touches the wood; amber B pushes C. Colors show placement only.',font=FONT(23),fill='#53685b');im.save(OUT/'female-A-B-C-placement.png')
# Preserve assembly positions as one compound 3MF for slicer inspection.
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',NS);tag=lambda s:'{'+NS+'}'+s;model=ET.Element(tag('model'),unit='millimeter');res=ET.SubElement(model,tag('resources'));mats=ET.SubElement(res,tag('basematerials'),id='1')
for name,color in [('A Sleeve','#526F5EFF'),('B Wedge','#D39F4DFF'),('C Pad','#5D99BDFF'),('REFERENCE wood','#B49067FF')]:ET.SubElement(mats,tag('base'),name=name,displaycolor=color)
objects=[mesh('female'),mesh('post-wedge'),mesh('post-pad'),(*box(0,0,18,25,25,46),WOOD)]
for i,(v,f,col) in enumerate(objects,2):
 obj=ET.SubElement(res,tag('object'),id=str(i),type='model',name=['A Female sleeve','B Tightening wedge','C Pressure pad','REFERENCE wood — do not print'][i-2],pid='1',pindex=str(i-2));mm=ET.SubElement(obj,tag('mesh'));vv=ET.SubElement(mm,tag('vertices'));ff=ET.SubElement(mm,tag('triangles'))
 for a in v:ET.SubElement(vv,tag('vertex'),x=f'{a[0]:.6f}',y=f'{a[1]:.6f}',z=f'{a[2]:.6f}')
 for a in f:ET.SubElement(ff,tag('triangle'),v1=str(a[0]),v2=str(a[1]),v3=str(a[2]))
a=ET.SubElement(res,tag('object'),id='10',type='model',name='Female assembly — DISPLAY ONLY');c=ET.SubElement(a,tag('components'))
for i in range(2,6):ET.SubElement(c,tag('component'),objectid=str(i))
b=ET.SubElement(model,tag('build'));ET.SubElement(b,tag('item'),objectid='10',transform='1 0 0 0 1 0 0 0 1 0 0 5')
with zipfile.ZipFile(OUT/'female-A-B-C-assembled-inspection.3mf','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True));z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>');z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
print('Labeled cutaway and assembled inspection 3MF ready')
