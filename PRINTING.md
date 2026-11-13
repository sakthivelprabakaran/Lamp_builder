# Upright A1 shade design

The current manufacturing target is a Bambu Lab A1, 0.4 mm nozzle, upright Z,
without supports. Geometry checks are a screen, not a print guarantee. Material
is undecided. The successful slicing review uses a provisional Generic PLA profile and
0.20 mm layers; its settings must be reviewed for the actual filament.

## Geometry

`print_geometry.py` meshes staggered rhombus tiles with exact pointed aperture
contours. Uniform subdivision refines curved surfaces without removing strands
or changing opening topology. The two crossing rib families share a continuous
web. A bounded continuous shear creates flowing/spiralling ribs. Organic fields
vary opening size and grade density; wave fields vary rib widths and flow.
Solid collar and rim bands connect every family. Openings never intersect them.

- Minimum aperture-to-aperture clearance target: 1.6 mm. Construction reserves
  an additional 20% to accommodate shear; the export measures actual contour
  separation in 3D and rejects clearances below 1.6 mm.
- Roofs rise at least 2.0 mm per circumferential mm before flow; maximum flow
  travel is 0.30 mm per vertical mm. Wide cell aspect ratios narrow the aperture to preserve the roof slope;
  configurations with no resolvable opening are rejected.
- Outer radial slopes are bounded to 0.55 mm per vertical mm. Inner inward growth
  uses the same bound, including the locking pocket chamfer. Decorative fields
  can still fail the final triangle overhang check; those exports are refused.
- Wall radial offsets compensate for local vertical and circumferential slopes.
  Export reports the minimum paired-facet normal wall estimate and rejects
  estimates below 0.8 mm. This is not a full medial-axis or self-intersection test.
- The build envelope is 250 mm on each axis, leaving margin inside the A1 bed.
  Generated geometry starts at Z=0. Preview coordinates are centered on XY=0;
  the separately supplied review STL is centered at XY=(128,128) on the A1 bed.

Existing rattan presets now use graceful, less exaggerated bulges and denser
crossing ribs. Graph presets retain field variation but omit the former sharp
radial displacement ridges. This changes design geometry, not only tessellation.
Legacy cell deletion remains available to code callers with `support_free=0`;
its meshes do not imply manufacturing suitability.

## Export gate and verification

Export rejects boundary/nonmanifold edges, multiple components, degenerate
triangles, inconsistent winding, nonfinite coordinates and nonpositive volume.
In A1 mode it also rejects excessive dimensions, underside triangles steeper
than 45 degrees from vertical above the bed, inadequate measured aperture
clearance, or inadequate estimated normal wall thickness. The catalogue says
“geometry checks passed,” not “print certified.”

Run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_print_geometry -v`.
Regression tests cover every preset, graph weave at preview/export resolution,
invalid dimensions, degenerate closed meshes, blocked export writes and a
successful export matching preview contour topology.

Global mesh connectivity is not per-layer support analysis. The approved woven
model was also sliced and screened across all 1,150 emitted layers at 0.20 mm
raster resolution, with no components lacking previous-layer overlap. Three
bridge sections and 26 floating-shell sections occur in the mounting collar,
not the woven body. Raster tolerance and bridge performance remain limitations. Pointed roofs and
continuous ribs are designed to avoid broad bridges and mid-air strand starts,
but actual slicing must check layer islands, toolpath widths and bridge spans.
Cooling, speed, adhesion, material, tolerances and structural durability still
need a physical test. Base mating is not physically validated; build123d is
unavailable in the current environment. No print job is sent automatically.

## Reproduce the slicing review

On macOS with Bambu Studio installed:

```sh
python3 tools/slice_a1.py output/revamp/rattan-flow-a1-upright.stl
python3 tools/analyze_toolpaths.py output/revamp/rattan-flow-a1-review.gcode
```

The first command creates a sliced 3MF with supports disabled using isolated
preferences. Extract `Metadata/plate_1.gcode` from that 3MF for the second command.
The toolpath screen rasterizes actual extrusion widths at 0.20 mm and reports
components without previous-layer overlap. Its conservative dilation can hide
sub-resolution gaps; it is evidence to review, not print certification.

Bambu CLI references: https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage
The successful review used Bambu Studio 02.08.04.57.
