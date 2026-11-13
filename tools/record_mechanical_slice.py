"""Record exact mechanical-part Bambu review evidence; not physical validation."""
import argparse, hashlib, json, pathlib, zipfile, xml.etree.ElementTree as ET
p=argparse.ArgumentParser(); p.add_argument('stl',type=pathlib.Path); p.add_argument('slice',type=pathlib.Path); p.add_argument('analysis',type=pathlib.Path); p.add_argument('--orientation',required=True); a=p.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
with zipfile.ZipFile(a.slice) as z:
 config=ET.fromstring(z.read('Metadata/slice_info.config'));plate=config.find('plate')
 header={x.get('key'):x.get('value') for x in config.find('header').findall('header_item')}
 metadata={x.get('key'):x.get('value') for x in plate.findall('metadata')}
 obj=plate.find('object')
 if obj.get('name')!=a.stl.name or obj.get('skipped')=='true': raise ValueError('Wrong object')
 analysis=json.loads(a.analysis.read_text())
 bridges=analysis['bridge_sections']
 evidence={'stl':str(a.stl.resolve()),'stl_sha256':sha(a.stl),'slice':str(a.slice.resolve()),'slice_sha256':sha(a.slice),'analysis_sha256':sha(a.analysis),'orientation':a.orientation,'slicer':('OrcaSlicer' if 'OrcaSlicer-Version' in header else 'Bambu Studio'),'slicer_version':header.get('OrcaSlicer-Version',header.get('X-BBL-Client-Version')),'slicer_warnings':[dict(q.attrib) for q in plate.findall('warning')],'printer':'Bambu Lab A1 0.4 mm nozzle','layer_height_mm':0.2,'material':'Generic PETG, provisional','walls':3,'supports_enabled':False,'inside_build_volume':metadata['outside']=='false','supports_used':metadata['support_used']=='true','prediction_seconds':int(metadata['prediction']),'weight_g':float(metadata['weight']),'layers_screened':analysis['layers_screened'],'candidate_unsupported_islands':analysis['candidate_unsupported_islands'],'floating_shell_sections':analysis['floating_vertical_shell_sections'],'bridge_sections':[{'layer':s['layer'],'z_mm':s['z_mm'],'path_count':len(s['paths']),'max_unsupported_span_estimate_mm':max((q['unsupported_span_estimate_mm'] for q in s['paths']),default=0)} for s in bridges],'physical_strength_verified':False,'snap_force_verified':False,'limitations':analysis['limitations']+['Provisional Generic PETG profile; review against purchased filament.','Raster connectedness is not proof that an overhanging path or bridge prints reliably.']}
 settings=a.slice.parent/'slice-inputs'; evidence['settings_sha256']={q.name:sha(q) for q in settings.glob('*.json')}
 out=a.slice.parent/'slice-evidence.json';out.write_text(json.dumps(evidence,indent=2)+'\n');print(out)
