"""Attach an individual completed Bambu slice to its exact catalog product.
Usage: python3 tools/record_product_slice.py product-id path/to/sliced.3mf
Does not record a physical test or transfer evidence to custom variations.
"""
import sys,json,hashlib,zipfile,pathlib,xml.etree.ElementTree as ET
from build_customer_catalog import ROOT
import lamp_engine as engine
import tempfile
ident=sys.argv[1];path=pathlib.Path(sys.argv[2]).resolve();record=ROOT/'assets/customer/catalog'/(ident+'.json')
d=json.loads(record.read_text())
source=path.parent/(ident+'.stl')
v,f=engine.build_shade_mesh(d['params'])
raw_hash=hashlib.sha256(v.tobytes()+f.tobytes()).hexdigest()
if raw_hash!=d['evidence']['mesh_sha256']:raise ValueError('Saved parameters differ from screened mesh')
v[:,:2]+=128
with tempfile.TemporaryDirectory(prefix='lume-slice-check-') as folder:
 expected=pathlib.Path(folder)/'expected.stl';engine.write_binary_stl(str(expected),v,f)
 if hashlib.sha256(expected.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():raise ValueError('Sliced STL input differs from the saved product settings')
with zipfile.ZipFile(path) as z:
 plate=ET.fromstring(z.read('Metadata/slice_info.config')).find('plate')
 metadata={x.get('key'):x.get('value') for x in plate.findall('metadata')}
 obj=plate.find('object')
 if obj.get('name')!=ident+'.stl' or obj.get('skipped')=='true':raise ValueError('Slice object does not match this product')
 if metadata['support_used']!='false' or metadata['outside']!='false':raise ValueError('Slice does not satisfy support/bed requirements')
 layers=plate.find('layer_filament_lists/layer_filament_list').get('layer_ranges')
 png=next((n for n in z.namelist() if n.endswith('.png') and 'top' not in n),None)
 if png:(path.parent/'bambu-preview.png').write_bytes(z.read(png))
 evidence=dict(product_id=ident,mesh_sha256=d['evidence']['mesh_sha256'],slice_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),file=str(path),supports_used=False,inside_build_volume=True,layer_range=layers,predicted_seconds=int(metadata['prediction']),estimated_grams=float(metadata['weight']),profile='Bambu A1 / 0.4 mm / 0.20 mm / Generic PLA provisional',physical_tested=False,full_toolpath_island_analysis=False)
 (path.parent/'slice-evidence.json').write_text(json.dumps(evidence,indent=2))
 d['evidence']['slicer_verified']=True;d['evidence']['individual_slice']=evidence
 record.write_text(json.dumps(d));print(json.dumps(evidence,indent=2))
