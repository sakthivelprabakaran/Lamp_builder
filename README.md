# Lamp Studio

A parametric lamp-shade + holder-base design engine (build123d), inspired by
Grasshopper/Rhino. Turn sliders → get an family of unique, geometrically screened
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
Perforated designs use a staggered contour mesh with flowing crossing ribs. Graph fields vary aperture density and size; the mesher constrains roof slopes and web clearances for upright printing.

## Printing
- **LED / cool bulbs only** — PLA/PETG will soften near hot bulbs.
- A1 target: 0.4 mm nozzle, upright Z, supports disabled, 250 mm design envelope. Perforated shades require ordinary wall printing, not vase/spiral mode.
- See [PRINTING.md](PRINTING.md) for geometry constraints, verification and limits.
- Base bore defaults to 10.5 mm (clearance for an M10 lamp nipple); set it to
  match your socket/cord kit.

## Files
`lamp_engine.py` geometry core · `server.py` loopback web server · `worker.py`
build123d base worker · `index.html` three.js UI · `presets/` saved params ·
`output/` generated STL/STEP. See `SKILL.md` (how), `VISION.md` (why),
`STATE.md` (where we are).

## Requires
Python 3 and `numpy` for shades. `build123d` is required only for base/STEP generation and is unavailable in this environment. No new geometry dependencies were added.

## Customer experience
Open `/customer` on the same local server for the separate Lume configurator.
The internal studio remains at `/`. The customer library contains individually
geometry-screened products across twelve silhouettes, woven/perforated structures
and continuous sculptural surfaces, plus fine rounded-hole studies. Search,
silhouette and structure filters, lazy thumbnails and twelve-card pages keep it
manageable. Only the chosen product loads a full mesh. Customization offers height,
density or relief depth, color and a complete-lamp/shade-only visualization.
The matching base preview uses engine mating dimensions. Downloads contain the
shade STL only; base CAD export requires unavailable build123d. Lighting is a
visualization, not an electrical/thermal/material validation. `/customer-mobile-preview`
is a real 390 × 844 iframe for responsive review. See CATALOG.md for per-product
validation states and the workflow for adding products one at a time.
