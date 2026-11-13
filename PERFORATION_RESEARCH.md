# Fine perforation studies

Primary sources consulted on 8 October 2026:

- [Artemide Shogun](https://www.artemide.com/fr/subfamily/25656/shogun): perforated
  diffusers create an interplay of highlights and shadows. Implementation:
  perforation-aware point-light shadows on the room's receiving wall and objects.
- [Mikko Laakkonen's Islet](https://www.mikkolaakkonen.com/work/islet/): tiny openings
  and folded surfaces diffuse light and vary its appearance with viewpoint.
  Implementation: new Column Pearl staggered fine openings, Urn Dew graduated
  opening sizes, and Aster Botanical flowing variation of opening sizes. These
  are original parameter/contour designs, not copies of those products.
- [Prusa modeling guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135):
  underside geometry and overhangs affect printability. Implementation: retain
  the upright geometric slope budget instead of cutting exact circular roofs.
- [Prusa bridge guidance](https://help.prusa3d.com/article/poor-bridging_1802): bridge
  quality depends on settings, speed and cooling. Implementation: individually
  slice fine openings and keep physical validation separate from geometry checks.

The new `micro_round` contour has a rounded, polygonal lower half and a steep
upper crown. It is round-looking, not a mathematical circle. Its crown rises
2 mm for each millimeter of circumferential travel, and rows are staggered.
Opening width adapts conservatively to local circumference and row spacing.
Solid collar and rim remain. Maximum nominal opening sizes are 2.2–2.7 mm;
actual openings can be smaller to preserve clearances on narrower profiles.
Requested density changes actual contour size, not just color or opacity.
The existing exact segment clearance and estimated wall export gates still apply.

Exact circular holes near the top require either a short bridge allowance or a
modified roof. No universal claim that an upright circular opening is support-free
is made. The pointed crown keeps these studies within the stricter geometric
screen. Ordinary no-support slicing and a material-specific test print remain
necessary. The room light is a qualitative rendering, not a calibrated photometric
or thermal model. Base preview dimensions come from the existing mating model;
base CAD export still requires build123d.
