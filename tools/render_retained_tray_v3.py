"""Render verified retained-tray-v3 meshes. Geometry JSON is supplied by CAD export.
No geometry is inferred or generated here; arrows/captions remain outside part shapes.
"""
import sys,pathlib,json
import bpy
ROOT=pathlib.Path(__file__).resolve().parents[1]
argv=sys.argv[sys.argv.index('--')+1:]
if len(argv)!=2:raise SystemExit('Usage: blender -b --python tools/render_retained_tray_v3.py -- geometry.json output-directory')
geometry_path,outdir=map(pathlib.Path,argv)
source=(ROOT/'tools/render_manual_blender.py').read_text()
sys.argv=[sys.argv[0],'--','--eevee']
# Reuse tested brand materials, exact mesh loader, camera fitting and studio lights.
source=source[:source.index("for name,spec in data['scenes'].items():")]
source=source.replace("width=1000 if a.quick else 1800","width=1000 if a.quick else 2600")
exec(compile(source,'LUME-render-library','exec'))
OUT=outdir;OUT.mkdir(parents=True,exist_ok=True)
data=json.loads(geometry_path.read_text());meshdata=data['meshes']
for name,spec in data['scenes'].items():
 render(name,spec)
print('Completed actual-geometry v3 studio renders',flush=True)
