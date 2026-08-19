# Lamp Studio — Vision

## The why
A parametric design engine for a **3D-printed lamp product line** (a sibling to
the Modular Hanger / MODUPLANT brand). The differentiator is not "a lamp STL" —
those are free everywhere — but a **Grasshopper-style generative tool** that
produces an effectively infinite family of unique, complex shade patterns plus a
distinctive, easy-to-assemble holder base. Every SKU comes out of one tool by
turning parameters, so the catalogue can grow without modelling each shade by hand.

## North-star goals
1. **Infinite patterns from composable operators**, not hardcoded shapes.
   Form × flutes × twist × ripple × noise (Phase 1); + perforation fields
   (honeycomb / voronoi / gyroid / lattice) in later phases.
2. **Print-ready by construction.** Watertight meshes, printable wall thickness,
   support-free geometry, and (for the continuous-wall family) vase-mode friendly.
3. **A unique base that assembles tool-free** and mates to a *standard* fitting
   (E27/E26 socket ring or M10 nipple / IKEA-style cord set) so no custom
   electrical parts are needed. Shade and base are separable SKUs (mix & match).
4. **Live, tactile UI** — turn a slider, see the shade update instantly.

## Constraints
- **LED / cool bulbs only** — PLA/PETG deform near hot incandescents. State this on listings.
- Min wall ≈ 0.8–1.6 mm for translucency + strength.
- Perforations (later phases) must stay support-free (≤45° overhang).
- Loopback-only tool; it runs the design engine locally, never exposed off-machine.

## Non-goals (for now)
- A full node-graph editor (Phase 5, optional). The operator engine is authored so
  a node UI can wrap the *same* backend later without a rewrite.
- Cloud / multi-user. Single-machine desktop tool.

## Kernel strategy (the load-bearing decision)
build123d/OpenCASCADE is a BREP kernel: great for exact parts (base, bores,
threads), **slow and fragile** for dense/organic surface patterns. So:
- **Shade** → pure-numpy parametric **mesh** (always watertight, instant).
- **Base** → **build123d** BREP.
- Dense perforation patterns (Phase 3) → mesh/SDF route (`sdf`, `manifold3d`),
  never OCC booleans.
