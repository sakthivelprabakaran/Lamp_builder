# Simple standing lamp — part-by-part decision plan

Status: reviewable first-prototype plan, not a mechanically validated product. Preserve the simple appearance: four exposed wooden posts, individual foot caps, and a patterned light chamber at the top. Two horizontal four-rail frames are now selected: one above the feet and one below the shade. No diagonals, shelf or outriggers. Twelve table variants remain in Lume; three standing variants differ by panel pattern and provisional height. A double-rod version is a future idea with no assumed section or construction.

## Latest decision: wedge female sleeve and axial rail screw

Active lamp model: wedge-tightened female sleeve plus pressure pad, paired with the axial-screw male cup. Unused female retaining-pin holes removed. Current files are in `output/revamp/selected-wedge-axial`; earlier clamp and wedge review files stay unchanged for comparison.



Owner decision: retain both female versions for comparison. The bolt-tightened split clamp and the earlier wedge-tightened sleeve remain in separate export folders; neither is discarded or selected as final pending owner inspection. The male rail cup with its axial screw is shared.

This supersedes the screwless wedge/pad/pin proposal and older fastener inventories below. Two printed parts now define the revised rail connection:

- **Female:** one sleeve around each intact vertical 25 mm post, carrying two female dovetail receivers. A split collar is tightened by one external clamp bolt and captive nut. The bolt does not enter or drill the wood.
- **Male:** one square rail-end cup with a dovetail tongue. A recessed axial screw passes through the tongue and end plate into the timber rail end. No printed wedges, pressure pads or additional loose locking pins.
- **Assembly:** attach sleeves to posts and male cups to rails; align both rail-end tongues above their sockets; lower the rail until both tongues seat on the closed receiver floors. Lift to remove. Positive anti-lift retention is not included in this revision.
- **Quantities:** eight dual female sleeves and sixteen male cups for two four-rail frames; eight clamp bolt/nut sets and sixteen rail-end screws. Hardware dimensions are provisional until owner fit checks.
- **Evidence:** both revised meshes are closed single solids; nominal one-corner common-volume checks report zero unwanted overlap. Direct inspection STLs and an assembled reference 3MF are in `output/revamp/simple-dovetail`. Print orientation/supports require slicing; no support-free connector claim.

The older v2 STEP archive and v3 yellow-piece renders are historical. Revised axial screw and clamp geometry is v4. The upper frame remains 65 mm below the chamber. Shade-collar retention and actual holder selection remain independent work.

## 1. Freeze inputs and proportions

- Purchased posts: **25 mm square**. Measure both axes of all four posts at several heights; use the largest section and check straightness before choosing a bore.
- Structural connectors and individual foot caps: **PETG**, confirmed by owner.
- Shade: owner's translucent/transparent filament described as Newmaker's Lab. Exact product/polymer remains unconfirmed; do not reuse PETG assumptions for its shrinkage, temperature or opacity.
- Exposed-leg height and illuminated height are separate parameters. Initial light chamber: **304.8 mm**. Compare 1066.8 or 1219.2 mm exposed legs plus that chamber (1371.6 or 1524 mm total) with the earlier 1219.2 mm total interpretation. Dimensions remain provisional.
- Initial upper footprint: 220 mm square; aesthetic width is still a proposal. Current 25 mm baseline gives 25.6 mm sockets, 31.2 mm collar outside width, 163.4 mm panel width, two 152.4 mm-high panel segments per side.

## 2. Choose attachment before refining the patterns

**Recommended first option:** removable PETG collars around the intact posts, with two inward-facing printed receivers on each collar. Each receiver holds the edge of one neighboring flat panel. Four posts separate the four side panels; the panels do not need to merge together or share a printed corner edge.

| Option | Appearance and serviceability | Consequence | Decision |
|---|---|---|---|
| Printed collar receivers | Small visible connector bands; panels and collars removable | Requires a positive height stop and removable upper retention | Recommended prototype; details below still require review |
| Short printed edge clips | Less visible banding | More separate clips/fasteners and higher local loads | Later aesthetic alternative |
| Routed grooves in wood | Cleaner uninterrupted posts | Permanent woodworking, groove tolerance, insertion order and post weakening must be assessed | Undecided; no grooves assumed or authorized |

Avoid a large printed cage: the shade pattern and timber are the main visual elements.

## 3. Inventory the first assembly

Quantities below assume four sides, a 304.8 mm light chamber and two panel segments per side.

| Part | Quantity | Material / purpose | Current state |
|---|---:|---|---|
| Square wooden post | 4 | Purchased 25 mm timber; continuous clean exposed legs | Layout modeled; actual section/straightness unmeasured |
| Individual closed-bottom foot cap | 4 | PETG; floor contact and rod-end protection | Mesh modeled; floor 2.4 mm, socket 25.6 mm, wall 3 mm, overall height 20 mm; fit pending |
| Bottom corner/support collar | 4 | PETG; two panel receivers, panel bottom stop and light-tray shelf | Mesh modeled; **positive fixation to the post is missing** |
| Mid-seam through collar | 4 | PETG; locate paired panel segments at the horizontal seam | Mesh modeled; removal/sliding path and seam fit pending |
| Upper through collar | 4 | PETG; locate upper panel ends and link the upper corners through panels | Mesh modeled; must be positioned with top at the post end |
| Removable top retaining cap | 4 | PETG; prevent panel/collar lift | Mesh modeled, 3 mm thick, 4.4 mm central through-hole; fastener selection/pilot hole and vertical play pending |
| Patterned panel segment | 8 | Owner's translucent filament; four sides × two segments | Real flat meshes; three standing patterns; seam/warpage/optical tests pending |
| Light support tray | 1 | PETG proposed; removable upper-chamber support | Mesh modeled with tie slots and cable edge entry; specific LED mount absent |
| LED/diffuser/holder | 1 set | Owner-selected low-voltage light hardware | Qualitative preview only; actual dimensions, mounting and heat requirements missing |
| Rod-fit coupon | 1 per chosen clearance | PETG; verify socket before connector batch | Mesh modeled; physical print pending |
| Panel-slot coupon | 1 per selected panel thickness/clearance | PETG receiver plus sample shade strip | **Needs a dedicated small coupon**; rod coupon alone is insufficient |
| Cable U-guide and removable cover | 7 pairs at 1371.6 mm total; 7 at 1524 mm | PETG proposed; accessible external cable route | Geometry exists in ≤220 mm lengths; full-height route, attachment and appearance need review |
| Tie-based strain-relief plate | 1, if needed by chosen light hardware | PETG proposed; accessible cable retention near upper tray | Geometry exists; pull/bend testing and mounting unresolved |
| Bottom-collar height-fixing fastener | 4 minimum, proposal | Accessible lateral screw into pilot-drilled timber or a removable split-clamp alternative | **Not modeled or selected**; essential decision before assembly |
| Top-cap fastener | 4, proposal | Accessible central fastener into post ends | Hole modeled; screw/pilot/end-grain retention undecided |
| Cable-guide ties/fasteners | As needed after route review | Removable attachment | Not selected; minimize visible additions |

| Rail part | Quantity | Material / purpose | Current state |
|---|---:|---|---|
| Horizontal timber rail | 8 | Matching 25 mm square timber proposed; material/section unconfirmed | Two four-rail perimeter frames; center heights 70 mm and 50 mm below shade proposed |
| Male dovetail rail shoe | 16 | PETG; factory-fastened to each rail end | Exact solid and printable mesh modeled; open-top shoe and two accessible fixing holes |
| Female dovetail receiver | 16 | PETG; two receivers per post at each frame level | Exact solid and printable mesh modeled; upward-open slide, closed floor, timber fixing holes |
| Removable locking cross-pin + keeper | 16 sets | Proposed 4 mm pin through 4.2 mm holes | Matching receiver/male holes modeled; purchased hardware and keeper not selected |
| Rail-shoe timber fastener | 32 proposed | Two per male shoe, accessible from underneath | Holes modeled; screw length/pilot/wood strength pending |
| Receiver timber fastener | 32 proposed | Two per female receiver; factory assembly before inserting rail | Holes modeled; adjacent face screw paths must be staggered/checked |

The prototype ZIP includes geometry for the existing parts. It does not include a finalized hardware kit or prove that loose socket collars hold their height. Do not treat the decorative preview as a finished attachment system.

## 4. Decide the bottom stop, seam and top retention

1. **Bottom height fixation is the first engineering decision.** A 0.6 mm-clearance sleeve is a sliding fit, not a clamp. Recommendation: one accessible side fastener per bottom collar into a small pilot hole in timber; no routed grooves. Alternative: a split PETG clamp with a captive nut, which adds visible hardware and parts. Decide this before moving to the full lamp.
2. Panel receiver: nominal panel 2.0 mm, slot 2.4 mm (0.2 mm each side), nominal insertion 8.8 mm. These are starting tolerances, not measured PETG performance.
3. Bottom receiver floor: 1.2 mm; intended panel-to-floor bearing contact. The adjacent inward shelf supports the tray. Confirm the tray seats without contacting the panels or wood.
4. Two panels on the same side currently have a flush horizontal seam with intentional face contact. There is no snap joint. Check flatness and whether a small seam clearance/registration feature is needed; do not add decorative complexity before testing.
5. Mid and top collars use through slots; they must slide along the posts without blocking panel insertion. The 25 mm timber forms the visual corner, with separate perpendicular panels kept apart by the post.
6. Top cap prevents lift, using accessible removable hardware. Specify vertical tolerance and cap/fastener position. Current zero-clearance end contact is an ideal nominal model and needs allowance for printed/wood variation.
7. No full upper lid is proposed. Keep the crown open for the first aesthetic study. The patterned panels and corner receivers form the upper frame; racking/load suitability is not verified.

## 5. Fit the light and cable to actual hardware

Keep the light support inside the upper one-foot chamber. The current tray is removable and has two tie slots plus an open cable edge entry. Select the LED/diffuser first, then dimension its real attachment. The rendered internal tube and glow are placeholders, not supplied light hardware.

Use an external, accessible cable channel along one solid post for the first reversible prototype; no hidden drilled timber route or grooves are assumed. Review whether continuous covers distract from the clean legs. A few discreet guides may suffice once cable diameter and bend radius are known. Validate tray entry, LED lead bend, guide continuity, cover removal and strain-relief pull before finalizing quantities.

## 6. CAD sections and assembly checks — before calling fit complete

Prepare dimensioned sections from the actual part meshes, not just a beauty render:

| Section | Required check | Acceptance evidence |
|---|---|---|
| Rod through collar | 25 mm timber vs actual meshed bore; side fastener access | Positive designed clearance; no unwanted overlap; specified height fixation |
| Panel through receiver | Real slot width, wall thickness, insertion depth and bottom floor | Panel fits without forcing; intended floor contact; insertion/removal path clear |
| Two neighboring panels at a post | Orthogonal panel ends, post and both receivers | Separate meshes; no panel-panel or panel-wood penetration |
| Horizontal panel seam | Lower/upper segment faces, mid collar and tolerances | Intended contact or explicit gap; no overlapping solids; seam stays located |
| Bottom light tray | Shelf bearing, tray, panels and LED mount | Tray bears on intended shelves; required supports; no collision with panel or cable |
| Top retaining cap | Collar end, wood end, panel end, cap and fastener | Lift stop works; tolerance allowance; tool access; cap removal releases panels |
| Foot cap | Actual socket, rod seating and closed floor | 25 mm rod clears side walls and contacts floor intentionally; clean outer appearance |
| Cable route | Tray entry, every guide joint, cover and strain relief | No pinching or blocked service route; actual cable bend/pull requirements addressed |

Classify each contact as (a) intended bearing/mating contact, (b) designed clearance, or (c) unwanted overlap. Report distances/areas and tolerances. Run an assembly interference test across post, collar, panel, tray, cap and light-hardware meshes. Mesh watertightness cannot substitute for these tests. Repeat at both height interpretations and after material/clearance changes.

For serviceability, illustrate: caps removed → upper collars moved → panels lifted/slid out → tray/light accessible. Test this motion path in CAD; friction, warp and wood movement still require a physical test.

## 7. PETG print and fit strategy

1. Measure rods; print a small PETG socket coupon at the starting 25.6 mm bore and neighboring clearances. Choose the fit from actual measured timber, not a nominal number.
2. Print the dedicated panel-slot coupon and a strip of the actual translucent filament at the chosen panel thickness. Check fit after cooling.
3. Foot caps: closed floor down, socket open upward. Collar sockets: axis upright. Top caps and tray: flat. Shade segments: flat; their rounded apertures have vertical walls in this orientation.
4. Keep every individual part inside the A1 bed/envelope. Verify closed/wound meshes, minimum features and actual slicer toolpaths in the exported orientation.
5. Slice PETG connectors with the exact PETG profile and shade with its actual filament profile once identified. Existing Generic PLA reviews are provisional and do not validate PETG.
6. Print one foot, one lower collar, one upper retainer and one shade joint first. Assemble the small upper module before batching eight panels and twelve collars.

## 8. Build, assess, then iterate

- Seat four foot caps on measured posts.
- Install/fix bottom collars at the selected exposed-leg height using the chosen positive stop.
- Seat tray; route the cable; install chosen light hardware.
- Assemble four lower panels and seam collars; add four upper panels and upper collars. Check this sequence against actual slot geometry before printing the set.
- Fit removable top caps; confirm fastener access and panel lift restraint.
- Remove and reinstall one panel to demonstrate serviceability.
- Physically check sliding fit, panel warp, retention, post alignment, tipping in all directions, top racking and light heat. Caps alone do not demonstrate stability. Record outcomes; do not reintroduce rejected lower structures as a hidden requirement.
- Review the three shade patterns in Lume and in a real lit sample. Refine aesthetics only after the simple joints work.

## Completed evidence versus pending work

**Completed:** clean-leg assembled Lume preview recovered; twelve table and three standing concepts present; real panel, collar, tray, cap and guide geometry; per-part export gate; four initial frame tests; provisional Generic PLA A1 slices for one flat standing panel and one bottom connector; first foot-cap geometry check. The 25 mm catalog refresh is underway.

**Pending:** dimensioned section/interference report for the updated 25 mm assembly; positive bottom-collar fixation; panel-slot coupon; fastener and LED selection; insertion-motion/retention verification; PETG and actual shade-material slicing; physical fit/stability/heat tests. No physical print, verified joint strength, commercial validation or sales prediction is claimed.

## 9. Parametric Studio and genuine CAD export

Wire the same four-post engine into Lamp Studio with editable rod size/clearance, separate leg/light heights, width, panel thickness/slot clearance, pattern/density, foot-cap dimensions, collar/receiver dimensions, stop-cap dimensions and cable diameter. A Studio edit must regenerate its applicable part and assembled geometry; customer Lume controls remain simple. Save/load the input JSON so prototypes are reproducible.

An installed FreeCAD backend inside VibeCAD successfully built a valid analytic box. Use this backend to generate named solid parts from dimensioned profiles/extrusions/Boolean features and export genuine STEP and regeneration inputs/script (native CAD document export is optional and currently limited by the installed material library). Do not rename STL, wrap mesh triangles in STEP, or imply STEP retains a parametric feature history. Distinguish CAD B-rep construction, editable regeneration parameters and any differences from polygonal STL contours. Re-import each STEP and check solid validity, volumes and bounds. Run assembly common-volume checks for intended contact versus unwanted overlap; unfinished light hardware and fastening interfaces must remain explicit.


## 10. Selected dovetail rail architecture — supersedes earlier brace alternatives

Owner selected printed PETG male connectors on short rails and female receivers on the standing posts. Use 16 separate receiver units (two per post per level) and 16 male shoes across eight rails. Integrating two receivers into one corner collar is a later aesthetic option; separate units make the first fit and access checks easier.

Each female opens upward. The male dovetail slides downward in the same Z direction at both rail ends, onto a 2 mm closed receiver floor. Proposed male head is 12 mm wide, neck 8 mm; receiver face allowance starts at 0.3 mm. The sloped face normal clearance is about 0.19 mm in the nominal profile. Male neck/backplate separation leaves 0.6 mm from the female front face. Male shoes print with tongue and shoe floor on the bed; female bodies print with the closed stop down. The exact cross-holes have pointed crowns for support-aware printing. First coarse voxel versions failed the overhang gate and were replaced by exact CAD-profile meshes; those replacements passed the gate.

Use a proposed removable 4 mm cross-pin with a keeper through aligned 4.2 mm holes. This is a positive lift stop in the modeled geometry, but actual pin/keeper hardware, access and retention remain unvalidated. Do not promise tool-free operation before selecting/trying the hardware. Male shoes attach to timber using two underside fixings. Female back plates attach to upright faces with accessible fixings before the rail is inserted; adjacent face screws need staggered heights and verified penetration depths. Fastener/pilot specifications remain proposals, not workshop instructions.

**Customer assembly proposal:** supply receiver-mounted posts and shoe-mounted rails → stand/align posts → lower the front/rear/side rails into paired receivers → fit cross-pins and keepers → repeat the second frame → install upper shade/light module. The fourth rail has two parallel vertical insertion paths, so it does not require an impossible sideways closing movement. CAD must sweep the complete rail plus both shoes upward/downward by 30 mm, including the final rail and already installed neighbors. The proposed upper rail center is 50 mm below the shade: nominal rail top plus the 30 mm insertion travel remains 7.5 mm below the chamber bottom. Prove this against actual collars/tray/fasteners and repeat with tolerance/wood variation. For disassembly remove pins, lift both ends together, and lift the rail clear. Pins must be accessible from the outward side.

Two horizontal frames can limit relative movement; no validated racking, tipping or joint strength is claimed. No diagonals, shelves or outriggers are included.

## 11. B22 / E27 commercial holder support option

B22/E27 specifies bulb/socket interface, not the holder's outside mounting dimensions. The exact ready-made insulated rated holder is required before completing its mechanical support. Studio exposes a provisional holder opening, flange/height and bulb envelope. Current tray can have a parameterized opening; it is **not** a verified holder mount or printed electrical socket. Use suitable commercial electrical components; this plan gives no mains wiring construction instructions. Confirm bulb clearance, ventilation, holder retention, material heat exposure and service access using the actual hardware and translucent filament before operation.

## Current task list

- Completed: corrected clean-leg preview, 25 mm inputs, initial section artifact, centering correction, actual dovetail profile meshes and export gates, initial panel/connector slices under provisional PLA.
- Underway: two horizontal-frame preview, genuine STEP part/assembly generation and common-volume checks, live Studio parameter/part controls, revised section/assembly illustration.
- Queued/pending: actual holder reference, timber rail material/section confirmation, receiver/male wood fastening decisions, bottom shade-collar height fixation, full insertion/removal sweep, pin/keeper selection, PETG/actual shade filament slicing and physical tests.

No additional agents are active; implementation and validation are being handled in this project chat.

### Verification update

Six frame tests pass, including exact dovetail mesh/export screens, separate leg/light heights, eight horizontal rails and invalid-profile rejection. The tangent-crown cross-hole encloses the full intended round pin clearance; the earlier triangular crown was corrected before final part checks. Bambu A1 / 0.4 mm / Generic PETG reviews completed with support use false: male shoe 42m53s / 9.42 g; female receiver 39m58s / 4.41 g. These are slicer predictions and provisional PETG settings, not physical fit or locking tests.

Shade engine smoke test reports watertight=True. Existing separate base CAD still cannot run because build123d is absent; the new four-post STEP path uses the installed FreeCAD runtime instead. No new package was installed. Native FreeCAD document creation encountered an installed material-library error; genuine STEP parts/assembly use solid B-reps and include parameter JSON and regeneration source rather than claiming retained native feature history.

### Default CAD results now available

Thirteen individual solid STEP files exported and re-imported as valid B-reps with volume checks. The assembly STEP and parameter/regeneration files are in `output/revamp/standing-cad/cad-parts.zip`. Seven nominal assembly checks reported zero unwanted volume: post/collar, post/foot, panel/collar, panel/post, dovetail pair, rail/shoe and rail/post. Panel envelope checks are conservative and resolve to detailed geometry if an envelope reports a possible collision.

The local dovetail sweep sampled 0, 5, 10, 15, 20, 25 and 30 mm travel: all had zero overlap. A 4 mm cylindrical pin also had zero nominal overlap with both parts. Default upper rail/wood lift clearance is 7.5 mm; shoe lift clearance 5.5 mm; neighboring corner shoe envelope clearance 1.2 mm. These establish a useful default geometry check, not a continuous complete-scene sweep or physical locking test. Hardware/wood fastener heads, keeper, actual holder and cable routing still need inclusion. Default CAD evidence does not cover every Studio parameter combination.
