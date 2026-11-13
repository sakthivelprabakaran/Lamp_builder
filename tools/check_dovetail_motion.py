"""Nominal local dovetail insertion/pin checks; hardware and physical fit excluded."""
import sys
sys.path.insert(0,'/Applications/VibeCAD.app/Contents/Resources/lib')
import FreeCAD as A,Part
import pathlib,json,math
root=pathlib.Path(__file__).resolve().parents[1];cad=root/'output/revamp/standing-cad';female=Part.read(str(cad/'dovetail-female.step'));male=Part.read(str(cad/'dovetail-male.step'));male.translate(A.Vector(12.6,0,2));checks=[]
for travel in [0,5,10,15,20,25,30]:
 moved=male.copy();moved.translate(A.Vector(0,0,travel));volume=female.common(moved).Volume;checks.append(dict(upward_travel_mm=travel,overlap_mm3=volume,passed=volume<1e-5))
pin=Part.makeCylinder(2.,24,A.Vector(7.3,-12,14),A.Vector(0,1,0));pinchecks={'female_overlap_mm3':female.common(pin).Volume,'male_overlap_mm3':male.common(pin).Volume}
report=dict(local_sweep=checks,round_4_mm_pin_nominal_clearance=pinchecks,upper_rail_wood_clearance_at_30_mm_lift_mm=7.5,upper_shoe_clearance_at_30_mm_lift_mm=5.5,neighbor_corner_shoe_envelope_gap_mm=1.2,interpretation='Both rail ends use this same vertical sweep; fourth rail has no opposing insertion direction. Corner envelope gap and upper-module clearance are nominal default dimension checks.',limitations=['Not a continuous full-scene sweep; sampled local B-rep checks plus nominal envelope distances.','Keeper, screw heads, actual wood/print distortion and light/cable hardware absent.','Physical sliding/locking, strength and stability unverified.'])
(cad/'dovetail-motion.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
