"""Clear actual-geometry views and mesh-gated inspection STLs/3MF."""
import sys,pathlib,math,json,zipfile,xml.etree.ElementTree as ET
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import frame_lamps as m,numpy as np,lamp_engine as engine,print_geometry as pg
from PIL import Image,ImageDraw,ImageFont
from joint_render_utils import box,transform,render
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'output/revamp/selected-wedge-axial';OUT.mkdir(parents=True,exist_ok=True);p=m.resolve(m.catalog()[-3]['params']);meshes={n:m._cad_dovetail(p,n) for n in ['female','post-wedge','post-pad','male']}
BODY=[90,113,98];WOOD=[172,135,94];METAL=[150,158,162]
font=lambda n:ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
anchor=p['socket_mm']/2+p['socket_wall']-1;off=anchor+p['dovetail_depth']+6.6;zc=3+(p['rail_mm']+p['rod_clearance'])/2;o=p['socket_mm']/2+p['socket_wall'];hx=4+.3-(p['dovetail_depth']+6.6)
def part(n,angle=0,xyz=(0,0,0)):
 v,f=meshes[n];return transform(v,angle,np.array(xyz)),f,BODY
# Approximate metal silhouettes illustrate screw location, not hardware specifications.
def cyl(axis,center,r,length,n=32):
 v=[]
 for t in [0,length]:
  for i in range(n):
   a=i*2*math.pi/n;v.append([t,r*math.cos(a),r*math.sin(a)])
 v+= [[0,0,0],[length,0,0]];f=[]
 for i in range(n):
  j=(i+1)%n;f.extend([[i,j,n+j],[i,n+j,n+i],[2*n,j,i],[2*n+1,n+i,n+j]])
 v=np.array(v,float)
 if axis=='Y':v=v[:,[1,0,2]];f=np.array(f)[:,::-1]
 return v+center,np.array(f),METAL

def sleeve():return [part(n) for n in ['female','post-wedge','post-pad']]
def clamp_hardware():return []
def rail_hardware():return [cyl('X',[hx+2.9,0,zc],2,27),cyl('X',[hx+.3,0,zc],3.6,2.4)]
def corner(lift=0):
 obs=sleeve()+[(*box(0,0,20,25,25,90),WOOD)]
 for a in [0,math.pi/2]:
  dz=2+(lift if a==0 else 0);pos=np.array([off*math.cos(a),off*math.sin(a),dz]);obs.append(part('male',a,pos))
  vv,ff=box(3.3+off+38,0,dz+zc,76,25,25);obs.append((transform(vv,a,np.zeros(3)),ff,WOOD))
  for vv,ff,col in rail_hardware():obs.append((transform(vv,a,pos),ff,col))
 return obs
im=Image.new('RGB',(1800,1450),(246,245,239));d=ImageDraw.Draw(im);d.text((45,26),'SIMPLE DOVETAIL / WHERE EACH PART GOES',font=font(36),fill='#273c30');d.text((45,80),'Wedge-tightened post sleeve + one axial screw per rail end.',font=font(24),fill='#59685d')
rects=[(35,140,850,580),(915,140,850,580),(35,750,850,580),(915,750,850,580)]
for x,y,w,h in rects:d.rounded_rectangle((x,y,x+w,y+h),18,fill='#e6eae1')
labels=['1  FEMALE SLEEVE ON VERTICAL POST','2  MALE CUP ON THE RAIL END','3  ALIGN ABOVE, THEN SLIDE DOWN','4  BOTH RAILS SEATED AT THE STOPS']
for r,label in zip(rects,labels):d.text((r[0]+24,r[1]+16),label,font=font(25),fill='#263c2f')
render(im,(50,208,500,375),sleeve()+[(*box(0,0,30,25,25,80),WOOD)],view=(-.8,-.9,.8))
render(im,(535,245,330,270),sleeve(),view=(.75,.95,.85))
d.text((60,632),'Printed wedge presses the pad against the post. No post drilling.',font=font(21),fill='#334b3c');d.text((545,536),'Two female grooves',font=font(18),fill='#334b3c')
render(im,(930,214,470,345),[part('male')]+rail_hardware(),view=(-1,.8,.65))
render(im,(1400,250,330,260),[part('male')],view=(1,.8,.65))
d.text((945,581),'Dovetail tongue + recessed axial screw',font=font(20),fill='#334b3c');d.text((1412,530),'25.6 mm rail socket',font=font(18),fill='#334b3c');d.text((945,635),'Slide the 25 mm rail into the cup, then screw into its end.',font=font(20),fill='#334b3c')
render(im,(50,815,820,425),corner(32),view=(.75,.95,.72))
d.line((750,885,750,1015),fill='#447656',width=7);d.polygon([(736,995),(764,995),(750,1027)],fill='#447656');d.text((65,1253),'Rail and male cup move together vertically.',font=font(22),fill='#334b3c')
render(im,(930,815,820,425),corner(),view=(.75,.95,.72));d.text((945,1253),'Female sleeve + wedge + pad; male cup + one axial rail screw.',font=font(21),fill='#334b3c')
d.text((45,1385),'Nominal prototype geometry. Screw lengths / fit and resistance to lift-out remain to be tested.',font=font(21),fill='#59685d')
im.save(OUT/'simple-dovetail-assembly.png')
# Clear standalone male / female views with STL filenames.
im=Image.new('RGB',(1600,750),(246,245,239));d=ImageDraw.Draw(im);d.text((40,20),'SELECTED CONNECTION',font=font(32),fill='#273c30');render(im,(30,95,740,540),sleeve(),view=(.75,.95,.8));render(im,(825,95,740,540),[part('male')],view=(-1,.8,.6));d.text((85,665),'Female sleeve + tightening wedge / pressure pad',font=font(24),fill='#334b3c');d.text((865,665),'B — male rail cup / axial screw opening',font=font(24),fill='#334b3c');im.save(OUT/'simple-dovetail-parts.png')
records={}
for n,(v,f) in meshes.items():
 ok,metrics=engine.verify_mesh(v,f)
 if not ok:raise ValueError('Mesh gate failed '+n)
 v=v.copy();v[:,2]-=v[:,2].min();filename={'female':'A-female-wedge-sleeve','post-wedge':'B-post-tightening-wedge','post-pad':'C-post-pressure-pad','male':'D-male-axial-rail-cup'}[n]+'.stl';engine.write_binary_stl(str(OUT/filename),v,f);records[n]={'file':filename,'mesh':metrics,'as_modeled_overhang_screen':pg.manufacturing_report(v,f)}
(OUT/'mesh-validation.json').write_text(json.dumps(records,indent=2));(OUT/'params.json').write_text(json.dumps(p,indent=2))
# 3MF core geometry package: separate named parts, wood reference and metal silhouettes.
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',NS);tag=lambda s:'{'+NS+'}'+s
model=ET.Element(tag('model'),unit='millimeter');res=ET.SubElement(model,tag('resources'));mats=ET.SubElement(res,tag('basematerials'),id='1')
for name,color in [('Printed connector','#5A7162FF'),('REFERENCE timber','#AC875EFF'),('REFERENCE screw','#969EA2FF')]:ET.SubElement(mats,tag('base'),name=name,displaycolor=color)
build=ET.SubElement(model,tag('build'));names=['Female wedge sleeve','Post tightening wedge','Post pressure pad','REFERENCE post','Male rail cup X','REFERENCE rail X','REFERENCE rail screw X','REFERENCE screw head X','Male rail cup Y','REFERENCE rail Y','REFERENCE rail screw Y','REFERENCE screw head Y']
for i,((v,f,col),name) in enumerate(zip(corner(),names),2):
 # Each reference/printed mesh passes the watertight gate separately.
 ok,metrics=engine.verify_mesh(v,f)
 if not ok:raise ValueError('3MF mesh failed '+name)
 obj=ET.SubElement(res,tag('object'),id=str(i),type='model',name=name,pid='1',pindex=str(0 if col==BODY else 1 if col==WOOD else 2));mesh=ET.SubElement(obj,tag('mesh'));verts=ET.SubElement(mesh,tag('vertices'));tris=ET.SubElement(mesh,tag('triangles'))
 for a in v:ET.SubElement(verts,tag('vertex'),x=f'{a[0]:.6f}',y=f'{a[1]:.6f}',z=f'{a[2]:.6f}')
 for a in f:ET.SubElement(tris,tag('triangle'),v1=str(a[0]),v2=str(a[1]),v3=str(a[2]))
 ET.SubElement(build,tag('item'),objectid=str(i))
for child in list(build):build.remove(child)
assembly=ET.SubElement(res,tag('object'),id='30',type='model',name='Corner assembly — DISPLAY ONLY');components=ET.SubElement(assembly,tag('components'))
for oid in range(2,2+len(corner())):ET.SubElement(components,tag('component'),objectid=str(oid))
ET.SubElement(build,tag('item'),objectid='30',transform='1 0 0 0 1 0 0 0 1 0 0 25')
with zipfile.ZipFile(OUT/'DISPLAY-ONLY-corner-assembly.3mf','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
 z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
(OUT/'README.txt').write_text('Selected connection: female sleeve with separate printed wedge and pressure pad, no screw driven into the vertical post. Male rail cup uses one axial screw into the rail end. Legacy female pin holes removed; no retaining pin supplied. All four meshes pass the watertight gate; slice orientation/supports and physical fit remain owner checks. The reference 3MF is for assembly inspection: do not print the wood or metal reference shapes. Dovetails slide down to their floors; positive lift-out retention is not claimed. Units mm; nominal 25 mm timber, 25.6 mm sockets. Earlier clamp and wedge review exports are retained separately.\n')
with zipfile.ZipFile(OUT/'selected-wedge-axial-STLs.zip','w',zipfile.ZIP_DEFLATED) as z:
 for path in OUT.iterdir():
  if path.suffix in ['.stl','.3mf','.txt','.json']:z.write(path,path.name)
print('Rendered and exported simplified connector files',flush=True)
