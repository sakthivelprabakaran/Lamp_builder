"""Build real mesh thumbnails and geometric evidence for the customer collection.
Offline authoring uses the existing NumPy engine and installed Pillow; no runtime dependency.
"""
import sys,pathlib,json,hashlib,copy,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
import lamp_engine as engine,print_geometry as pg
SHAPES=[('Aster',44,40,40,.55),('Column',62,62,0,.5),('Cone',78,36,0,.5),('Flare',38,78,0,.5),('Urn',52,38,32,.65),('Pear',42,28,30,.42),('Hourglass',68,60,-25,.5),('Barrel',58,54,25,.5),('Bell',40,70,20,.7),('Obelisk',50,26,12,.4),('Lantern',54,52,36,.52),('Tulip',38,60,25,.7)]
STRUCTURES=[
 ('Flow','Woven',dict(pattern='weave',pat_cols=24,pat_rows=8,weave_width=2.4)),
 ('Filigree','Woven',dict(pattern='weave',pat_cols=32,pat_rows=10,weave_width=2.0)),
 ('Canopy','Woven',dict(pattern='weave',pat_cols=16,pat_rows=6,weave_width=3.2)),
 ('Grove','Organic',dict(pattern='voronoi',pat_cols=18,pat_rows=5,web=.30)),
 ('Tide','Lattice',dict(pattern='gyroid',pat_cols=20,pat_rows=7,web=.33)),
 ('Reed','Solid',dict(pattern='none',lobes=36,lobe_amp=.04,twist_turns=.08)),
 ('Swell','Solid',dict(pattern='none',lobes=5,lobe_amp=.12,twist_turns=.12)),
 ('Pleat','Solid',dict(pattern='none',lobes=24,lobe_amp=.06,twist_turns=0)),
 ('Spiral','Solid',dict(pattern='none',lobes=12,lobe_amp=.09,twist_turns=.4)),
 ('Ripple','Solid',dict(pattern='none',lobes=0,lobe_amp=0,ripple_waves=5,ripple_amp=.035))]
def designs():
 result=[]
 for si,(shape,r0,r1,b,bp) in enumerate(SHAPES):
  for ti,(texture,group,recipe) in enumerate(STRUCTURES):
   p=dict(height=230,r_bottom=r0,r_top=r1,bulge=b,bulge_pos=bp,wall=1.6,support_free=1,res_theta=160,res_z=160,lobes=0,lobe_amp=0,twist_turns=0,ripple_waves=0,ripple_amp=0,noise_amp=0,top_solid=12,pat_seed=7+si*11,seed=1+si)
   p.update(recipe)
   if si==0 and ti==0:p['wall']=1.6 # same approved flowing geometry
   name=shape+' '+texture;ident=shape.lower()+'-'+texture.lower()
   result.append(dict(id=ident,name=name,shape=shape,structure=texture,group=group,description=f'{shape} silhouette with '+{'Woven':'crossing flowing ribs.','Organic':'graded organic openings.','Lattice':'a pointed lattice of light.','Solid':'a continuous sculptural wall.'}[group],params=p,thumbnail='/assets/customer/catalog/'+ident+'.png'))
 return result
def customized(p,height,density):
 p=copy.deepcopy(p);p['height']=height
 if p['pattern']=='none':
  factor={'airy':.75,'balanced':1,'intimate':1.25}[density]
  p['lobe_amp']*=factor;p['ripple_amp']*=factor
 elif p['pattern']=='micro_round':p['pat_hole_mm']*= {'airy':1.15,'balanced':1,'intimate':.75}[density]
 elif p['pattern']=='weave':p['weave_width']*= {'airy':.85,'balanced':1,'intimate':1.25}[density]
 else:p['web']+= {'airy':-.06,'balanced':0,'intimate':.08}[density]
 return p
def thumbnail(v,f,path):
 # Orthographic mesh projection, depth sorted and lit using actual triangle normals.
 tri=v[f].astype(float);view=np.array([.45,-.85,.27]);view/=np.linalg.norm(view);right=np.cross(view,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,view)
 normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
 visible=normals@view>0;tri=tri[visible];normals=normals[visible]
 proj=np.stack([tri@right,tri@up],axis=-1);flat=proj.reshape(-1,2);lo=flat.min(0);hi=flat.max(0);scale=min(198/(hi[0]-lo[0]),252/(hi[1]-lo[1]));proj=(proj-(lo+hi)/2)*scale;proj[:,:,0]+=130;proj[:,:,1]=153-proj[:,:,1]
 depth=tri.mean(1)@view;light=np.array([-.3,-.7,.7]);light/=np.linalg.norm(light);illum=np.clip(normals@light,0,1);shade=(.62+.35*illum)[:,None]*np.array([239,233,220])
 im=Image.new('RGB',(260,306),(242,241,233));draw=ImageDraw.Draw(im)
 draw.ellipse((60,280,224,295),fill=(224,224,212))
 for i in np.argsort(depth):draw.polygon([tuple(a) for a in proj[i]],fill=tuple(shade[i].astype(int)))
 im.save(path,optimize=True)
def check(d):
 p=d['params'];v,f=engine.build_shade_mesh(p);ok,metrics=engine.verify_mesh(v,f);report=pg.manufacturing_report(v,f)
 if not ok or not report['passed']:raise ValueError((d['id'],metrics,report))
 digest=hashlib.sha256(v.tobytes()+f.tobytes()).hexdigest()
 thumbnail(v,f,ROOT/'assets/customer/catalog'/f"{d['id']}.png")
 features=pg.measure_features(v,f,18.)
 if features['minimum_normal_wall_estimate_mm']<.8 or (features['aperture_count'] and features['minimum_aperture_clearance_mm']<1.6):raise ValueError((d['id'],features))
 checks=[]
 for h,den in [(180,'airy'),(180,'intimate'),(230,'airy'),(230,'intimate')]:
  cv,cf=engine.build_shade_mesh(customized(p,h,den));r=pg.manufacturing_report(cv,cf)
  if not r['passed']:raise ValueError((d['id'],h,den,r))
  checks.append(dict(height=h,density=den,passed=True))
 d['evidence']=dict(mesh_sha256=digest,triangles=len(f),apertures=features['aperture_count'],size_mm=report['size_mm'],minimum_wall_estimate_mm=features['minimum_normal_wall_estimate_mm'],minimum_web_clearance_mm=features['minimum_aperture_clearance_mm'],geometry_passed=True,range_checks=checks,slicer_verified=False)
 (ROOT/'assets/customer/catalog'/f"{d['id']}.json").write_text(json.dumps(d))
 return d
if __name__=='__main__':
 ds=designs();out=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(check,d):d['id'] for d in ds}
  for future in concurrent.futures.as_completed(futures):
   out.append(future.result());print(f'{len(out)}/120 {futures[future]}',flush=True)
 out.sort(key=lambda d:next(i for i,x in enumerate(ds) if x['id']==d['id']))
 hashes={d['evidence']['mesh_sha256'] for d in out};assert len(hashes)==120
 result=dict(count=len(out),unique_meshes=len(hashes),size_range_mm=[180,230],geometry_screen='upright A1 / 0.4 mm nozzle; mesh integrity, facet overhang, feature estimates; no physical validation',designs=out)
 (ROOT/'assets/customer/catalog.json').write_text(json.dumps(result,separators=(',',':')))
 (ROOT/'output/revamp/customer-catalog-evidence.json').write_text(json.dumps(result,indent=2))
 print('Finished: 120 unique meshes; 480 range screens',flush=True)
