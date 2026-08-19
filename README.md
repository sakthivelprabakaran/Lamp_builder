# Lamp Studio

A parametric lamp-shade + holder-base design engine (build123d), inspired by
Grasshopper/Rhino. Turn sliders → get an infinite family of unique, print-ready
shades and a matching, tool-free-assembly base. Part of the 3D-print product line.

![port](https://img.shields.io/badge/localhost-8776-blue)

## Quick start
Double-click **`Start Lamp Studio.cmd`** (or `python server.py`), then open
http://127.0.0.1:8776. The shade updates live as you drag sliders.

- **Export shade STL** — full-resolution, watertight-verified.
- **Generate base** — build123d adapter, exported as STL **and** STEP.
- **Presets** — save/load full `{shade, base}` parameter sets.

## The idea
A shade is one radius field `r(θ, z)` built from composable operators:

| Operator | Params | Effect |
|---|---|---|
| Form | height, r_bottom, r_top, bulge, bulge_pos | cylinder / cone / vase / flare / waist |
| Flutes | lobes, lobe_amp | vertical fluting around the shade |
| Twist | twist_turns | spins the flutes into a spiral |
| Ripple | ripple_waves, ripple_amp | horizontal waves up the height |
| Organic | noise_amp, noise_scale, seed | irregular organic surface |

Combined, these span an effectively infinite set of continuous-wall shades.
Perforated patterns (honeycomb / voronoi / gyroid / lattice) are Phase 3.

## Printing
- **LED / cool bulbs only** — PLA/PETG will soften near hot bulbs.
- Wall 0.8–1.6 mm prints translucent and glows well; thin single-wall shades
  slice nicely in **vase / spiralize** mode.
- Base bore defaults to 10.5 mm (clearance for an M10 lamp nipple); set it to
  match your socket/cord kit.

## Files
`lamp_engine.py` geometry core · `server.py` loopback web server · `worker.py`
build123d base worker · `index.html` three.js UI · `presets/` saved params ·
`output/` generated STL/STEP. See `SKILL.md` (how), `VISION.md` (why),
`STATE.md` (where we are).

## Requires
Python 3, `numpy`, `build123d` (already installed on this machine). No other deps
until Phase 3, which will need `sdf` / `manifold3d` (owner approval first).
