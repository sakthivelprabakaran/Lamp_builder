"""Sample expected Column Pearl hole centers against actual Bambu extrusion paths.
Checks three representative rows; not every aperture or physical hole tolerance.
"""
import math,re,json,pathlib,numpy as np,zipfile,xml.etree.ElementTree as ET
root=pathlib.Path(__file__).resolve().parents[1];source=root/'output/revamp/products/column-pearl/review.gcode'
lo=21.2 # collar 18 + reserved 3.2 mm band
hi=218.;pitch=(hi-lo)/32;radius=1.1
rows=[5,15,25];targets={int(round((lo+(r+.5)*pitch-radius*.5)/.2)):r for r in rows}
pts={k:[] for k in targets};x=y=z=0.;layer=0;width=.42;feature='Custom';rx=re.compile(r'([XYZEFIJK])([-+]?(?:\d*\.\d+|\d+))')
for raw in source.open():
 if raw.startswith('; layer num/total_layer_count:'):layer=int(raw.split(':')[1].split('/')[0]);continue
 if raw.startswith('; FEATURE:'):feature=raw.split(':')[1].strip();continue
 if raw.startswith('; LINE_WIDTH:'):width=float(raw.split(':')[1]);continue
 code=raw.split(';')[0].strip();op=code.split(' ')[0]
 if op not in ['G0','G1','G2','G3']:continue
 a={k:float(v) for k,v in rx.findall(code)};nx=a.get('X',x);ny=a.get('Y',y);nz=a.get('Z',z)
 if layer in targets and a.get('E',0)>0 and feature!='Custom' and ('X' in a or 'Y' in a):
  if op in ['G2','G3'] and ('I' in a or 'J' in a):
   cx=x+a.get('I',0);cy=y+a.get('J',0);rr=math.hypot(x-cx,y-cy);aa=math.atan2(y-cy,x-cx);bb=math.atan2(ny-cy,nx-cx);dd=(bb-aa)%(2*math.pi) if op=='G3' else -((aa-bb)%(2*math.pi));n=max(2,int(abs(dd)*rr/.12)+1);angle=np.linspace(aa,aa+dd,n);xx=cx+rr*np.cos(angle);yy=cy+rr*np.sin(angle)
  else:
   n=max(2,int(math.hypot(nx-x,ny-y)/.12)+1);xx=np.linspace(x,nx,n);yy=np.linspace(y,ny,n)
  pts[layer].extend(zip(xx,yy,np.full(n,width/2)))
 x,y,z=nx,ny,nz
with zipfile.ZipFile(source.with_name('column-pearl-sliced.3mf')) as archive:
 model=ET.fromstring(archive.read('3D/3dmodel.model'));item=model.find('{*}build/{*}item');transform=np.asarray([float(x) for x in item.get('transform').split()]);rotation=transform[:9].reshape(3,3)[:2,:2];translation=transform[9:11]
results=[]
for layer,row in targets.items():
 # Column's outer 62 / inner 60.4 mm, hence center of wall at 61.2 mm.
 angle=2*math.pi*(np.arange(80)+.5*(row%2))/80;centers=np.column_stack([128+61.2*np.cos(angle),128+61.2*np.sin(angle)]);centers=centers@rotation+translation;samples=np.asarray(pts[layer]);clear=np.full(80,np.inf)
 for j in range(0,len(samples),5000):
  p=samples[j:j+5000];d=np.linalg.norm(centers[:,None,:]-p[None,:,:2],axis=-1)-p[None,:,2];clear=np.minimum(clear,d.min(axis=1))
 results.append(dict(row=row,layer=layer,z_mm=layer*.2,sampled_apertures=80,open_centers=int((clear>.30).sum()),minimum_clear_radius_mm=float(clear.min())))
report=dict(product='column-pearl',rows=results,sampled_apertures=240,open_centers=sum(x['open_centers'] for x in results),method='Expected hole centers compared to sampled extrusion centerlines minus half line width, three rows only; >0.30 mm free radius',physical_tolerance_verified=False)
(root/'output/revamp/products/column-pearl/aperture-preservation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
