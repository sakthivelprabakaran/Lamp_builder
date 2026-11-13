"""Stage actual existing Pearl lamp meshes plus current retained tray v3."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'assets/customer/assembly-v3';d=json.loads((R/'tmp/pdfs/manual-assets/geometry.json').read_text());v3=json.loads((R/'output/revamp/retained-tray-v3/render-geometry.json').read_text());meshes=d['meshes'];meshes.update(v3['meshes'])
for name,path in [('female-one-piece','output/revamp/one-piece-female/female.npz'),('mid-panel-guide','output/revamp/shade-support-v1/mid-panel-guide.npz'),('top-panel-grip-cap','output/revamp/shade-support-v1/top-panel-grip-cap.npz')]:
 a=np.load(R/path);meshes[name]={'v':a['v'].tolist(),'f':a['f'].tolist()}
items=[]
for old in d['scenes']['hero']['objects']:
 o=dict(old);n=o.get('mesh','');z=o['xyz'][2]
 if n in ['post-wedge','post-pad','corner-bottom','corner-through','top-retaining-cap','light-tray']:continue
 if n=='female':o['mesh']='female-one-piece';n='female-one-piece'
 stage=0
 if n in ['female-one-piece','male'] or ('box'in o and o['box'][2]<=25):stage=1 if z<100 else 2
 if n.startswith('panel-'):stage=5 if n=='panel-0' else 7
 o['stage']=stage;items.append(o)
for old in d['scenes']['shade-supported-assembly']['objects']:
 if old.get('mesh') not in ['mid-panel-guide','top-panel-grip-cap']:continue
 o=dict(old);o['stage']=6 if o['mesh']=='mid-panel-guide' else 8;items.append(o)
for old in v3['scenes']['assembly-overview']['objects']:
 if old.get('mesh') not in ['snap-reinforced-holder','flat-tray']:continue
 o=dict(old);o['stage']=3 if o['mesh']=='snap-reinforced-holder' else 4;items.append(o)
scenes={'full-lamp':{'objects':items},'corner-seated':v3['scenes']['corner-seated']};names={o['mesh'] for s in scenes.values() for o in s['objects'] if 'mesh'in o};out={'revision':v3.get('revision','retained-tray-v3-holder-integral-tongues'),'integration_status':'Existing Pearl frame and shade prototypes composed with revised tray v3. Full assembly paths and structural integration are not newly CAD-verified.','scenes':scenes,'meshes':{n:meshes[n] for n in names},'steps':['Posts and feet','Lower rail frame','Upper rail frame','Reinforced shade holders','Snap-in tray','Lower shade panels','Middle panel guides','Upper shade panels','Top retaining caps']};(O/'geometry.json').write_text(json.dumps(out,separators=(',',':')));print('Full lamp staged:',len(items),'instances;',len(names),'actual mesh types')
