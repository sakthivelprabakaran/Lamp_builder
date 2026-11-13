"""Compose actual exported v3 CAD geometry for clear studio views."""
from pathlib import Path
import json,math,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'output/revamp/retained-tray-v3'
d=json.loads((R/'tmp/pdfs/manual-assets/geometry.json').read_text())
for name in ['flat-tray','snap-reinforced-holder','tray-corner-crop']:
 p=O/(name+'.npz')
 if p.exists():
  a=np.load(p);d['meshes'][name]={'v':a['v'].tolist(),'f':a['f'].tolist()}
objects=[]
for item in d['scenes']['tray-four-post-support-v2']['objects']:
 item=dict(item)
 if item.get('mesh')=='B22-M10-adapter':continue
 if item.get('mesh')=='reinforced-bottom-holder':item['mesh']='snap-reinforced-holder'
 if item.get('mesh')=='tray-integral-latches':item['mesh']='flat-tray'
 objects.append(item)
scenes={'assembly-overview':{'objects':objects,'view':[.9,-1,1.4],'size':[2600,2200]}}
if 'tray-corner-crop' in d['meshes']:
 holder={'mesh':'snap-reinforced-holder','xyz':[-97.5,-97.5,-52.8],'material':'sage'}
 for name,dz in [('corner-exploded',18),('corner-seated',0)]:
  scenes[name]={'objects':[holder,{'mesh':'tray-corner-crop','xyz':[0,0,dz],'material':'shade'},{'box':[25,25,95],'xyz':[-97.5,-97.5,-14],'material':'wood'}],'view':[1,-1,.65],'size':[2600,2300]}
d['scenes']=scenes
(O/'render-geometry.json').write_text(json.dumps(d))
print('Composed:',', '.join(scenes))
