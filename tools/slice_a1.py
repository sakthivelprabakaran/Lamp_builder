"""Slice a reviewed STL using installed macOS Bambu Studio and temporary settings.

Uses bundled full A1 0.4 mm, 0.20 mm and provisional Generic PLA profiles.
Does not send a print job or change normal user preferences.
"""
import argparse
import json
import pathlib
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--filament',choices=['PLA','PETG'],default='PLA')
parser.add_argument('stl',type=pathlib.Path)
parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path('output/revamp'))
args=parser.parse_args()
app=pathlib.Path('/Applications/BambuStudio.app')
root=app/'Contents/Resources/profiles/BBL'
index={}
for path in root.rglob('*.json'):
    try:
        data=json.loads(path.read_text())
    except (ValueError,UnicodeError):
        continue
    index[data.get('name',path.stem)]=data
    index.setdefault(path.stem,data)

def resolve(name,seen=frozenset()):
    if name in seen:
        raise ValueError('Cyclic profile inheritance: '+name)
    data=index[name]; result={}; seen=seen|{name}
    if data.get('inherits'):
        result.update(resolve(data['inherits'],seen))
    for include in data.get('include',[]):
        result.update(resolve(include,seen))
    result.update(data)
    result.pop('inherits',None); result.pop('include',None)
    return result

output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
inputs=output/'slice-inputs';inputs.mkdir(exist_ok=True)
for label,name in [('machine','Bambu Lab A1 0.4 nozzle'),
                   ('process','0.20mm Standard @BBL A1'),
                   ('filament','Generic '+args.filament+' @BBL A1')]:
    data=resolve(name)
    if label=='process':
        data.update(enable_support='0',wall_loops='3')
    (inputs/(label+'.json')).write_text(json.dumps(data,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='lamp-bambu-') as datadir:
    command=[str(app/'Contents/MacOS/BambuStudio'),'--datadir',datadir,
             '--load-settings',str(inputs/'machine.json')+';'+str(inputs/'process.json'),
             '--load-filaments',str(inputs/'filament.json'),
             '--curr-bed-type','Textured PEI Plate','--orient','0','--arrange','1',
             '--slice','0','--debug','2','--outputdir',str(output),
             '--export-3mf',args.stl.stem+'-sliced.3mf',str(args.stl.resolve())]
    print('Slicing exported orientation, supports off; Generic '+args.filament+' is a provisional review profile.',flush=True)
    with (output/'bambu-cli.log').open('w') as log:
        result=subprocess.run(command,cwd=app/'Contents/MacOS',stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit('Bambu CLI failed (%s); inspect %s'%(result.returncode,output/'bambu-cli.log'))
    print(output/(args.stl.stem+'-sliced.3mf'))
