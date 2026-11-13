"""Offline actual panel/post geometry thumbnails for frame studies."""
import sys,pathlib,json,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import frame_lamps as m,numpy as np
from PIL import Image,ImageDraw
ROOT=pathlib.Path(__file__).resolve().parents[1]
def box(x,y,z,w,h,d):
 v=np.array([[x+a*w/2,y+b*h/2,z+c*d/2] for c in [-1,1] for b in [-1,1] for a in [-1,1]],float)
 f=np.array([[0,2,3],[0,3,1],[4,5,7],[4,7,6],[0,1,5],[0,5,4],[2,6,7],[2,7,3],[0,4,6],[0,6,2],[1,3,7],[1,7,5]])
 return v,f
def beam(a,b,width):
 a=np.array(a,float);b=np.array(b,float);axis=b-a;length=np.linalg.norm(axis);z=axis/length;helper=np.array([0,0,1]) if abs(z[2])<.9 else np.array([0,1,0]);x=np.cross(helper,z);x/=np.linalg.norm(x);y=np.cross(z,x);v,f=box(0,0,0,width,width,length);return v@np.stack([x,y,z])+(a+b)/2,f
for design in m.catalog():
 if len(sys.argv)>1 and design["id"] not in sys.argv[1:]:continue
 data=m.preview(design['params']);p=data['frame'];v=np.asarray(data['vertices']).reshape(-1,3);f=np.asarray(data['indices']).reshape(-1,3);tri=[v[f]];col=[np.full((len(f),3),[240,233,218])]
 for x in [-p['post_center'],p['post_center']]:
  for y in [-p['post_center'],p['post_center']]:
   bv,bf=box(x,y,p['height']/2+(1.2 if p['standing'] else 0),p['rod_mm'],p['rod_mm'],p['height']-(2.4 if p['standing'] else 0));tri.append(bv[bf]);col.append(np.full((len(bf),3),[158,127,94]))
 if p['standing']:
  structure=m.standing_structure(p)
  for x in [-p['post_center'],p['post_center']]:
   for y in [-p['post_center'],p['post_center']]:
    bv,bf=box(x,y,10,p['socket_mm']+6,p['socket_mm']+6,20);tri.append(bv[bf]);col.append(np.full((len(bf),3),[100,108,87]))
  for rail in structure['wood_rails']:
   bv,bf=beam(rail['start'],rail['end'],rail['square_mm']);tri.append(bv[bf]);col.append(np.full((len(bf),3),[158,127,94]))
  if data.get('joints'):
   for ins in data['joint_instances']:
    jd=data['joints'][ins['part']];bv=np.array(jd['vertices']).reshape(-1,3);bf=np.array(jd['indices']).reshape(-1,3);angle=ins['angle'];rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);bv[:,:2]=bv[:,:2]@rot.T;bv+=np.array(ins['xyz']);tri.append(bv[bf]);col.append(np.full((len(bf),3),[100,108,87] if ins['part'] in ['female','male'] else [188,137,75]))
  if structure['shelf']:

   shelf=structure['shelf'];bv,bf=box(0,0,shelf['z_mm'],shelf['width_mm'],shelf['depth_mm'],shelf['thickness_mm']);tri.append(bv[bf]);col.append(np.full((len(bf),3),[158,127,94]))
 t=np.concatenate(tri);colors=np.concatenate(col);view=np.array([.65,-.95,.23]);view/=np.linalg.norm(view);right=np.cross(view,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,view);normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12);vis=normal@view>0;t=t[vis];colors=colors[vis];normal=normal[vis];uv=np.stack([t@right,t@up],-1);lo=uv.reshape(-1,2).min(0);hi=uv.reshape(-1,2).max(0);scale=min(190/(hi[0]-lo[0]),256/(hi[1]-lo[1]));uv=(uv-(lo+hi)/2)*scale;uv[:,:,0]+=130;uv[:,:,1]=153-uv[:,:,1];shade=(.60+.4*np.clip(normal@np.array([-.3,-.6,.74]),0,1))[:,None]*colors;depth=t.mean(1)@view;im=Image.new('RGB',(260,306),(242,241,233));draw=ImageDraw.Draw(im);draw.ellipse((62,282,213,297),fill=(221,221,208))
 for i in np.argsort(depth):draw.polygon([tuple(x) for x in uv[i]],fill=tuple(shade[i].astype(int)))
 im.save(ROOT/'assets/customer/catalog'/(design['id']+'.png'),optimize=True);print(design['name'],flush=True)
