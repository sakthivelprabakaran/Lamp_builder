# Lamp Studio review — 7 October 2026

Running URL: http://127.0.0.1:8776/ . Launched the saved project with the existing Python 3.9 interpreter. NumPy 1.26.4 is available; build123d is absent. No dependencies were installed and no product code was changed.

## Prioritized findings

1. **High — preset loads depend on previous state.** Reproduction: load Woven Rattan Gourd, then Spiral Flute Vase. The shape form changes to the spiral values, but Pattern remains Woven rattan, hoop width remains 9, and top band remains 14. Spiral Flute Vase.json omits those fields. `loadPreset` in index.html merges partial data into the current shade/base using Object.assign instead of rebuilding from defaults. This also affects empty base objects. Reset both parameter objects from defaults before applying a migrated preset, and test the same preset after several different predecessors.

2. **High — base and test-fit journeys are blocked on this Mac.** Both buttons produce “Base build timed out or the worker crashed.” `_worker.log` identifies `ModuleNotFoundError: No module named 'build123d'`. README incorrectly assumes the dependency is already installed. Add a dependency manifest, supported Python/environment setup, a macOS launcher, and startup capability checks. Show the precise missing dependency and disable unavailable actions until setup is complete. Base assembly, STL/STEP quality, holder fits, and LED module geometry could not be verified.

3. **High — export verification does not enforce a gate (source-confirmed).** In server.py make_shade, verify_mesh returns ok and rep, but ok is ignored; the STL is written and response ok remains true even when watertight is false. index.html exportShade downloads whenever d.ok is true. Reject invalid meshes before writing/downloading; provide the failed check and corrective advice. The tested default export passed; an invalid-mesh download was not reproduced during this review.

4. **Medium — preset values and sliders disagree.** Woven Rattan Gourd loads Bulge / waist 72 while its slider is capped at 60. The default weave turns label is 0.35 while the range input rounds to 0.36. Align schemas, step sizes, and preset validation; add numeric entry for exact dimensions. Avoid silently clamping only the UI while geometry retains another value.

5. **Medium — controls expose irrelevant settings and lack accessible names.** With solid-wall Pattern selected, Voronoi and all weave settings remain visible. M10 holder mode still exposes recess and screw fields. AX snapshots show unnamed sliders and checkboxes; graph delete controls appear as plain text “✕”. Show applicable settings by mode, associate labels with inputs, and make graph actions keyboard-operable buttons. The rattan hint refers to “Cells around (Quality)” although Cells around is under Perforation and Quality contains resolution controls; correct the instruction.

6. **Medium — graph mode changes the design without clear migration context.** From the rattan preset, switching to Node graph exposes the default Form 70/55/18 and Voronoi graph rather than converting the current stack. Switching back restores the stack. Explain that each mode uses a distinct design, offer a deliberate conversion/start action, and add undo/reset plus keyboard wiring support. Node creation was verified; arbitrary wiring and cycle handling were not exercised.

7. **Medium — printable status is too broad.** The catalogue marks printable from watertight and one component only. The tested batch is marked printable in manifest.csv while the restored preview warns that fine cane is thinner than the resolution cell and will look ragged; thumbnails visibly show coarse irregular cane. Label this as mesh validation, surface minimum-feature/resolution warnings on each card, and clearly distinguish fast scouting exports from final print exports. No physical print or slicer validation was performed.

## Flows reviewed

- Launch and initial 3D preview: succeeds after allowing localhost binding outside the sandbox; default shade shows 99,840 triangles and preview/export resolution information.
- Slider adjustment: height changes from 200 to 201 and live preview rebuild begins.
- Presets: loaded Woven Rattan Gourd and Spiral Flute Vase; saved a uniquely named temporary preset and verified it appeared in the list. Complete reload round-trip was not verified.
- Stack/graph switching and adding a Checker node: succeeds. Wiring, deletion, operator reordering, and all individual pattern combinations were not exhaustively tested.
- Default shade export: succeeds, 177,600 triangles, watertight true, output/shade.stl created.
- Base and test-fit: fail due to missing build123d; holder configuration controls reviewed.
- Catalogue: two fast-resolution Height variants (180 and 190), completed in 25 seconds. Contact sheet opened and displayed thumbnails and STL links. Manifest reports both watertight, one component, and no duplicates. ZIP exists; download/unzip and Stop mid-run were not tested.

Evidence: output/review-screen.jpg; output/catalogue/review-smoke/index.html; output/catalogue/review-smoke/manifest.csv; _worker.log. Generated review exports remain under output/. The temporary saved preset was moved to /private/tmp/lamp-review-temporary-preset.json to avoid cluttering the preset list.

## Limits

Desktop browser review only; responsive/mobile layouts, physical assembly, heat suitability, every preset/pattern, and all geometry limits remain unverified. A temporary automatic browser approval timeout interrupted inspection, then the retry succeeded. The server is left running in the current session.
