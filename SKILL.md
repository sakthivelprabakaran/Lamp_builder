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
