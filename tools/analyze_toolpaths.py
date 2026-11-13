"""Conservative 0.20 mm raster screen of emitted extrusion footprints.
Not a physical print guarantee or a full slicer support implementation.
"""
import re,math,json,argparse,numpy as np
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('gcode',type=Path)
parser.add_argument('--max-layer',type=int)
parser.add_argument('--output',type=Path)
cli_args=parser.parse_args();source=cli_args.gcode
STEP=.2;ORIGIN=0.;SIZE=1280
prev=np.zeros((SIZE,SIZE),bool);curr=prev.copy()
layer=0;feature='Custom';width=.42;x=y=z=0.;relative=True
samples=[];sections=[];section=None;islands=[];layerstats=[]
rx=re.compile(r'([XYZEFIJK])([-+]?(?:\d*\.\d+|\d+))')

def flush_points():
 global samples
 if not samples:return
 pts=np.asarray(samples);samples=[]
 # Each sample carries the actual line width; adding half a raster diagonal
 # is conservative and can hide gaps below the 0.2 mm screening resolution.
 for first in range(0,len(pts),10000):
  p=pts[first:first+10000];ix=np.floor(p[:,0]/STEP).astype(int);iy=np.floor(p[:,1]/STEP).astype(int)
  rad=p[:,2]/2+STEP*.7072
  rr=int(np.ceil(rad.max()/STEP))+1
  for dx in range(-rr,rr+1):
   for dy in range(-rr,rr+1):
    xx=ix+dx;yy=iy+dy
    hit=((xx+.5)*STEP-p[:,0])**2+((yy+.5)*STEP-p[:,1])**2<=rad**2
    hit&=(xx>=0)&(xx<SIZE)&(yy>=0)&(yy<SIZE)
    curr[yy[hit],xx[hit]]=True

def finish_layer():
 global prev,curr
 flush_points()
 if not curr.any():return
 parent=[];supported=[];previous=[];roots={};allruns=[]
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(i,j):
  a,b=find(i),find(j)
  if a!=b:parent[b]=a;supported[a]|=supported[b]
 active=np.flatnonzero(curr.any(axis=1))
 for yy in range(int(active[0]),int(active[-1])+1):
  row=curr[yy]
  if not row.any():previous=[];continue
  d=np.diff(np.r_[False,row,False].astype(np.int8));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1)-1
  runs=[];k=0
  for a,b in zip(starts,ends):
   idx=len(parent);parent.append(idx);supported.append(bool(prev[yy,a:b+1].any()));runs.append((a,b,idx))
   while k<len(previous) and previous[k][1]<a-1:k+=1
   j=k
   while j<len(previous) and previous[j][0]<=b+1:
    union(idx,previous[j][2]);j+=1
  allruns.extend((yy,a,b,idx) for a,b,idx in runs)
  previous=runs
 rootset={find(i) for i in range(len(parent))}
 missing=sum(not supported[r] for r in rootset) if layer>1 else 0
 if missing:
  boxes={}
  for yy,a,b,idx in allruns:
   r=find(idx)
   if supported[r]:continue
   box=boxes.setdefault(r,[a,yy,b,yy]);box[0]=min(box[0],a);box[1]=min(box[1],yy);box[2]=max(box[2],b);box[3]=max(box[3],yy)
  islands.append({'layer':layer,'z_mm':round(layer*.2,3),'components_without_previous_layer_overlap':missing,'xy_bounds_mm':[[round(v*STEP,3) for v in box] for box in boxes.values()]})
 layerstats.append({'layer':layer,'components':len(rootset),'unsupported_components':missing})
 prev=curr;curr=np.zeros((SIZE,SIZE),bool)

def unsupported_span(xx,yy,width,length):
 pts=np.column_stack([xx,yy]);ix=np.floor(xx/STEP).astype(int);iy=np.floor(yy/STEP).astype(int)
 hit=np.zeros(len(pts),bool);radius=width/2+STEP*.7072;rr=int(math.ceil(radius/STEP))+1
 for dx in range(-rr,rr+1):
  for dy in range(-rr,rr+1):
   qx=ix+dx;qy=iy+dy
   ok=((qx+.5)*STEP-xx)**2+((qy+.5)*STEP-yy)**2<=radius**2
   ok&=(qx>=0)&(qx<SIZE)&(qy>=0)&(qy<SIZE)
   good=np.flatnonzero(ok);hit[good]|=prev[qy[good],qx[good]]
 absent=~hit;d=np.diff(np.r_[False,absent,False].astype(int));start=np.flatnonzero(d==1);end=np.flatnonzero(d==-1)
 return float(min(length,max(end-start,default=0)*length/max(1,len(pts)-1)))

for raw in source.open():
 if raw.startswith('; layer num/total_layer_count:'):
  finish_layer();layer=int(raw.split(':',1)[1].split('/')[0]);
  if cli_args.max_layer and layer>cli_args.max_layer:break
  if layer%100==0:print('Screening layer %d'%layer,flush=True)
  continue
 if raw.startswith('; FEATURE:'):
  feature=raw.split(':',1)[1].strip()
  if feature in ('Bridge','Internal Bridge','Floating vertical shell'):
   section={'feature':('Bridge' if feature=='Internal Bridge' else feature),'source_feature':feature,'layer':layer,'z_mm':round(layer*.2,3),'length_mm':0.,'paths':[]};sections.append(section)
  else:section=None
  continue
 if raw.startswith('; LINE_WIDTH:'):width=float(raw.split(':',1)[1]);continue
 line=raw.split(';',1)[0].strip()
 if not line:continue
 if line.startswith('M83'):relative=True
 if line.startswith('M82'):relative=False
 op=line.split(' ',1)[0]
 if op not in ('G0','G1','G2','G3'):continue
 args={k:float(v) for k,v in rx.findall(line)}
 nx=args.get('X',x);ny=args.get('Y',y);nz=args.get('Z',z)
 extrusion=args.get('E',0.)>0 and ('X'in args or 'Y'in args) and feature!='Custom' and layer>0
 if extrusion:
  if op in ('G2','G3') and ('I'in args or 'J'in args):
   cx=x+args.get('I',0.);cy=y+args.get('J',0.);r=math.hypot(x-cx,y-cy)
   aa=math.atan2(y-cy,x-cx);bb=math.atan2(ny-cy,nx-cx)
   delta=(bb-aa)%(2*math.pi) if op=='G3' else -((aa-bb)%(2*math.pi))
   length=abs(delta)*r;num=max(2,int(math.ceil(length/.12))+1)
   angle=np.linspace(aa,aa+delta,num);xx=cx+r*np.cos(angle);yy=cy+r*np.sin(angle)
  else:
   length=math.hypot(nx-x,ny-y);num=max(2,int(math.ceil(length/.12))+1)
   xx=np.linspace(x,nx,num);yy=np.linspace(y,ny,num)
  samples.extend(zip(xx,yy,np.full(num,width)))
  if section is not None:
   section['length_mm']+=length
   section['paths'].append({'start':[x,y],'end':[nx,ny],'length_mm':length,'width_mm':width,'unsupported_span_estimate_mm':unsupported_span(xx,yy,width,length) if section['feature']=='Bridge' else None})
  if len(samples)>20000:flush_points()
 x,y,z=nx,ny,nz
finish_layer()
summary={'layers_screened':len(layerstats),'raster_mm':STEP,'supports_enabled':False,
 'island_screen':'8-connected extrusion-footprint components must overlap previous layer; conservative raster dilation',
 'candidate_unsupported_islands':islands,'bridge_sections':[s for s in sections if s['feature']=='Bridge'],
 'floating_vertical_shell_sections':len([s for s in sections if s['feature']=='Floating vertical shell']),
 'floating_shell_layer_range':([min(s['layer'] for s in sections if s['feature']=='Floating vertical shell'),max(s['layer'] for s in sections if s['feature']=='Floating vertical shell')] if any(s['feature']=='Floating vertical shell' for s in sections) else None),
 'limitations':['Raster dilation can hide sub-0.2 mm gaps.','This analyzes emitted toolpaths, not material cooling, adhesion or mechanical strength.','Bridge section length is extrusion path length, not necessarily unsupported span.']}
(cli_args.output or source.with_name(source.stem+'-toolpath-analysis.json')).write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='bridge_sections'},indent=2),flush=True)
print('Bridge extrusion lengths:',[round(s['length_mm'],3) for s in summary['bridge_sections']],flush=True)
