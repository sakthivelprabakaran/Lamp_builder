# A1 print review — retained tray v3

This revision uses a flat tray and upright holders with integral tongues. Print one tray and four identical holders. Two diagonally opposite tray apertures catch the hooks; the other two are clearance apertures. No separately printed locking parts are required.

## Declared setup

- Bambu Lab A1, 0.4 mm nozzle, Textured PEI Plate.
- 0.20 mm Standard process, 3 wall loops, supports disabled.
- Generic PETG profile is provisional. Use the purchased filament's validated profile for physical samples.
- Tray: broad flat underside on the bed, 163.4 × 163.4 × 3 mm; approximately 46 mm nominal clearance on each side of the 256 mm bed when centred.
- Holder: sleeve/stem bottom on bed, sleeve axis vertical; overall height 75.6 mm. Do not rotate the side shelf onto the bed.

## What was checked

Every changed STL was sliced with the requested OrcaSlicer 2.4.2; prior Bambu Studio 02.08.04.57 evidence is retained separately. The emitted extrusion footprints were screened at 0.20 mm raster resolution across all layers. The sliced 3MF files preserve the settings and toolpaths; per-part JSON records identify the exact STL, slice, analysis and settings hashes.

The flat tray has 15 layers and no components without previous-layer footprint overlap. Its longest estimated unsupported bridge span is 1.80 mm, over the interior infill beneath the top skin, rather than an exposed hanging latch. Orca reports this top-skin section as an internal bridge; no floating-shell sections occur in its feature comments.

The holder's original 14 mm shelf bridge and two newly detected floating starts were corrected in CAD before delivery. Final holder results are recorded in orca-holder-slice/slice-evidence.json: 378 layers, zero candidate unsupported islands, and estimated internal bridge spans up to 3.48 mm. The final hook uses a 45-degree underside ramp and a 0.4 mm retaining toe; actual hook toolpaths advance by 0.2 mm, 0.2 mm, then 0.4 mm at the retaining toe. That final step is approximately one extrusion width, and still requires physical edge-quality confirmation. Bridge lengths in the reports are estimated unsupported spans, not total bridge extrusion lengths.

## Material and structural limits

The upright tongue flexes across the Z-layer interfaces. Three wall loops produce a filled 1.6 mm beam, but do not establish adequate layer bonding, allowable bending strain, snap force, fatigue or heat resistance. PETG print samples must confirm the hook underside, release, retention and repeated cycling. Keep the holder's small hook free of damage during bed removal and handling.

No supports are generated in these review slices, so no support removal from the mating bore or flexible tongue is proposed. Support-free slicing and a connected-layer screen are not physical printing certification. The actual shelf bridges, hook edge and material performance still need a physical sample.

## Orca profile warning

The bundled provisional Generic PETG profile slices at 255 C nozzle and 80 C textured-plate bed. Orca emits `bed_temperature_too_high_than_filament`. No temperature is approved for the purchased filament by this review; confirm and save its validated settings before printing. Holder slice includes a 5 mm adhesion brim, removed only at the stem bottom. The tray has no support-removal operation.
