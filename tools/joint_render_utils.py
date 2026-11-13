import math,numpy as np
from PIL import Image,ImageDraw
def box(x,y,z,w,d,h):
 v=np.array([[x+a*w/2,y+b*d/2,z+c*h/2] for c in [-1,1] for b in [-1,1] for a in [-1,1]],float)
 f=np.array([[0,2,3],[0,3,1],[4,5,7],[4,7,6],[0,1,5],[0,5,4],[2,6,7],[2,7,3],[0,4,6],[0,6,2],[1,3,7],[1,7,5]])
 return v,f
BODY=[89,108,96];LOCK=[202,150,76];WOOD=[172,135,94]
def transform(v,angle,xyz):
 v=v.copy();c,s=math.cos(angle),math.sin(angle);v[:,:2]=v[:,:2]@np.array([[c,-s],[s,c]]).T;return v+xyz

def render(im,rect,objects,view=(.75,.95,.6),margin=25):
 ts=[];cs=[]
 for v,f,col in objects:ts.append(v[f]);cs.append(np.tile(col,(len(f),1)))
 t=np.concatenate(ts);colors=np.concatenate(cs);view=np.array(view,float);view/=np.linalg.norm(view);right=np.cross(view,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,view)
 normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 vis=normal@view>0;t=t[vis];normal=normal[vis];colors=colors[vis];uv=np.stack([t@right,t@up],-1);lo=uv.reshape(-1,2).min(0);hi=uv.reshape(-1,2).max(0);x,y,w,h=rect;scale=min((w-2*margin)/(hi[0]-lo[0]),(h-2*margin)/(hi[1]-lo[1]));uv=(uv-(lo+hi)/2)*scale;uv[:,:,0]+=x+w/2;uv[:,:,1]=y+h/2-uv[:,:,1];light=np.array([.3,.2,.92]);shade=(.50+.5*np.maximum(normal@light,0))[:,None]*colors;draw=ImageDraw.Draw(im)
 # Per-pixel depth resolves interleaving wood/connector faces correctly.
 pixels=np.array(im);depthbuf=np.full((im.height,im.width),-np.inf,dtype=np.float32);depth=t@view
 for i,pts in enumerate(uv):
  xmin=max(0,int(np.floor(pts[:,0].min())));xmax=min(im.width-1,int(np.ceil(pts[:,0].max())));ymin=max(0,int(np.floor(pts[:,1].min())));ymax=min(im.height-1,int(np.ceil(pts[:,1].max())))
  if xmax<xmin or ymax<ymin:continue
  a,b,c=pts;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-9:continue
  yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1];xx=xx+.5;yy=yy+.5
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
  z=u*depth[i,0]+v*depth[i,1]+w*depth[i,2];db=depthbuf[ymin:ymax+1,xmin:xmax+1];mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(z>db)
  db[mask]=z[mask];pixels[ymin:ymax+1,xmin:xmax+1][mask]=shade[i].astype(np.uint8)
 im.paste(Image.fromarray(pixels))
 def project(point):
  point=np.asarray(point);a=np.array([point@right,point@up]);a=(a-(lo+hi)/2)*scale;return np.array([rect[0]+rect[2]/2+a[0],rect[1]+rect[3]/2-a[1]])
 return project
