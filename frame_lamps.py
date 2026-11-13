"""Four-post lamp studies: NumPy-only flat panels and printable joinery.
Dimensions are provisional millimeters; no physical fit/electrical claim.
"""
import math,hashlib
import numpy as np
import lamp_engine as engine
import print_geometry as pg
DEFAULTS=dict(rod_mm=25.,rod_clearance=.6,panel_mm=2.,panel_clearance=.4,width=190.,height=440.,cable_mm=3.,pattern='pearl',aperture_mm=3.2,aperture_web_mm=2.0,cols=8,rows=12,relief=False,crown='open',standing=False,stand_style='cross',illuminated_height=304.8,exposed_leg_height=None,rails=True,rail_mm=25.,lower_rail_z=70.,upper_rail_gap=65.,foot_wall=3.,foot_floor=2.4,foot_height=20.,collar_wall=2.8,receiver_length=9.,cap_mm=3.,dovetail_clearance=.3,light_type="LED",holder_bore=32.,holder_flange=45.,holder_height=18.,bulb_diameter=60.,bulb_height=110.,dovetail_head=12.,dovetail_neck=8.,dovetail_depth=6.,dovetail_height=24.,receiver_height=30.,locking_pin_mm=4.,wood_fixing_hole_mm=4.2)
DESIGNS=[
 ('atrium-pearl','Atrium Pearl','pearl',8,12,190,440,'open'),
 ('dewfall','Dewfall','graded',10,14,190,460,'rail'),
 ('reed-house','Reed House','slits',10,5,180,440,'rail'),
 ('folio','Folio','leaf',6,10,200,480,'open'),
 ('tideline','Tideline','wave',8,10,190,500,'rail'),
 ('moire','Moiré','diamond',8,14,190,440,'rail'),
 ('petal-house','Petal House','petal',6,10,200,460,'open'),
 ('window-house','Window House','window',4,7,210,480,'rail'),
 ('arbor','Arbor','arbor',7,11,190,500,'open'),
 ('opal-house','Opal House','solid',12,8,180,440,'rail'),
 ('cascade-house','Cascade House','cascade',8,12,190,480,'open'),
 ('braid-house','Braid House','braid',8,12,200,500,'rail')]
def catalog():
 table=[dict(id=i,name=n,kind='frame',pattern=p,crown=c,description='Four 25 mm square posts, replaceable '+p+' panels and '+('an open crown.' if c=='open' else 'a bordered crown.'),params=dict(DEFAULTS,pattern=p,cols=co,rows=ro,width=w,height=h,crown=c)) for i,n,p,co,ro,w,h,c in DESIGNS]
 standing=[]
 for i,n,pattern,style in [('standing-cross','Pearl / Standing','micro_round','cross'),('standing-tier','Reed / Standing','micro_hex','tier'),('standing-shelf','Folio / Standing','micro_oct','shelf')]:
  standing.append(dict(id=i,name=n,kind='frame',pattern=pattern,crown='open',description='Four clean exposed square posts with individual printed foot caps and a one-foot '+pattern+' light chamber. Dimensions provisional.',params=dict(DEFAULTS,standing=True,stand_style=style,width=220,height={'cross':1371.6,'tier':1524.,'shelf':1219.2}[style],exposed_leg_height={'cross':1066.8,'tier':1219.2,'shelf':914.4}[style],pattern=pattern)))
 return table+standing
def resolve(params):
 p=dict(DEFAULTS);p.update({k:v for k,v in params.items() if k in p})
 if p['standing'] and p['exposed_leg_height'] is not None:p['height']=float(p['exposed_leg_height'])+float(p['illuminated_height'])
 for key in ('rod_mm','rod_clearance','panel_mm','panel_clearance','width','height','cable_mm'):
  p[key]=float(p[key])
 if not all(math.isfinite(p[k]) for k in ('rod_mm','rod_clearance','panel_mm','panel_clearance','width','height','cable_mm')):raise ValueError('Dimensions must be finite.')
 if not 20<=p['rod_mm']<=32 or not .2<=p['rod_clearance']<=1.2:raise ValueError('Rod/fit clearance outside reviewed design range.')
 height_ok=1040<=p['height']<=1600 if p['standing'] else 320<=p['height']<=600
 if not 160<=p['width']<=220 or not height_ok:raise ValueError('Use width 160–220 mm and provisional height 320–600 mm.')
 if not 1.6<=p['panel_mm']<=3 or not .2<=p['panel_clearance']<=.8 or not 2<=p['cable_mm']<=6:raise ValueError('Panel or cable dimensions outside reviewed range.')
 ranges={'aperture_mm':(2.4,4.0),'aperture_web_mm':(1.6,4.0),'foot_wall':(2.4,5),'foot_floor':(2,4),'foot_height':(16,30),'collar_wall':(2.4,4),'receiver_length':(8,14),'cap_mm':(2.4,5),'rail_mm':(20,28),'lower_rail_z':(45,130),'upper_rail_gap':(45,90),'dovetail_clearance':(.2,.6),'holder_bore':(15,50),'holder_flange':(25,65),'holder_height':(10,40),'bulb_diameter':(40,90),'bulb_height':(60,160),'illuminated_height':(260,360),'dovetail_head':(10,16),'dovetail_neck':(6,10),'dovetail_depth':(5,9),'dovetail_height':(20,30),'receiver_height':(26,40),'locking_pin_mm':(3,4),'wood_fixing_hole_mm':(3.2,5.2)}
 for key,(low,high) in ranges.items():
  p[key]=float(p[key])
  if not math.isfinite(p[key]) or not low<=p[key]<=high:raise ValueError(key+' outside reviewed parameter range')
 if p['standing'] and p['rails'] and (p['rail_mm']+p['rod_clearance'])/2+2.8>=p['rod_mm']/2+4.3:raise ValueError('Rail shoes may collide at the corner; use a smaller rail section for this post size')
 if p['light_type'] in ('B22','E27') and p['holder_flange']<=p['holder_bore']+4:raise ValueError('Provisional holder flange must exceed the mounting opening')
 if p['dovetail_head']<=p['dovetail_neck']+2 or p['receiver_height']<p['dovetail_height']+4:raise ValueError('Dovetail head/neck or receiver stop clearance invalid')
 p['cols']=min(16,max(3,int(p['cols'])));p['rows']=min(24,max(4,int(p['rows'])))
 p['post_center']=(p['width']-p['rod_mm'])/2
 p['socket_mm']=p['rod_mm']+p['rod_clearance'];p['socket_wall']=float(p['collar_wall'])
 p['receiver_back']=p['socket_mm']/2+2.8
 p['panel_width']=2*p['post_center']-2*(p['receiver_back']+.2)
 p['panel_height']=float(p['illuminated_height']) if p['standing'] else p['height']-70
 p['exposed_leg_height']=p['height']-p['panel_height'] if p['standing'] else None
 p['panel_bottom']=p['height']-p['panel_height'] if p['standing'] else 35
 p['light_z']=p['panel_bottom']+(float(p['holder_height'])+float(p['bulb_height'])/2 if p['light_type'] in ('B22','E27') else p['panel_height']/2)
 p['segments']=math.ceil(p['panel_height']/230)
 p['segment_height']=p['panel_height']/p['segments']
 p['slot_mm']=p['panel_mm']+p['panel_clearance']
 if p['panel_width']<85:raise ValueError('Frame leaves too little panel width.')
 return p

def slab(triangles,thick):
 t=np.round(np.asarray(triangles,float),6);uv,inv=np.unique(t.reshape(-1,2),axis=0,return_inverse=True);f=inv.reshape(-1,3)
 area=np.cross(uv[f[:,1]]-uv[f[:,0]],uv[f[:,2]]-uv[f[:,0]])
 f=f[np.abs(area)>1e-8];area=area[np.abs(area)>1e-8];f[area<0]=f[area<0][:,::-1]
 n=len(uv);v=np.concatenate([np.column_stack([uv,np.full(n,thick)]),np.column_stack([uv,np.zeros(n)])])
 edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);_,ix,cnt=np.unique(np.sort(edges,axis=1),axis=0,return_index=True,return_counts=True);e=edges[ix[cnt==1]]
 faces=np.concatenate([f,f[:,::-1]+n,np.column_stack([e[:,0],e[:,1]+n,e[:,1]]),np.column_stack([e[:,0],e[:,0]+n,e[:,1]+n])])
 return v.astype('float32'),faces.astype('int32')
def panel(params,segment=0):
 p=resolve(params);w=p['panel_width'];h=p['segment_height'];
 if p['pattern'] in ('micro_round','micro_hex','micro_oct'):return _micro_panel(p)
 co=p['cols']+2;ro=max(4,round(p['rows']/p['segments']))+2;cw=w/co;ch=h/ro;t=[];count=0
 # Shared rectangular tile edges, each with eight segments. Circular holes are
 # polygonal circles in the FLAT XY printing orientation, with vertical walls.
 n=32;ang=np.linspace(-3*math.pi/4,5*math.pi/4,n,endpoint=False)
 unit=np.stack([np.cos(ang),np.sin(ang)],1)
 outer=np.concatenate([np.column_stack([np.linspace(-cw/2,cw/2,8,endpoint=False),np.full(8,-ch/2)]),np.column_stack([np.full(8,cw/2),np.linspace(-ch/2,ch/2,8,endpoint=False)]),np.column_stack([np.linspace(cw/2,-cw/2,8,endpoint=False),np.full(8,ch/2)]),np.column_stack([np.full(8,-cw/2),np.linspace(ch/2,-ch/2,8,endpoint=False)])])
 for r in range(ro):
  for c in range(co):
   center=np.array([(c+.5)*cw,(r+.5)*ch]);o=outer+center
   holes=p['pattern']!='solid' and 0<r<ro-1 and 0<c<co-1
   if not holes:
    for k in range(n):t.append([o[k],o[(k+1)%n],center])
    continue
   count+=1;rx=max(.8,cw/2-2.4);ry=max(.8,ch/2-2.4);kind=p['pattern'];u=(r/(ro-1)+segment)/p['segments'];theta=0
   if kind in ('pearl','graded','petal'):
    rx=ry=min(rx,ry)*(.78 if kind=='pearl' else 1)
   if kind=='graded':rx*=.50+.50*math.sin(math.pi*u)**2;ry=rx
   if kind=='slits':rx=min(rx,2.0)
   if kind=='leaf':rx*=.42;theta=(-1 if c%2 else 1)*.25
   if kind=='wave':rx*=.44;theta=.38*math.sin(c*.8+r*.65)
   if kind=='arbor':rx*=.36;theta=(-1 if (c+r)%2 else 1)*.32
   if kind=='cascade':rx*=.48+.35*u;ry*=.55+.40*u
   if kind=='braid':ry*=.32;theta=(-1 if r%2 else 1)*.40
   direction=outer/np.linalg.norm(outer,axis=1)[:,None];angle=np.arctan2(direction[:,1],direction[:,0]);local=angle-theta
   if kind=='diamond':rad=1/(np.abs(np.cos(local))/rx+np.abs(np.sin(local))/ry)
   elif kind=='window':rad=np.minimum(rx/np.maximum(np.abs(np.cos(local)),1e-9),ry/np.maximum(np.abs(np.sin(local)),1e-9))
   elif kind=='petal':rad=min(rx,ry)*.88*(1+.11*np.cos(5*angle))
   else:rad=1/np.sqrt((np.cos(local)/rx)**2+(np.sin(local)/ry)**2)
   inner=direction*rad[:,None]
   scale=min(1,(cw/2-2.4)/np.abs(inner[:,0]).max(),(ch/2-2.4)/np.abs(inner[:,1]).max());inner*=scale
   inner+=center
   for k in range(n):
    j=(k+1)%n;t.extend([[o[k],o[j],inner[j]],[o[k],inner[j],inner[k]]])
 v,f=slab(t,p['panel_mm']);return v,f,dict(apertures=count,width_mm=w,height_mm=h,thickness_mm=p['panel_mm'],minimum_cell_web_design_mm=4.8)

def _micro_panel(p):
 """Physical-size apertures in a flat panel; unchanged receiver border/interface."""
 w=p['panel_width'];h=p['segment_height'];diam=p['aperture_mm'];web=p['aperture_web_mm'];border=4.0
 # Reserve full, unperforated 4mm edges for handling and panel-receiver engagement.
 nx=max(1,int((w-2*border)/(diam+web)));ny=max(1,int((h-2*border)/(diam+web)))
 cw=(w-2*border)/nx;ch=(h-2*border)/ny
 n=24;angle=np.arange(n)*2*math.pi/n;direction=np.column_stack([np.cos(angle),np.sin(angle)])
 radius=np.minimum(cw/2/np.maximum(abs(direction[:,0]),1e-12),ch/2/np.maximum(abs(direction[:,1]),1e-12))
 outer=direction*radius[:,None]
 sides={'micro_round':24,'micro_hex':6,'micro_oct':8}[p['pattern']]
 # Uniform angular samples include every polygon vertex for n divisible by6/8.
 if sides==24:inner=direction*(diam/2)
 else:
  local=(angle+math.pi/sides)%(2*math.pi/sides)-math.pi/sides
  radial=(diam/2*math.cos(math.pi/sides))/np.cos(local)
  inner=direction*radial[:,None]
 triangles=[]
 for row in range(ny):
  for col in range(nx):
   centre=np.array([border+(col+.5)*cw,border+(row+.5)*ch]);o=outer+centre;i=inner+centre
   for k in range(n):
    j=(k+1)%n;triangles.extend([[o[k],o[j],i[j]],[o[k],i[j],i[k]]])
 # Connect the perforated grid to a solid outer border with matching vertices.
 # Every boundary tile edge contributes a quad to its projected panel edge.
 for row in range(ny):
  for col in range(nx):
   centre=np.array([border+(col+.5)*cw,border+(row+.5)*ch]);o=outer+centre
   for k in range(n):
    j=(k+1)%n;a=o[k];b=o[j]
    target=None
    if row==0 and abs(a[1]-border)<1e-7 and abs(b[1]-border)<1e-7:target=lambda q:np.array([q[0],0.])
    elif row==ny-1 and abs(a[1]-(h-border))<1e-7 and abs(b[1]-(h-border))<1e-7:target=lambda q:np.array([q[0],h])
    elif col==0 and abs(a[0]-border)<1e-7 and abs(b[0]-border)<1e-7:target=lambda q:np.array([0.,q[1]])
    elif col==nx-1 and abs(a[0]-(w-border))<1e-7 and abs(b[0]-(w-border))<1e-7:target=lambda q:np.array([w,q[1]])
    if target:
     aa=target(a);bb=target(b);triangles.extend([[a,b,bb],[a,bb,aa]])
 for x,y in [(0,0),(w-border,0),(0,h-border),(w-border,h-border)]:
  a=np.array([x,y]);b=a+[border,0];c=a+[border,border];d=a+[0,border];triangles.extend([[a,b,c],[a,c,d]])
 v,f=slab(triangles,p['panel_mm'])
 return v,f,dict(apertures=nx*ny,width_mm=w,height_mm=h,thickness_mm=p['panel_mm'],aperture_shape=p['pattern'],aperture_max_width_mm=diam,aperture_polygon_sides=sides,pitch_mm=[cw,ch],minimum_cell_web_design_mm=min(cw,ch)-diam,solid_border_mm=border,print_orientation='flat XY',nozzle_target_mm=.4,geometry_revision='frame-small-perforations-v1',optical_performance_verified=False)


def layers_mesh(masks,zlevels,step=.2,x0=0.,y0=0.):
 """Union extrusion with explicit layer levels: no hidden internal faces."""
 quads=[];hh,ww=masks[0].shape
 for k,mask in enumerate(masks):
  for j,i in np.argwhere(mask):
   x=x0+i*step;y=y0+j*step;za=zlevels[k];zb=zlevels[k+1]
   a=[x,y,za];b=[x+step,y,za];c=[x+step,y+step,za];d=[x,y+step,za];aa=[x,y,zb];bb=[x+step,y,zb];cc=[x+step,y+step,zb];dd=[x,y+step,zb]
   if k==0 or not masks[k-1][j,i]:quads.append([a,d,c,b])
   if k==len(masks)-1 or not masks[k+1][j,i]:quads.append([aa,bb,cc,dd])
   if i==0 or not mask[j,i-1]:quads.append([a,aa,dd,d])
   if i==ww-1 or not mask[j,i+1]:quads.append([b,c,cc,bb])
   if j==0 or not mask[j-1,i]:quads.append([a,b,bb,aa])
   if j==hh-1 or not mask[j+1,i]:quads.append([d,dd,cc,c])
 q=np.round(np.asarray(quads,float),6);v,inv=np.unique(q.reshape(-1,3),axis=0,return_inverse=True);qf=inv.reshape(-1,4);f=np.concatenate([qf[:,[0,1,2]],qf[:,[0,2,3]]]);return v.astype('float32'),f.astype('int32')
def connector(params,coupon=False,through=False):
 p=resolve(params);step=.2;half=p['socket_mm']/2;out=half+p['socket_wall'];limit=math.ceil((out+11)/step)*step
 xx,yy=np.meshgrid(np.arange(-limit,limit,step)+step/2,np.arange(-limit,limit,step)+step/2)
 ring=(np.abs(xx)<=out)&(np.abs(yy)<=out)&~((np.abs(xx)<half)&(np.abs(yy)<half))
 if coupon:return layers_mesh([ring],[0,8],step,-limit,-limit)
 rails=((xx>=out-1)&(xx<out+p['receiver_length'])&(np.abs(yy)<=p['slot_mm']/2+2.4))|((yy>=out-1)&(yy<out+p['receiver_length'])&(np.abs(xx)<=p['slot_mm']/2+2.4))
 slots=((xx>out)&(np.abs(yy)<p['slot_mm']/2))|((yy>out)&(np.abs(xx)<p['slot_mm']/2))
 wire_inner=p['cable_mm']+.6;wire=(xx<=-out+1)&(xx>=-out-wire_inner-2.4)&(np.abs(yy)<=wire_inner/2+2.4)
 wire_cut=(xx<-out)&(np.abs(yy)<wire_inner/2)
 mask=(ring|rails|wire)&~(slots|wire_cut)
 shelf=(xx>=out-1.8)&(xx<=out+7)&(yy>=out-1.8)&(yy<=out+7)
 floor=(ring|rails|wire|shelf)&~wire_cut
 return layers_mesh([mask],[0,24],step,-limit,-limit) if through else layers_mesh([floor,mask],[0,1.2,24],step,-limit,-limit)
def cable_guide(params):
 p=resolve(params);step=.4;length=min(220,p['height']/math.ceil(p['height']/220));inside=p['cable_mm']+.6;w=inside+4.8
 x=np.arange(0,length,step)+step/2;y=np.arange(-w/2,w/2,step)+step/2;xx,yy=np.meshgrid(x,y);base=np.ones_like(xx,dtype=bool);rail=np.abs(yy)>=inside/2
 return layers_mesh([base,rail],[0,1.2,p['cable_mm']+2.0],step,0,-w/2)
def check_part(v,f,allow_supports=False):
 ok,metrics=engine.verify_mesh(v,f);screen=pg.manufacturing_report(v,f)
 if not ok or (not screen['passed'] and not allow_supports) or np.any(np.ptp(v,axis=0)>250.001):raise ValueError(dict(metrics=metrics,screen=screen))
 return dict(mesh_sha256=hashlib.sha256(v.tobytes()+f.tobytes()).hexdigest(),metrics=metrics,screen=screen,requires_slicer_orientation_or_supports=not screen['passed'])
def preview(params):
 p=resolve(params);v,f,info=panel(p);vertices=[];faces=[];offset=0
 for side in range(4):
  for segment in range(p['segments']):
   v,f,info=panel(p,segment)
   vv=v.copy();vv[:,0]-=p['panel_width']/2
   # panel XY flat becomes XZ upright; thickness points toward inner cavity.
   xyz=np.column_stack([vv[:,0],np.full(len(vv),-p['post_center'])+vv[:,2]-p['panel_mm']/2,vv[:,1]+p['panel_bottom']+segment*p['segment_height']])
   a=side*math.pi/2;rot=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);xyz[:,:2]=xyz[:,:2]@rot.T
   vertices.append(xyz);faces.append(f[:,::-1]+offset);offset+=len(vv)
 verts=np.concatenate(vertices);idx=np.concatenate(faces)
 latest=latest_preview_parts(p)
 joints=None
 if latest['available']:
  joints={name:_preview_mesh_data(path) for name,path in {
   'female':'output/revamp/one-piece-female/A-one-piece-female-sleeve-v3.stl',
   'male':'output/revamp/selected-wedge-axial/D-male-axial-rail-cup.stl'}.items()}
 return dict(ok=True,joints=joints,joint_instances=joint_instances(p) if joints else [],latest_parts=latest,vertices=verts.astype(float).ravel().tolist(),indices=idx.ravel().tolist(),frame=p,structure=standing_structure(p) if p['standing'] else None,panel_info=info,notes=['Nominal rod size; verify with calipers and coupon.','Flat panel orientation for printing; geometry-only checks.','Physical fit, racking, tipping, heat and cable suitability unverified.'])


def _preview_mesh_data(relative_path):
 """Read an actual exported revision; never stretch a mating interface."""
 import pathlib
 path=pathlib.Path(__file__).resolve().parent/relative_path
 if path.suffix=='.npz':
  with np.load(path) as data:v,f=data['v'],data['f']
 else:
  raw=path.read_bytes();count=int.from_bytes(raw[80:84],'little')
  dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
  if len(raw)!=84+count*50:raise ValueError('Unexpected preview STL format: '+path.name)
  triangles=np.frombuffer(raw,dtype=dtype,count=count,offset=84)['vertices']
  v,ix=np.unique(np.round(triangles.reshape(-1,3),6),axis=0,return_inverse=True);f=ix.reshape(-1,3)
 return dict(vertices=v.astype(float).ravel().tolist(),indices=f.ravel().tolist())


def latest_preview_parts(params):
 """Revision-specific standing assembly meshes; custom interfaces stay unsupported."""
 import pathlib
 p=resolve(params)
 fixed=dict(rod_mm=25.,width=220.,rod_clearance=.6,collar_wall=2.8,panel_mm=2.,panel_clearance=.4,receiver_length=9.,cap_mm=3.,upper_rail_gap=65.,rail_mm=25.,receiver_height=30.,dovetail_clearance=.3,dovetail_head=12.,dovetail_neck=8.,dovetail_depth=6.,dovetail_height=24.,wood_fixing_hole_mm=4.2)
 mismatch=[k for k,value in fixed.items() if abs(float(p[k])-value)>1e-6]
 if not p['standing'] or not p['rails']:
  return dict(available=False,revision='standing-preview-v3',reason='Latest standing assembly requires the standing rail configuration.',meshes={},instances=[])
 if mismatch:
  return dict(available=False,revision='standing-preview-v3',reason='Latest checked connector geometry is unavailable for these custom dimensions.',unsupported_parameters=mismatch,meshes={},instances=[])
 paths={'bottom-holder':'output/revamp/retained-tray-v3/snap-reinforced-holder.npz','tray':'output/revamp/retained-tray-v3/flat-tray.npz','mid-guide':'output/revamp/shade-support-v1/mid-panel-guide.npz','top-cap':'output/revamp/shade-support-v1/top-panel-grip-cap.npz'}
 root=pathlib.Path(__file__).resolve().parent
 missing=[name for name,path in paths.items() if not (root/path).is_file()]
 if missing:return dict(available=False,revision='standing-preview-v3',reason='Latest assembly preview assets are missing.',missing_parts=missing,meshes={},instances=[])
 meshes={name:_preview_mesh_data(path) for name,path in paths.items()};items=[];q=p['post_center']
 for x,y,angle in [(-q,-q,0),(-q,q,math.pi*1.5),(q,-q,math.pi/2),(q,q,math.pi)]:
  items.append(dict(part='bottom-holder',angle=angle,xyz=[x,y,p['panel_bottom']-52.8],group='base'))
  for j in range(1,p['segments']):items.append(dict(part='mid-guide',angle=angle,xyz=[x,y,p['panel_bottom']+j*p['segment_height']-12],group='base'))
  items.append(dict(part='top-cap',angle=angle,xyz=[x,y,p['height']-24],group='base'))
 items.append(dict(part='tray',angle=0,xyz=[0,0,p['panel_bottom']],group='light'))
 return dict(available=True,revision='standing-preview-v3-opposed-sleeve-integral-holder-snaps',reason='Current prototype assembly; physical strength and bulb-holder fit remain unverified.',meshes=meshes,instances=items,sources={name:dict(path=path,sha256=hashlib.sha256((root/path).read_bytes()).hexdigest()) for name,path in paths.items()})



def cable_cover(params):
 p=resolve(params);length=min(220,p['height']/math.ceil(p['height']/220));w=p['cable_mm']+.6+4.8
 return slab([[[0,0],[length,0],[length,w]],[[0,0],[length,w],[0,w]]],1.2)

def strain_relief(params):
 p=resolve(params);step=.4;x=np.arange(0,60,step)+step/2;y=np.arange(0,30,step)+step/2;xx,yy=np.meshgrid(x,y)
 # Accessible tie slots and large round bosses. Cable bend-radius suitability
 # and clamping loads remain material-specific physical checks.
 slots=((np.abs(xx-8)<1.6)|(np.abs(xx-52)<1.6))&((np.abs(yy-6)<1.6)|(np.abs(yy-24)<1.6))
 base=~slots;boss=np.zeros_like(base)
 for cx,cy in [(10.8,15),(30,15),(49.2,15)]:boss|=(xx-cx)**2+(yy-cy)**2<=6**2
 return layers_mesh([base,boss],[0,2,10],step)

def light_tray(params):
 p=resolve(params);w=p['panel_width'];step=.4;x=np.arange(0,w,step)+step/2;y=x.copy();xx,yy=np.meshgrid(x,y)
 # Tie holes plus open edge cable entry; no unverified electrical holder mount.
 slots=((np.abs(xx-w/2)<2)&(np.abs(yy-w/2-12)<3))|((np.abs(xx-w/2)<2)&(np.abs(yy-w/2+12)<3))
 if p['light_type'] in ('B22','E27'):slots|=(xx-w/2)**2+(yy-w/2)**2<(float(p['holder_bore'])/2)**2
 cable=(xx<w/2+2)&(xx>w/2-2)&(yy<12)
 return layers_mesh([~(slots|cable)],[0,3],step)

def export_kit(params,outdir):
 import pathlib,json,zipfile
 p=resolve(params);out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True);records={};meshes={}
 for i in range(p['segments']):
  v,f,info=panel(p,i);meshes['panel-'+str(i+1)]=(v,f)
 meshes.update({'top-retaining-cap':stop_cap(p),'corner-bottom':connector(p),'corner-through':connector(p,through=True),'rod-fit-coupon':connector(p,True),'cable-guide':cable_guide(p),'cable-cover':cable_cover(p),'strain-relief':strain_relief(p),'light-tray':light_tray(p)})
 if p['standing']:
  meshes['foot-cap']=foot_cap(p)
  if p['rails']:
   for name in ['female','male','post-wedge','post-pad']:meshes['dovetail-'+name]=_cad_dovetail(p,name)
 # Validate every mesh before writing any product file.
 for name,(v,f) in meshes.items():records[name]=check_part(v,f,allow_supports=name.startswith('dovetail-'))
 for name,(v,f) in meshes.items():engine.write_binary_stl(str(out/(name+'.stl')),v,f)
 manifest=dict(params=p,parts=records,bill_of_parts=[{'item':'nominal square posts','count':4,'cut_height_mm':p['height']-(p['foot_floor'] if p['standing'] else 0),'square_mm':p['rod_mm'],'supplied_by_owner':True},{'item':'panel segment','count':4*p['segments']},{'item':'bottom corner','count':4},{'item':'through corner','count':4*p['segments']},{'item':'top retaining cap','count':4},{'item':'light tray','count':1},{'item':'cable guide/cover lengths','count':math.ceil(p['height']/220)},{'item':'strain relief','count':1},{'item':'fit coupon','count':1}],fit=dict(rod_bore_mm=p['socket_mm'],rod_total_clearance_mm=p['rod_clearance'],panel_slot_mm=p['slot_mm'],panel_total_clearance_mm=p['panel_clearance'],receiver_insertion_mm=8.8,cable_channel_mm=p['cable_mm']+.6),assembly=['Measure actual posts; print coupon before connector batch.','Slide bottom and through collars onto posts; keep receivers facing inward.','Seat light tray on bottom corner shelves, without forcing it.','Insert each panel edge into 8.8 mm receivers; stack the segments so lower panels bear the upper ones. Through collars grip the seam.','Fit four top retaining caps using accessible owner-selected fasteners into post ends. Remove caps and upper collars to replace panels. Screw pull-out and retention capability require physical testing.','Route low-voltage cable through the open tray entry, outside one solid post in accessible guide lengths, then inward to LED. Tie-based cover/strain-relief attachment needs a physical pull test.','Remove upper collars and lift panel stack for replacement; no trapped screws or hidden glued joints.'],unverified=['Actual rod size, moisture/movement and material','Clearance, sliding fit and panel retention','Racking, stability/tipping and connector loads','Cable bend radius, strain relief and thermal/electrical suitability','LED, diffuser and holder selection'],screening='Mesh integrity and A1 envelope checked. Dovetail parts may require supports or changed orientation: inspect their recorded overhang screens in your slicer. Assembled tall lamp is not a single printable part.')
 if p['standing']:
  manifest['standing_structure']=standing_structure(p)
  manifest['bill_of_parts'].append({'item':'individual foot cap','count':4})
  if p['rails']:manifest['bill_of_parts'] += [{'item':'horizontal timber rail','count':8,'section_mm':p['rail_mm'],'material_provisional':True},{'item':'dual female wedge sleeve','count':8},{'item':'dovetail male rail shoe','count':16},{'item':'post tightening wedge','count':8},{'item':'post pressure pad','count':8},{'item':'axial rail screw','count':16,'hardware_provisional':True}]
  manifest['assembly'].append('Fit one individual cap to each exposed post. Print caps with closed floor on the bed and open socket upward. Two horizontal rail frames are proposed; diagonal braces, shelves and outriggers are excluded. Selected rail joint: wedge-tightened female PETG sleeves on uprights with separate pressure pads, male cups with one axial screw per rail end, and downward dovetail insertion. Rail screws remain provisional; no positive anti-lift latch is claimed. Actual fit and stability remain unverified.')
 (out/'assembly.json').write_text(json.dumps(manifest,indent=2))
 with zipfile.ZipFile(out/'parts-kit.zip','w',zipfile.ZIP_DEFLATED) as z:
  for name in meshes:z.write(out/(name+'.stl'),name+'.stl')
  z.write(out/'assembly.json','assembly.json')
 return manifest

def standing_structure(params):
 p=resolve(params)
 rails=[]
 if p['rails']:
  q=p['post_center'];inset=p['socket_mm']/2+p['socket_wall']-1+p['dovetail_depth']+9.9
  for z in [float(p['lower_rail_z']),p['panel_bottom']-float(p['upper_rail_gap'])]:
   for y in [-q,q]:rails.append(dict(start=[-q+inset,y,z],end=[q-inset,y,z],label='horizontal frame rail',square_mm=p['rail_mm']))
   for x in [-q,q]:rails.append(dict(start=[x,-q+inset,z],end=[x,q-inset,z],label='horizontal frame rail',square_mm=p['rail_mm']))
 return dict(wood_rails=rails,shelf=None,foot_caps=4,footprint_mm=[p['width']+8,p['width']+8],physical_stability_verified=False)
def foot_cap(params):
 p=resolve(params);half=p['socket_mm']/2;outside=half+float(p['foot_wall']);step=.2;xx,yy=np.meshgrid(np.arange(-outside,outside,step)+step/2,np.arange(-outside,outside,step)+step/2)
 floor=np.ones_like(xx,dtype=bool);wall=~((np.abs(xx)<half)&(np.abs(yy)<half))
 return layers_mesh([floor,wall],[0,float(p['foot_floor']),float(p['foot_height'])],step,-outside,-outside)

def stop_cap(params):
 p=resolve(params);half=(p['socket_mm']+2*p['socket_wall']+18)/2;angles=np.arange(32)*2*math.pi/32;u=np.stack([np.cos(angles),np.sin(angles)],1);outer=u*(half/np.maximum(np.abs(u[:,0]),np.abs(u[:,1])))[:,None];inner=u*2.2;t=[]
 for i in range(32):
  j=(i+1)%32;t.extend([[outer[i],outer[j],inner[j]],[outer[i],inner[j],inner[i]]])
 return slab(t,float(p['cap_mm']))

def _cad_dovetail(params,kind):
 import pathlib,json,subprocess,os
 p=resolve(params);root=pathlib.Path(__file__).resolve().parent;cache=root/'output/frame-cache';cache.mkdir(parents=True,exist_ok=True);key=hashlib.sha256(('wedge-axial-v5'+json.dumps({k:p[k] for k in ('rod_mm','socket_mm','socket_wall','rail_mm','rod_clearance','dovetail_clearance','dovetail_head','dovetail_neck','dovetail_depth','dovetail_height','receiver_height','locking_pin_mm','wood_fixing_hole_mm')},sort_keys=True)).encode()).hexdigest()[:20];result=cache/(kind+'-'+key+'.npz');inputs=cache/(key+'.json')
 if not result.exists():
  inputs.write_text(json.dumps(p));runtime='/Applications/VibeCAD.app/Contents/Resources/bin/python'
  if not pathlib.Path(runtime).is_file():raise ValueError('Exact dovetail cross-hole geometry requires the installed FreeCAD runtime.')
  process=subprocess.run([runtime,str(root/'tools/cad_dovetail_mesh.py'),str(inputs),str(result),kind],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1'),timeout=90)
  if process.returncode:raise ValueError('Dovetail CAD failed: '+process.stderr[-1500:])
 data=np.load(result);return data['v'],data['f']
def dovetail_female(params):return _cad_dovetail(params,'female')
def dovetail_male(params):return _cad_dovetail(params,'male')

def joint_instances(params,legacy=False):
 """Latest one-piece sleeve placement; legacy wedge inventory for archived exports."""
 p=resolve(params);q=p['post_center'];anchor=p['socket_mm']/2+p['socket_wall']-1;zc=3+(p['rail_mm']+p['rod_clearance'])/2;items=[]
 for x in [-q,q]:
  for y in [-q,q]:
   corner=0 if x<0 and y<0 else math.pi/2 if x>0 and y<0 else math.pi if x>0 else math.pi*1.5
   for level in [p['lower_rail_z'],p['panel_bottom']-p['upper_rail_gap']]:
    z=level-2-zc
    for name in (['female','post-wedge','post-pad'] if legacy else ['female']):items.append(dict(part=name,angle=corner,xyz=[x,y,z]))
    for a in [0 if x<0 else math.pi, math.pi/2 if y<0 else math.pi*1.5]:
     offset=anchor+p['dovetail_depth']+6.6;items.append(dict(part='male',angle=a,xyz=[x+math.cos(a)*offset,y+math.sin(a)*offset,z+2]))
 return items
