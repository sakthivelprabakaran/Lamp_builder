"""Exact solid insertion sweep. Run inside a FreeCAD-capable Python runtime."""
import argparse,json,pathlib,hashlib,math,sys,os
parser=argparse.ArgumentParser(description='Check STEP insertion. Contract keys: fixed_step, moving_step, axis:[x,y,z], start_mm, end_mm, step_mm; optional allowed_contact_steps:[], minimum_clearance_mm, volume_tolerance_mm3. STEP placements are the zero-motion pose. Output report path is required.')
parser.add_argument('contract');parser.add_argument('report');args=parser.parse_args()
# FreeCAD's embedded import may reset __main__; preserve arguments explicitly.
import builtins
builtins._cad_gate_args=(args.contract,args.report)
if os.environ.get("FREECAD_LIB"):sys.path.insert(0,os.environ["FREECAD_LIB"])
import FreeCAD,Part
import argparse,json,pathlib,hashlib,math,sys,builtins
contract_path,report_path=builtins._cad_gate_args;cpath=pathlib.Path(contract_path).resolve();c=json.loads(cpath.read_text());base=cpath.parent
V=FreeCAD.Vector
sources={}
def load(path):
 p=(base/path).resolve();s=Part.read(str(p));assert s.isValid() and len(s.Solids)>0,'Invalid/non-solid STEP: '+str(p);sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return s
fixed=load(c['fixed_step']);moving=load(c['moving_step']);rigid=fixed
for path in c.get('allowed_contact_steps',[]):rigid=rigid.cut(load(path))
a=c['axis'];length=math.sqrt(sum(x*x for x in a));assert length>0;axis=V(*(x/length for x in a));start=float(c['start_mm']);end=float(c['end_mm']);step=float(c['step_mm']);assert step>0
n=max(1,math.ceil(abs(end-start)/step));assert n<=10000,'Sweep exceeds 10,001 poses; revise explicit sampling plan';poses=[start+(end-start)*i/n for i in range(n+1)];tol=float(c.get('volume_tolerance_mm3',1e-6));clearance=float(c.get('minimum_clearance_mm',0));assert tol>=0 and clearance>=0
rows=[]
for t in poses:
 s=moving.copy();s.translate(axis*t);volume=rigid.common(s).Volume;total=fixed.common(s).Volume;distance=rigid.distToShape(s)[0];rows.append(dict(translation_mm=t,forbidden_overlap_mm3=volume,total_undeformed_overlap_mm3=total,rigid_distance_mm=distance,passed=volume<=tol and distance+1e-7>=clearance))
report=dict(passed=all(x['passed'] for x in rows),method='exact B-rep boolean and distance at sampled translation poses',continuous_path_proven=False,physical_smoothness_proven=False,source_sha256=sources,contract=c,samples=rows)
pathlib.Path(report_path).write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'poses':len(rows),'max_forbidden_overlap_mm3':max(x['forbidden_overlap_mm3'] for x in rows)}));sys.exit(0 if report['passed'] else 2)
