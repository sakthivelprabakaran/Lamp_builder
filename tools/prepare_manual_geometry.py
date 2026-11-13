"""Stage exact meshes and scene instructions for the assembly booklet."""
import pathlib,json,math,sys,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]));import frame_lamps as m
R=pathlib.Path(__file__).resolve().parents[1];O=R/'tmp/pdfs/manual-assets';O.mkdir(parents=True,exist_ok=True);p=m.resolve(m.catalog()[-3]['params']);meshes={}
for n in ['female','post-wedge','post-pad','male']:
 v,f=m._cad_dovetail(p,n);meshes[n]={'v':v.tolist(),'f':f.tolist()}
for n in ['foot-cap','corner-bottom','corner-through','top-retaining-cap','light-tray','cable-guide','cable-cover','strain-relief','female-cut','post-wedge-cut','post-pad-cut']:
 a=np.load(O/(n+'.npz'));meshes[n]={'v':a['v'].tolist(),'f':a['f'].tolist()}
for j in range(2):
 v,f,_=m.panel(p,j);meshes['panel-'+str(j)]={'v':v.tolist(),'f':f.tolist()}

def obj(mesh,xyz=(0,0,0),angle=0,material='sage',**kw):return dict(mesh=mesh,xyz=list(xyz),angle=angle,material=material,**kw)
def cub(x,y,z,w,d,h,mat='wood',**kw):return dict(box=[w,d,h],xyz=[x,y,z],material=mat,**kw)
def cylinder(x,y,z,r,length,axis='Z',mat='metal'):return dict(cylinder=[r,length,axis],xyz=[x,y,z],material=mat)
q=p['post_center'];H=p['height'];B=p['panel_bottom'];zc=3+(p['rail_mm']+p['rod_clearance'])/2;anchor=p['socket_mm']/2+p['socket_wall']-1;off=anchor+p['dovetail_depth']+6.6;hx=4+.3-(p['dovetail_depth']+6.6)
def corner(lift=0,wood=True,exploded=False):
 a=[obj('female'),obj('post-pad',(-15 if exploded else 0,0,0),material='blue'),obj('post-wedge',(-34 if exploded else 0,0,14 if exploded else 0),material='ochre')]
 if wood:a.append(cub(0,0,20,25,25,90))
 for ang in [0,math.pi/2]:
  zz=2+(lift if ang==0 else 0);a.append(obj('male',(off*math.cos(ang),off*math.sin(ang),zz),ang))
  center=np.array([off+3.3+38,0,zz+zc]);a.append(cub(center[0] if ang==0 else 0,center[0] if ang else 0,center[2],76 if ang==0 else 25,25 if ang==0 else 76,25))
 return a

def assembly(include='all',panel_lift=False):
 a=[]
 for x in [-q,q]:
  for y in [-q,q]:
   a.extend([cub(x,y,(H+p['foot_floor'])/2,25,25,H-p['foot_floor']),obj('foot-cap',(x,y,0))])
 for r in m.standing_structure(p)['wood_rails']:
  if include=='lower' and r['start'][2]>100:continue
  aa=np.array(r['start']);bb=np.array(r['end']);mid=(aa+bb)/2;length=np.linalg.norm(bb-aa);a.append(cub(*mid,length if bb[0]>aa[0] else 25,25 if bb[0]>aa[0] else length,25))
 for ins in m.joint_instances(p,legacy=True):
  if include=='lower' and ins['xyz'][2]>100:continue
  a.append(obj(ins['part'],ins['xyz'],ins['angle']))
 if include in ['all','panels','tray','top']:
  for x in [-q,q]:
   for y in [-q,q]:
    ang=0 if x<0 and y<0 else math.pi/2 if x>0 and y<0 else math.pi if x>0 else math.pi*1.5
    for j in range(3):
     if include=='tray' and j>0:continue
     z=B-1.2 if j==0 else H-24 if j==2 else B+p['segment_height']-12
     a.append(obj('corner-bottom' if j==0 else 'corner-through',(x,y,z),ang))
    if include in ['all','top']:a.append(obj('top-retaining-cap',(x,y,H)))
  a.append(obj('light-tray',(-p['panel_width']/2,-p['panel_width']/2,B)))
  if include in ['all','panels','top']:
   for side in range(4):
    for j in range(2):
     ang=side*math.pi/2;xyz=np.array([-p['panel_width']/2,-q+p['panel_mm']/2,B+j*p['segment_height']+(60 if panel_lift and side==0 else 0)]);c,s=math.cos(ang),math.sin(ang);xyz[:2]=xyz[:2]@np.array([[c,s],[-s,c]]);a.append(obj('panel-'+str(j),xyz,ang,material='shade',rotate_x=math.pi/2))
 return a
scenes={}
def add(n,a,view=(.8,-1,.65),size=(2400,1700),**kw):scenes[n]=dict(objects=a,view=view,size=list(size),**kw)
add('hero',assembly(),(.8,-1,.25),(2200,3000))
# Post/rail layout is seen from above: long timber parallel, short rails in two groups.
a=[]
for i in range(4):a.append(cub(-120+i*80,0,12.5,25,H-p['foot_floor'],25))
for i in range(8):a.append(cub(270+(i%2)*190,-540+(i//2)*310,12.5,134,25,25))
add('flat-layout',a,(0,-.15,1),(3000,2300))
add('frame-parts',[obj('foot-cap',(-110,0,0)),obj('female',(-50,0,0)),obj('post-wedge',(20,0,0),material='ochre'),obj('post-pad',(65,0,0),material='blue'),obj('male',(120,0,0))],(.2,-1,.7),(3000,1500))
add('shade-parts',[obj('panel-0',(-260,-120,0),material='shade'),obj('corner-bottom',(-30,0,0)),obj('corner-through',(30,0,0)),obj('top-retaining-cap',(95,0,0)),obj('light-tray',(150,-70,0))],(.1,-1,1.2),(3000,1900))
add('feet',[obj('foot-cap'),cub(0,0,68,25,25,100)],(.9,-1,.8),(2400,2200),points={'foot':[15,0,10],'post':[0,0,70]})
add('female-exploded',[obj('female'),cub(0,0,20,25,25,80),obj('post-pad',(-23,0,0),material='blue'),obj('post-wedge',(-48,0,0),material='ochre')],(-.25,-1,.5),(3000,1900),points={'A':[15,0,15],'B':[-66,0,16],'C':[-36,0,16]})
add('female-cutaway',[obj('female-cut'),obj('post-pad-cut',material='blue'),obj('post-wedge-cut',material='ochre'),cub(0,6.25,18,25,12.5,46)],(-.15,-1,.42),(3000,2100),points={'A':[15,0,17],'B':[-18.5,0,13],'C':[-13.3,0,17],'wood':[0,0,35]})
add('male-exploded',[obj('male'),cub(72,0,zc,84,25,25),cylinder(hx-32,0,zc,2,29,'X'),cylinder(hx-34,0,zc,3.6,2,'X')],(-.8,-1,.65),(3000,2100),points={'cup':[12,-15,15],'rail':[60,0,zc],'screw':[hx-21,0,zc],'tongue':[hx,0,4]})
add('corner-slide',corner(34),(.8,-1,.7),(3000,2400),points={'insert':[off,0,36],'seat':[anchor+7,0,12]})
add('corner-seated',corner(),(.8,-1,.7),(2800,2200))
add('lower-frame',assembly('lower'),(.8,-1,.28),(2300,3000))
# Crop long posts for focused upper assembly illustrations, without changing parts.
for n,mode in [('upper-frame','frame'),('tray','tray'),('panels','panels'),('top','top')]:
 a=assembly(mode,panel_lift=n=='panels')
 for item in a:
  if 'box' in item and item['box'][2]>1000:item['box'][2]=H-B+160;item['xyz'][2]=(H+B-160)/2
 # Feet/lower frame are removed from the close-up scene.
 a=[o for o in a if o['xyz'][2]>B-200 or ('box' in o and o['box'][2]>300)]
 add(n,a,(.8,-1,.8),(2800,2400))
# Cable guide: an outside post, open U-guide, separate cover and optional relief plate.
add('cable',[cub(0,0,115,25,25,230),obj('cable-guide',(-16,-4,10),rotate_y=-math.pi/2),obj('cable-cover',(-38,-4,10),rotate_y=-math.pi/2),obj('strain-relief',(30,-15,0))],(-.7,-1,.55),(2600,2100))
(O/'geometry.json').write_text(json.dumps(dict(params=p,meshes=meshes,scenes=scenes)));(O/'parts-counts.json').write_text(json.dumps({'vertical_posts':4,'wood_rails':8,'feet':4,'female_sleeves':8,'post_wedges':8,'pressure_pads':8,'male_cups':16,'shade_panels':8,'bottom_collars':4,'through_collars':8,'top_caps':4,'light_tray':1,'core_printed_parts':69,'optional_cable_guides':7,'optional_covers':7,'optional_strain_plate':1,'optional_printed_parts':15,'assembly_coupon_excluded':True},indent=2));print('Prepared',len(scenes),'scenes')
