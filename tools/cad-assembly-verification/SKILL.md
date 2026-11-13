---
name: cad-assembly-verification
description: Verify mechanical CAD mating interfaces, interference, clearances, insertion/removal paths, and section views before delivering assemblies or fit-dependent parts. Use for sleeves, rails, dovetails, snap features, press fits, and moving CAD assemblies; ordinary standalone decorative meshes need their mesh/print checks instead.
---
# CAD assembly verification

For every new or changed mating interface, run geometry checks before delivering its STL, STEP, assembly, or final render. Preserve previous versions and tie evidence to the delivered geometry revision.

- Use exact solids in an installed CAD kernel when available. Validate solid count, topology, and exported mesh watertightness separately.
- Define fixed and moving parts, coordinates, insertion direction, start/end poses, and the edge/datum customers align. Verify assembly order and tool access.
- Classify each contact: forbidden rigid interference, intentional contact, or flexible contact. For a flexible feature, allow only its free-span region. Its bonded root and surrounding body remain forbidden. Do not allowlist an entire part to hide a collision.
- Sweep insertion and removal with explicit sampling intervals, endpoints, and extra samples at first contact or geometry transitions. Check nominal sizes and declared manufacturing limits, offsets, and angular misalignment where relevant. Report sampled coverage; discrete poses do not prove continuous collision freedom.
- For friction fits, check permitted lateral/rotational freedom for a pose that removes all intended contact. Confirm that the intended contact cannot be escaped inside the available clearance; this still does not prove adequate grip force.
- Record intersection volumes and minimum distances. Fail forbidden overlaps above a declared numerical tolerance or required clearance violations. Fix failures and rerun; preserve the failing evidence.
- Show section/cutaway views with the actual mating geometry at approach, contact, and seated positions. Distinguish intended undeformed overlap from simulated deformation. Do not animate a rigid tongue through wood and call it a solved fit.
- Before final delivery, include a compact report stating geometry revision/hashes, tested dimensions/poses, pass/fail criteria, results, and unresolved checks. If checks are unavailable, label an explicitly requested draft as unverified rather than claiming a pass.

`scripts/check_insertion.py` runs exact STEP-based translation sweeps. Read its `--help`; supply a JSON contract with paths to fixed/moving solids, a motion axis/range/step, and optional STEP volumes defining ONLY permitted flexible contact. Use a CAD Python runtime providing FreeCAD and Part. It exits nonzero for forbidden overlap or failed clearance. Re-run on each delivered variant or document a justified equivalent interface family with its worst-case members tested.

Geometric clearance is not proof of smooth insertion, holding force, fatigue, creep, or thermal performance. Those need appropriate material/contact analysis or physical evidence. Report which was actually performed; never invent load/material parameters.

For Lamp Builder, keep female wedge and screw-clamp designs archived while evaluating one-piece sleeves. Mark positions reference the bare post bottom and the sleeve bottom edge, not the rail centre. Update model-specific assembly instructions when insertion direction/order changes.

Reference capabilities: [FreeCAD Part scripting](https://github.com/FreeCAD/FreeCAD-documentation-docusaurus/blob/Stable/docs/python-scripting/part-scripting.md). Related repository identified by the user-requested search: [FreeCAD assembly engineering](https://github.com/vindu939/freecad-skills/blob/main/freecad-production-suite-marketplace/plugins/freecad-production-suite/skills/freecad-assembly-engineering/SKILL.md). This skill uses installed tools and does not install or execute that repository.
