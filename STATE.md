# Lamp Studio — State log

## Resume point (2026-08-18, latest)
Phases 1–3 done+verified. **Phase 5 (operator-stack "◆ SHAPE" editor) is now
IMPLEMENTED across all layers and works** — see the Phase 5 section below.
**Next when you resume:** re-run the *fixed* UI verify (`python _verify_ui_p5.py`,
server up) to exercise reorder/▲▼ + mute (the last run crashed on a console-encoding
bug in the harness, now fixed — the app itself was clean). Then decide the UX call on
"added op starts as a no-op" (see note) and update the roadmap. Deferred: Phase 2
base polish (base too flat), Phase 4 batch/catalogue export.

(earlier) Phase 1 built + verified end-to-end: app runs, shade previews live,
exports watertight STL, base builds to STL+STEP.

## Done
- **Engine** (`lamp_engine.py`): composable operator field (form/flutes/twist/
  ripple/noise), numpy mesh shade, binary STL writer, vectorized watertight
  verify, build123d base adapter. Timings: shade build 32 ms, verify 43 ms,
  STL write 114 ms @ 200×180 (144k tris).
- **App**: stdlib loopback server (:8776), persistent build123d base worker,
  three.js live-preview UI with grouped sliders, presets, shade/base/both toggle,
  export STL, generate base (STL+STEP).
- **Verified**: `/api/shade`, `/api/export_shade` (watertight True),
  `/api/base` (STL+STEP, ~0.7 s after 15 s warm), preset save. Smoke test passes.
- Launcher `Start Lamp Studio.cmd`; `.gitignore`; scaffold (VISION/SKILL/STATE/README).

## In progress — Phase 2 (base + tool-free twist-lock)
Built & verified 2026-08-18. Shade↔base is a **3-lug bayonet**; base↔holder is a
**parametric holder mount** (m10 / b22 / e27 / ikea) with a **test-fit ring**.
- Bayonet is expressed as inner-wall radius features on the shade's bottom collar
  (entry channels centred on 0/120/240° + trapping pockets with a chamfered,
  support-free upper ledge). Shade stays watertight (177k tris, verified). No
  through-slot mesh surgery. See `_bayonet_inner` + `bayonet_geometry`.
- Base lugs built in build123d (`build_base`) at 0/120/240°, coupled to the shade
  via `_base_dims`(shade_params) so they mate. Holder mount in `_cut_holder_mount`:
  m10=hex nut pocket underside; b22=Ø recess + 2 screw holes; e27/ikea=Ø recess.
  `build_testfit_ring` = short disc with just the holder cavity.
- **Fit verified geometrically** (clearances): insertion channel r=67.7 ≥ lug
  tip 66.7 (CLEAR), pocket has ROOM, ledges trap the lug above & below (65.0 <
  66.7), twist-to-lock ≈ 28.5°. NOT yet physically printed — print the collar +
  base and tune `fit_clr` (default 0.5 mm) for the real slip fit.
- UI: Twist-lock + Holder slider groups, holder-type dropdown, "Test-fit ring"
  button, shade-rests-on-base offset in the Both view.
- **Holder dimensions are NOMINAL** (Indian holders vary by brand) — always print
  the test-fit ring against the real purchased holder before a full base.

### Bugs found while user-testing (all fixed 2026-08-18)
- **Worker crashed under `pythonw`** (windowless launch = the .cmd): inherited
  stderr is None → worker's log write threw → base never built → empty Base/Both
  preview. Fixed: `_log()` guards None stderr; server routes worker stderr to
  `_worker.log`. Also: BASE_TIMEOUT 120→300s (cold OCP import under machine load,
  e.g. other uvicorn servers running, was tripping a false "worker crashed"), and
  server now background-**prewarms** the worker at startup.
- **Base/Both toggles showed nothing**: they only switched visibility. Now they
  auto-build the base if missing/stale (`setShow` → `genBase(false)`).
- **Changing holder type didn't update preview**: only set baseDirty. Now base +
  holder param changes live-rebuild via `scheduleBase()` (debounced) while the
  base is visible. m10=6486 verts (flat + underside nut pocket), b22=9216 (recess
  + 2 screw holes) — verified the preview changes.

### build123d gotcha (fixed)
`extrude()` with an implicit "pending sketch" does NOT work inside a nested
helper function (only in the BuildPart's own `with` block). Pass the sketch
explicitly: `extrude(to_extrude=sk.sketch, ...)`. See `_cut_holder_mount`.

## Phase 3 DONE + verified 2026-08-18 (perforation patterns)
Holes cut through the thick wall and sealed with rim walls -> watertight by
construction (collar + top band stay solid). Pure numpy, no new deps.
- Patterns (`pattern` param): **dots** (round holes, hex-packed — user's request),
  **honeycomb** (hexagons), **voronoi** (organic), **gyroid** (wavy struts),
  **grid** (square). `_perforation_solid` returns a solid/hole cell mask;
  `_hole_rims` seals boundaries; `_declink` removes diagonal (checkerboard) pinches
  that were causing non-manifold edges in voronoi/gyroid. All 5 verify watertight
  at res 200. Params: pat_cols, pat_rows, web (web/hole size), pat_seed, top_solid.
- UI: Perforation group + pattern dropdown; live-rebuilds via scheduleShade.

### Bug fixed: rapid-fetch hang (was blamed on the app; also laptop slowness)
Python http.server default HTTP/1.0 races with browser socket reuse -> live
sliders (many quick fetches) hung. Fix: `protocol_version="HTTP/1.1"` + `timeout=30`
on Handler (every response already sets Content-Length). Debug counters removed.

## Phase 5 DONE (implemented) — operator-stack editor (2026-08-18)
The shade surface is now an **ordered operator stack** instead of a flat radius
field. Wired end-to-end and confirmed watertight; UI works, needs one clean
verify pass for reorder/mute.
- **Engine** (`lamp_engine.py` ~L144-251): `OP_SCHEMA` (5 op types: form/twist/
  flute/ripple/noise + their sliders), `STACK_DEFAULT` (= classic default shade),
  `eval_stack()` runs the stack top→bottom (**order matters**: twist before flute
  = spiralling flutes; duplicate ops allowed). `_default_stack_from_flat()`
  synthesises a stack from the legacy flat SHADE params so **old presets/flat
  callers still render**. `build_shade_mesh()` consumes `params["stack"]` (L389)
  and couples the `form` op back to the bayonet/base dims.
- **Server** (`server.py`): `make_shade()` accepts a `stack` list (L117);
  `/api/defaults` exposes `op_schema` + `stack_default` (L184-185).
- **UI** (`index.html` L206-251): `renderStack()` draws the "◆ SHAPE" panel — each
  op is a card with per-op sliders, a mute checkbox, ▲/▼ reorder, ✕ remove; "+ Add"
  dropdown adds any non-form op; `form` can't be deleted; presets rebuild the stack
  (`stackFromFlat` fallback for legacy presets).
- **Verified — engine**: default stack + an extra ripple → 53,760 tris, watertight
  True (`verify_mesh` euler 0, 0 boundary/nonmanifold edges).
- **Verified — UI (partial, `_verify_ui_p5.py`)**: initial stack renders
  form/twist/flute (3 cards, shade 99,840 tris), **+ripple adds to the stack**, no
  page errors. Reorder/mute NOT yet exercised — the harness crashed on a `▲` char
  under Windows cp1252 (NOT an app fault); **fixed** with
  `sys.stdout.reconfigure(encoding="utf-8")`. Re-run to finish that check.
- **UX note to decide**: a newly-added op gets each param set to its slider *min*
  (add-button code `op[k]=mn`). For ripple/flute that means waves/amp=0, so
  `eval_stack` skips it → the just-added op is a **visual no-op until you raise a
  slider**. Confirm whether adds should seed sensible defaults (e.g. `OP_DEFAULTS`)
  instead so the op is visible immediately.
- **Scope note**: this is a linear operator STACK, not a branching node-graph.
  Matches VISION's "node UI wraps the same backend"; a true graph UI is still open
  if wanted.

## Remaining / next
- Phase 2 polish (deferred by owner until after P3-5): **base is too flat** — add
  real body height (a taller skirt below the collar), less-pancake proportions, a
  self-tightening ramp on the pocket floor, a detent to resist loosening, strain-relief.
- Then Phase 3 (perforations, needs `sdf`/`manifold3d` OK), Phase 4 (batch), Phase 5 (nodes).

## (earlier) In progress
- (none)

## UI verified with Playwright (2026-08-18, headless Chromium, WebGL 2.0)
Screenshots in `screenshots/` (gitignored). Re-run: `python _verify_ui.py` with the
server up. Confirmed: initial shade render, live slider regen (twist changed bbox),
preset load (Deep Flute Cone → 16 flutes, sliders + geometry updated), base build
(build123d, STL+STEP, renders in Base/Both views). No JS page errors.
- **Bug found + fixed**: `GET /api/preset/<name>` didn't URL-decode, so a preset
  with a space ("Deep Flute Cone" → `%20`) 404'd and silently failed to load.
  Fixed with `urllib.parse.unquote` in `server.py`. Restart the server to pick up
  server.py changes (no hot-reload).
- Test note: base build cold-warms build123d (~40s); a naive 90s Playwright poll
  can time out under browser load. It is NOT an app fault (curl builds in 0.64s warm).
- Cosmetic (Phase 2): default base is a wide flat disc (141.8mm dia x 21mm) and its
  lip sits slightly proud of the shade in the Both view. Redesign in the base pass.

## Escalated / needs owner decision
- **Phase 3 dependency approval**: dense perforation patterns (honeycomb, voronoi,
  gyroid, lattice) should use the mesh/SDF route — `sdf` (fogleman) and/or
  `manifold3d`. These are pip installs; owner must OK before adding.
- Base fitting spec: confirm the target socket standard (E27 shade-ring vs M10
  nipple vs a specific IKEA cord set) so the collar/bore can be dimensioned to it.

## Lessons learned
- `np.unique(axis=0)` on the edge array is slow (~1.2 s); encoding each edge as a
  single int64 key `lo*(V+1)+hi` drops verify to ~40 ms.
- Binary STL: build a structured-dtype record array and `tobytes()` — the
  per-facet `struct.pack` loop cost ~1.8 s, vectorized is ~0.1 s.
- The thin-wall tube is topologically a torus → Euler characteristic 0 with zero
  boundary edges is the "watertight" signature; don't expect Euler 2.
- build123d import/warm is the only slow thing (~15 s once); keep it out of the
  shade path entirely so preview stays instant.

## Roadmap
- **Phase 1** ✅ continuous-wall family (form/flutes/twist/ripple/noise) + base + Studio UI.
- **Phase 2** base polish: twist-bayonet / 3-tab snap join, socket-standard dims, cord strain relief.
- **Phase 3** perforation patterns via SDF/mesh (honeycomb, voronoi, gyroid, box lattice) + overhang guardrail.
- **Phase 4** batch/catalogue export (grid of variations → STL set + thumbnails).
- **Phase 5** ✅ operator-stack editor over the same operator backend (linear stack;
  add/reorder/mute/remove ops). True branching node-graph still optional.
