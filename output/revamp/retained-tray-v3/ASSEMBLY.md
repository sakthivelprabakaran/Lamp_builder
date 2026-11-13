# LUME — press-in shade-base tray, revision 3

## Customer parts
- 4 identical snap-reinforced bottom shade holders.
- 1 flat tray.
- No separate locking clips, wedges, pins or tray screws.

Each holder has an integral tongue. Two diagonal tray apertures catch the tongue hooks; the other two apertures are larger clearance openings. This keeps all four holders identical while requiring only two simultaneous finger presses for removal.

## Assemble
1. Install the upper rail frame first. Slide each bottom shade holder onto its post with its panel receivers facing inward. Its long sleeve rests on the upper rail connector.
2. Keep the tray level, central bulb-holder opening in the middle. Line up all four apertures over the four upward tongues.
3. Lower the tray onto all four reinforced seats. Press gently at the two diagonal catch positions until both hooks emerge above the tray. Check all four corners are seated and both hook shoulders overlap the tray top. An audible click is possible, but is not a verified acceptance test.
4. Install the remaining shade parts. The tray is mechanical support only; its central 32 mm opening retains the earlier review interface. It is not a confirmed mount or terminal enclosure for any particular India-sourced B22 or E27 holder.

To remove, press the two diagonal locking tongues toward the tray centre, then lift the tray level. The two clearance apertures do not catch. Do not pull the tray against engaged hooks.

## Dimensions and print orientation
- Tray: 163.4 × 163.4 × 3 mm. Print its broad underside flat on the bed.
- Four identical holders: print with the long square-post sleeve upright, bottom opening on the bed.
- Post sleeve bore: 25.6 × 25.6 mm, nominal 25 mm timber.
- Reinforced seats: 16 × 16 × 4 mm. Tray bears on 14 × 14 mm at each corner (196 mm² per seat).
- Tongue: 1.6 mm thick × 8 mm wide; approximate free span 13.8 mm. Root and support brace remain rigid in the CAD interference check.
- Hook shoulder nominally 0.3 mm above the seated 3 mm tray.
- Catch-side aperture clearance: 0.35 mm; release clearance permits the checked 0.9 mm inward free-span displacement.

## What was checked
Exact CAD solids and STEP reloads are valid. Delivered STL meshes are watertight with no boundary or nonmanifold edges. Nominal tray insertion was sampled every 0.5 mm over 25 mm; the rigid holder roots and bodies had zero overlap. Nine lateral positions spanning ±0.1 mm in X/Y were additionally sampled every 1 mm over the final 12 mm of insertion and passed. The seated assembly has zero rigid overlap. Raising the unpressed tray by 1 mm gives 5.06 mm³ intersection at the retaining hooks, confirming geometric lift-out obstruction. Moving only the permitted free-span envelopes inward by 0.9 mm and sampling the 25 mm lift every 0.5 mm gives zero overlap.

These are discrete geometric tests, not continuous beam deformation or force simulation. See verification.json and the slicer report for revision-specific evidence. Archived failed reports document corrected aperture orientation and release-clearance mistakes.

## Remaining prototype qualifications
The upright holder tongue bends across deposited layers. Printed strength, click feel, required assembly force, fatigue, PETG creep, actual timber sleeve grip and thermal behaviour are not verified. The hook underside has a 45-degree 0.4 mm ramp and a 0.4 mm flat retaining toe. That small ledge is an overhang requiring inspection in the actual slicer profile. Use the delivered slicer evidence; do not describe this geometry as physically tested or production-qualified. Confirm the purchased bulb holder, anti-rotation, terminal enclosure and strain relief before completing electrical assembly.
