"""Render actual v3 triangle geometry; no generated substitute shapes."""
import sys,pathlib,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np,frame_lamps as m
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'output/revamp';p=m.resolve(m.catalog()[-3]['params'])
FONTP='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(n):return ImageFont.truetype(FONTP,n)
def box(x,y,z,w,d,h):
 v=np.array([[x+a*w/2,y+b*d/2,z+c*h/2] for c in [-1,1] for b in [-1,1] for a in [-1,1]],float)
 f=np.array([[0,2,3],[0,3,1],[4,5,7],[4,7,6],[0,1,5],[0,5,4],[2,6,7],[2,7,3],[0,4,6],[0,6,2],[1,3,7],[1,7,5]])
 return v,f
meshes={n:m._cad_dovetail(p,n) for n in ['female','male','post-wedge','rail-wedge','post-pad','rail-pad','pin','keeper']}
BODY=[89,108,96];LOCK=[202,150,76];WOOD=[172,135,94]
def transform(v,angle,xyz):
 v=v.copy();c,s=math.cos(angle),math.sin(angle);v[:,:2]=v[:,:2]@np.array([[c,-s],[s,c]]).T;return v+xyz

def render(im,rect,objects,view=(.75,.95,.6),margin=25):
 ts=[];cs=[]
 for v,f,col in objects:ts.append(v[f]);cs.append(np.tile(col,(len(f),1)))
 t=np.concatenate(ts);colors=np.concatenate(cs);view=np.array(view,float);view/=np.linalg.norm(view);right=np.cross(view,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,view)
 normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 vis=normal@view>0;t=t[vis];normal=normal[vis];colors=colors[vis];uv=np.stack([t@right,t@up],-1);lo=uv.reshape(-1,2).min(0);hi=uv.reshape(-1,2).max(0);x,y,w,h=rect;scale=min((w-2*margin)/(hi[0]-lo[0]),(h-2*margin)/(hi[1]-lo[1]));uv=(uv-(lo+hi)/2)*scale;uv[:,:,0]+=x+w/2;uv[:,:,1]=y+h/2-uv[:,:,1];light=np.array([.3,.2,.92]);shade=(.50+.5*np.maximum(normal@light,0))[:,None]*colors;draw=ImageDraw.Draw(im)
 for i in np.argsort(t.mean(1)@view):draw.polygon([tuple(q) for q in uv[i]],fill=tuple(shade[i].astype(int)))

def joint(exploded=False):
 objects=[];anchor=p['socket_mm']/2+p['socket_wall']-1;off=anchor+p['dovetail_depth']+6.6;zc=3+(p['rail_mm']+p['rod_clearance'])/2;width=max(10,p['dovetail_head']/2+p['dovetail_clearance']+3.7)
 def add(n,angle=0,xyz=(0,0,0)):
  v,f=meshes[n];objects.append((transform(v,angle,np.array(xyz)),f,BODY if n in ['female','male'] else LOCK))
 add('female');add('post-wedge',xyz=(0,0,42 if exploded else 0));add('post-pad',xyz=(-28,0,20) if exploded else (0,0,0))
 if not exploded:objects.append((*box(0,0,20,25,25,110),WOOD))
 for a in [0,math.pi/2]:
  shift=42 if exploded else 0;z=38 if exploded else 2;xy=np.array([math.cos(a),math.sin(a)])*(off+shift)
  add('male',a,(*xy,z));add('rail-pad',a,(*xy,z+18 if exploded else z));add('rail-wedge',a,(*(xy+np.array([math.cos(a),math.sin(a)])*(28 if exploded else 0)),z+12 if exploded else z))
  if not exploded:
   pc=anchor+4+p['dovetail_depth']*.55;pxy=np.array([math.cos(a),math.sin(a)])*pc;pinz=p['dovetail_height']/2+2;add('pin',a,(*pxy,pinz));add('keeper',a,(*(pxy+np.array([-math.sin(a),math.cos(a)])*(width+4)),pinz))
   vv,ff=box(off+3.3+45,0,2+zc,90,25,25);objects.append((transform(vv,a,np.zeros(3)),ff,WOOD))
 return objects
im=Image.new('RGB',(1600,1000),(244,243,236));d=ImageDraw.Draw(im);d.text((55,32),'POST SLEEVE + MALE / FEMALE DOVETAIL',font=font(34),fill='#27392f');d.text((55,82),'Actual modeled parts • PETG prototype • 25 mm square timber',font=font(22),fill='#5c665e')
d.rounded_rectangle((35,140,790,800),18,fill='#e9ebe3');d.rounded_rectangle((810,140,1565,800),18,fill='#e9ebe3');render(im,(40,180,740,570),joint());render(im,(820,180,735,570),joint(True));d.text((65,155),'ASSEMBLED CORNER',font=font(22),fill='#27392f');d.text((840,155),'EXPLODED — VERTICAL DOVETAIL INSERTION',font=font(22),fill='#27392f')
lines=['Green: one sleeve around the post, with two female receivers; male sleeve on each rail.', 'Amber: removable wedges, pressure pads, dovetail cross-pin and separate keeper.', 'No screw holes in the revised wood mounts. Wedge grip / PETG creep need physical tests.', 'Nominal geometry preview — not a strength, support-free printing or commercial certification.']
for i,line in enumerate(lines):d.text((55,835+i*34),line,font=font(21),fill='#344239')
im.save(OUT/'standing-sleeve-dovetail-detail.png')
# Full standing variants, including actual panel meshes and every placed joint.
im=Image.new('RGB',(1600,1120),(244,243,236));d=ImageDraw.Draw(im);d.text((50,28),'LUME / STANDING — REVISED SLEEVE JOINTS',font=font(32),fill='#27392f');d.text((50,76),'Two horizontal rail frames • four clean timber posts • no diagonal braces or shelves',font=font(21),fill='#5c665e')
def cached_render(n):
 a=np.load(ROOT/'output/frame-cache'/('render-'+n+'.npz'));return a['v'],a['f']
foot_mesh=cached_render('foot-cap');collar_meshes={False:cached_render('corner-bottom'),True:cached_render('corner-through')}
for i,des in enumerate(m.catalog()[-3:]):
 data=m.preview(des['params']);pp=data['frame'];v=np.array(data['vertices']).reshape(-1,3);f=np.array(data['indices']).reshape(-1,3);objects=[(v,f,[240,224,191])];q=pp['post_center']
 for x in [-q,q]:
  for y in [-q,q]:
   objects.append((*box(x,y,(pp['height']+pp['foot_floor'])/2,25,25,pp['height']-pp['foot_floor']),WOOD));fv,ff=foot_mesh;objects.append((fv+[x,y,0],ff,BODY))
 for rail in data['structure']['wood_rails']:
  a=np.array(rail['start']);b=np.array(rail['end']);length=np.linalg.norm(b-a);angle=0 if b[0]>a[0] else math.pi/2;bv,bf=box(length/2,0,0,length,25,25);objects.append((transform(bv,angle,a),bf,WOOD))
 for ins in data['joint_instances']:
  n=ins['part'];jd=data['joints'][n];bv=np.array(jd['vertices']).reshape(-1,3);bf=np.array(jd['indices']).reshape(-1,3);objects.append((transform(bv,ins['angle'],np.array(ins['xyz'])),bf,BODY if n in ['female','male'] else LOCK))
 for x in [-q,q]:
  for y in [-q,q]:
   angle=0 if x<0 and y<0 else math.pi/2 if x>0 and y<0 else math.pi if x>0 else math.pi*1.5
   for j in range(pp['segments']+1):
    bv,bf=collar_meshes[j>0];z=pp['panel_bottom']-1.2 if j==0 else pp['height']-24 if j==pp['segments'] else pp['panel_bottom']+j*pp['segment_height']-12;objects.append((transform(bv,angle,np.array([x,y,z])),bf,BODY))
 render(im,(35+i*530,145,510,820),objects,view=(.65,-.95,.23),margin=20);d.text((90+i*530,1000),des['name'],font=font(24),fill='#27392f');d.text((90+i*530,1036),f"{pp['height']:.0f} mm overall • prototype",font=font(18),fill='#5c665e')
im.save(OUT/'standing-sleeve-three-renders.png');print('Rendered detail and three standing designs')
