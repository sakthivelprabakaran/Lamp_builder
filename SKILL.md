# Lamp Studio — How we build here

## Run it
- One-click: **`Start Lamp Studio.cmd`** (windowless, auto-opens the browser).
- Manual: `python server.py` → http://127.0.0.1:8776
- Stop: Ctrl+C in the console, or `pkill -f server.py` (also kills the base worker).
- Port **8776** (8771–8775 are taken by KindleSSH/notebook/GPC/unlock/b3d2scad).

## Architecture (mirror of the b3d2scad Studio pattern)
- `lamp_engine.py` — geometry core. **No web/IO concerns.**
  - `build_shade_mesh(params) -> (verts, faces)` — pure numpy, ~30 ms.
  - `write_binary_stl`, `verify_mesh` (watertight gate), `min_wall_ok`.
  - `build_base(params, shade_params) -> build123d Solid` (imports build123d lazily).
- `server.py` — stdlib HTTP, loopback-only, Origin/Host checked. Generates the
  **shade in-process** (numpy is cheap) and the **base via a persistent worker**.
- `worker.py` — long-lived `--serve` subprocess; warms build123d **once** (~15 s),
  then each base build is ~0.7 s. Used for the base only.
- `index.html` — three.js viewer + grouped sliders + presets. Debounced live preview.
- `presets/*.json` — saved `{shade, base}` parameter sets (gitignored? no — tracked).
- `output/` — generated STL/STEP (gitignored).

## The operator model (how "infinite patterns" works)
A shade is one radius field `r(theta, z)` composed from independent operators in
`_radius_field()`: profile `R(z)` (form) × `(1 + lobe_amp·sin(lobes·θ + twist·z))`
× ripple × value-noise. **Add a new pattern = add a term here**, expose its params
in `SHADE_DEFAULTS`, and add a slider row in `index.html`'s `SHADE_CTRL`. That's it.

## The gate (never skip)
- Every **export** runs `verify_mesh` → must report `watertight: True`,
  `boundary_edges: 0`, `nonmanifold_edges: 0`. The UI surfaces a warning if not.
- `min_wall_ok` warns below 0.8 mm.
- After any engine change, run the smoke test: `python lamp_engine.py --base`
  (must print `watertight=True` and build the base without error).

## Conventions
- Units: **millimetres** everywhere.
- Keep `lamp_engine.py` importable without build123d (numpy only at module top).
- Preview caps resolution (≤160×120); export uses the full `res_theta`/`res_z`.
- Mesh winding: outer normals out, inner normals in, caps join them — keep it
  watertight when editing `build_shade_mesh`.

## Never touch / guardrails
- Don't move the server off `127.0.0.1` — it executes geometry locally.
- Don't add pip dependencies without the owner's OK (supply-chain policy).
  Phase 3 (`sdf`/`manifold3d`) must be approved first.
- Don't cap coverage silently — if a build is truncated or fails a gate, say so.

## Mechanical assembly verification gate
### Design for FDM printing — all lamp parts
User requirement: design every part around its manufacturing orientation before finalizing the mechanism. Use the Bambu Lab A1 and the actual nozzle/material profile as the printing target. Record bed contact, build-envelope margin, layer direction relative to loads and flexure, feature/toolpath thickness, overhangs, bridges, layer islands, and accessible support removal. Avoid supports on mating faces and flexible arms where removal can damage their function. Prefer simple flat-printing geometry; separately printed captive parts may be pre-fitted so customers do not handle loose locks.

Before delivering a revision as print-ready, slice every changed part in its declared orientation and inspect toolpaths, unsupported starts, bridge spans, thin features, and support access. Tie this evidence to the delivered revision and settings. Geometry screening alone is not slicer verification; slicer verification does not establish physical strength, snap force, fatigue, creep, or heat resistance. Record unresolved checks explicitly. Preserve existing prototypes, but do not describe the retained-tray-v2 integral hanging-hook design as print-ready: its printing setup is unresolved.

User requirement: before delivering any new or changed model with mating parts, run [CAD assembly verification](tools/cad-assembly-verification/SKILL.md). Include collision, clearance, insertion/removal direction and path, assembly sequence, and section-view evidence. Classify flexible contact separately from rigid interference; tongue roots must never be exempted. Record geometry revision, tested tolerances and poses, pass/fail results, and unresolved physical checks. Failed checks require correction and rerun before verified delivery. A mesh check alone is insufficient. Test every changed interface/variant or an explicitly justified equivalent interface family; standalone shades retain their mesh/print gate.

## Customer assembly preview
The local customer page links to `/assembly`, the nine-step complete Pearl lamp illustration. Regenerate its actual-mesh asset with `tools/compose_full_lamp_assembly.py` after relevant CAD changes. Keep module verification separate from full illustrative motion. Current revised tray download pack is under output/revamp/retained-tray-v3; the chosen purchased bulb-holder interface remains pending. Browser QA must identify the actual browser used; an in-app preview does not constitute Chrome testing.

## Storefront and owner workspace
Customer routes `/` and `/customer` provide browsing, customization, local order requests and `/assembly` instructions only. Never add manufacturing downloads to customer UI. `/studio` and `/frame-studio` hold design tools; `/studio/orders` holds production files and local order workflow. Local prototype orders use `lume.orders.v1`; transfers use `lume.studio.import.v1`. There is no remote delivery, payment, authentication or backend access control yet; UI separation must not be represented as file-access security. Latest compatible standing preview uses actual revision-specific meshes; archived parametric exports must be labeled clearly.
