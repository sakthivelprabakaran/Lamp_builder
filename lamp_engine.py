"""
lamp_engine.py  --  Parametric lamp-shade + base geometry core for Lamp Studio.

Design philosophy (Grasshopper-style, composable operators, NOT hardcoded shapes):
a shade is ONE surface described by a radius field r(theta, z), built up from
independent operators that stack:

    form      profile R(z)          cylinder / cone / vase / flare
    lobes     * (1 + a*sin(k*t))    fluting around the circumference
    twist      phase += rate*z      turns the flutes into a spiral
    ripple    + b*sin(m*z)          horizontal waves up the height
    noise     + value-noise field   organic irregular surface (optional)

Because the operators compose (form x lobes x twist x ripple x noise), a handful
of sliders spans an effectively infinite family of continuous-wall shades.

Kernel split (see VISION.md): the continuous-wall SHADE is generated as a pure
numpy parametric mesh -- always watertight, instant, no BREP fragility -- which
is the right tool for dense/organic surfaces and gives live-preview speed. The
BASE adapter, which needs exact bores and standard fittings, is built with
build123d (imported lazily so shade generation never pays the OCP import cost).

Units: millimetres throughout.
"""

import math
import struct
import numpy as np

import graph_engine        # Phase 6 field node-graph (pure numpy, no new deps)


# --------------------------------------------------------------------------- #
#  Parameters
# --------------------------------------------------------------------------- #

SHADE_DEFAULTS = dict(
    height=180.0,          # overall height (mm)
    r_bottom=70.0,         # radius at the base
    r_top=55.0,            # radius at the top
    bulge=18.0,            # extra radius at mid-height (+ barrel / - waist)
    bulge_pos=0.5,         # 0..1 height fraction where the bulge peaks
    wall=1.2,              # wall thickness (mm) -- 0.8..1.6 prints translucent
    lobes=8,               # number of vertical flutes around (0 = smooth)
    lobe_amp=0.10,         # flute depth as a fraction of local radius
    twist_turns=0.75,      # total rotations of the flutes over full height
    ripple_waves=0.0,      # horizontal wave count up the height
    ripple_amp=0.0,        # horizontal wave depth (fraction of radius)
    noise_amp=0.0,         # organic value-noise depth (fraction of radius)
    noise_scale=6.0,       # noise frequency (cells around the circumference)
    res_theta=200,         # circumferential resolution
    res_z=180,             # vertical resolution
    seed=1,                # noise seed (integer)
    # --- perforation pattern (Phase 3): holes cut through the thick wall ---
    pattern="none",        # none | honeycomb | voronoi | gyroid | grid
    pat_cols=14,           # pattern cells around the circumference
    pat_rows=10,           # pattern cells up the height
    web=0.28,              # strut thickness (0..1 of cell spacing; bigger = less open)
    pat_seed=7,            # random seed (voronoi)
    top_solid=12.0,        # solid rim band at the very top (mm), for strength
    # --- bayonet twist-lock collar at the shade bottom (mates the base) ---
    bayonet=1,             # 1 = generate the twist-lock collar, 0 = plain open bottom
    collar_h=18.0,         # height of the straight mounting collar (mm)
    collar_wall=5.0,       # collar wall thickness (mm) -- must exceed lug_protr+fit_clr
    lug_count=3,           # number of bayonet lugs / channels
    channel_w_deg=17.0,    # angular width of each entry channel
    lock_w_deg=40.0,       # angular travel of the twist into the locking pocket
    lug_protr=2.2,         # how far a base lug sticks into the collar wall (mm)
    fit_clr=0.5,           # radial slip clearance between collar and base (mm)
    pocket_z0=7.0,         # height of the pocket floor (lower trapping ledge) (mm)
    pocket_h=5.0,          # pocket height = lug seat + play (mm)
)

BASE_DEFAULTS = dict(
    holder_type="m10",     # m10 | b22 | e27 | ikea  -- what the base mounts below
    rim_over=4.0,          # plate extends this far beyond the shade outer (mm)
    plate_thick=5.0,       # base plate thickness (mm)
    seat_wall=3.0,         # bayonet collar wall (mm)
    seat_extra=7.0         # collar rises pocket_center + this above the plate (mm)
        ,
    bore=10.5,             # centre through-bore for the cord / M10 nipple (mm)
    nut_dia=19.0,          # M10 lock-nut pocket across-corners (mm), holder_type=m10
    nut_depth=4.5,         # nut pocket depth from the underside (mm)
    holder_dia=42.0,       # seat recess diameter for b22/e27/ikea holder body (mm)
    holder_depth=6.0,      # seat recess depth (mm)
    screw_spacing=28.0,    # 2 mounting-screw pitch for b22 batten holders (mm)
    screw_dia=3.4,         # mounting-screw clearance hole (mm)
    cord_slot=5.0,         # underside cord-exit slot width (mm, 0 = none)
    lug_arc_trim=3.0,      # lug arc = channel_w - this, so it enters the channel (deg)
)


# --------------------------------------------------------------------------- #
#  Shade  (pure-numpy parametric mesh)
# --------------------------------------------------------------------------- #

def _profile_radius(zf, p):
    """Base radius R(z) as a function of height fraction zf in [0,1]."""
    r0, r1 = p["r_bottom"], p["r_top"]
    base = r0 + (r1 - r0) * zf
    # A smooth bulge/waist centred on bulge_pos (raised-cosine window).
    bp = min(max(p["bulge_pos"], 0.02), 0.98)
    # window peaks (=1) at bp, falls to 0 at the ends
    if zf <= bp:
        w = 0.5 - 0.5 * math.cos(math.pi * zf / bp)
    else:
        w = 0.5 - 0.5 * math.cos(math.pi * (1 - zf) / (1 - bp))
    return base + p["bulge"] * w


def _value_noise(theta, zf, scale, seed):
    """Cheap, seedable, periodic-in-theta value noise in roughly [-1, 1].
    Sum of a few sine harmonics with pseudo-random phases -- no dependency,
    deterministic for a given seed, and continuous across the theta seam."""
    rng = np.random.default_rng(int(seed) & 0x7FFFFFFF)
    out = np.zeros_like(theta)
    amp = 1.0
    total = 0.0
    for h in range(1, 5):
        kt = max(1, int(round(scale * h / 3.0)))          # integer -> seamless
        kz = h
        pt = rng.uniform(0, 2 * math.pi)
        pz = rng.uniform(0, 2 * math.pi)
        out += amp * np.sin(kt * theta + pt) * np.sin(kz * math.pi * zf + pz)
        total += amp
        amp *= 0.55
    return out / total


def _radius_field(theta, zf, p):
    """The full r(theta, z) field with every operator composed in."""
    R = np.array([_profile_radius(float(z), p) for z in zf[:, 0]])[:, None]
    R = np.broadcast_to(R, theta.shape).copy()

    factor = np.ones_like(theta)
    if p["lobes"] and p["lobe_amp"]:
        twist = 2.0 * math.pi * p["twist_turns"] * zf   # phase grows with height
        factor += p["lobe_amp"] * np.sin(p["lobes"] * theta + twist)
    if p["ripple_waves"] and p["ripple_amp"]:
        factor += p["ripple_amp"] * np.sin(math.pi * p["ripple_waves"] * zf)
    if p["noise_amp"]:
        factor += p["noise_amp"] * _value_noise(theta, zf, p["noise_scale"], p["seed"])
    return R * factor


# --------------------------------------------------------------------------- #
#  Operator stack (Phase 5): a shade's surface is an ordered list of operators.
#  Each operator transforms the running (theta_eff, radius) state; ORDER MATTERS
#  (twist before flute -> spiralling flutes; after -> unaffected). Multiple
#  instances of an operator are allowed (e.g. two ripples). Perforation + the
#  bayonet collar are handled separately (they are a mask / structure, not a
#  radius-field op). The flat SHADE_DEFAULTS still work via a default stack.
# --------------------------------------------------------------------------- #

# UI schema: per operator type, its param sliders (key, label, min, max, step).
OP_SCHEMA = {
    "form":   [("r_bottom", "Bottom radius", 20, 140, 1),
               ("r_top", "Top radius", 15, 140, 1),
               ("bulge", "Bulge / waist", -40, 60, 1),
               ("bulge_pos", "Bulge position", 0.05, 0.95, 0.01)],
    "twist":  [("turns", "Twist turns", -3, 3, 0.05)],
    "flute":  [("count", "Flute count", 0, 40, 1),
               ("amp", "Flute depth", 0, 0.4, 0.01)],
    "ripple": [("waves", "Ripple waves", 0, 20, 1),
               ("amp", "Ripple depth", 0, 0.3, 0.01)],
    "noise":  [("amp", "Noise depth", 0, 0.35, 0.01),
               ("scale", "Noise scale", 1, 20, 1),
               ("seed", "Noise seed", 1, 99, 1)],
}
OP_DEFAULTS = {t: {k: (min_ + max_) / 2 if k not in
               ("r_bottom", "r_top", "bulge", "count", "amp", "turns", "waves")
               else 0 for (k, _, min_, max_, _s) in specs}
               for t, specs in OP_SCHEMA.items()}

# The default stack reproduces the classic default shade (form + twist + flute).
STACK_DEFAULT = [
    {"type": "form", "on": 1, "r_bottom": 70, "r_top": 55, "bulge": 18, "bulge_pos": 0.5},
    {"type": "twist", "on": 1, "turns": 0.75},
    {"type": "flute", "on": 1, "count": 8, "amp": 0.10},
]


def _op_get(op, key, fallback=0.0):
    try:
        return float(op.get(key, fallback))
    except Exception:
        return fallback


def _form_radius_1d(zf1d, op):
    """Base profile R(z) for a form operator over a 1-D height fraction array."""
    r0, r1 = _op_get(op, "r_bottom", 70), _op_get(op, "r_top", 55)
    bulge = _op_get(op, "bulge", 0)
    bp = min(max(_op_get(op, "bulge_pos", 0.5), 0.02), 0.98)
    base = r0 + (r1 - r0) * zf1d
    w = np.where(zf1d <= bp,
                 0.5 - 0.5 * np.cos(np.pi * zf1d / bp),
                 0.5 - 0.5 * np.cos(np.pi * (1 - zf1d) / (1 - bp)))
    return base + bulge * w


def eval_stack(theta, zf, stack):
    """Evaluate the operator stack -> radius field r(theta, z). theta/zf are 2-D
    grids of the same shape. Returns (r, form_op) so the caller can reuse the form
    params for the bayonet/base coupling."""
    theta_eff = theta.copy()
    r = None
    form_op = None
    for op in stack:
        if not op.get("on", 1):
            continue
        t = op.get("type")
        if t == "form":
            form_op = op
            R1d = _form_radius_1d(zf[:, 0], op)
            r = np.broadcast_to(R1d[:, None], theta.shape).copy()
        elif r is None:
            continue                        # operators before a form have nothing to act on
        elif t == "twist":
            theta_eff = theta_eff + 2.0 * math.pi * _op_get(op, "turns") * zf
        elif t == "flute":
            c, a = _op_get(op, "count"), _op_get(op, "amp")
            if c and a:
                r = r * (1 + a * np.sin(c * theta_eff))
        elif t == "ripple":
            wv, a = _op_get(op, "waves"), _op_get(op, "amp")
            if wv and a:
                r = r * (1 + a * np.sin(math.pi * wv * zf))
        elif t == "noise":
            a = _op_get(op, "amp")
            if a:
                r = r * (1 + a * _value_noise(theta_eff, zf,
                                              _op_get(op, "scale", 6), _op_get(op, "seed", 1)))
    if r is None:                            # no form op -> fall back to a plain cylinder
        r = np.broadcast_to(np.full(zf[:, 0].shape, 60.0)[:, None], theta.shape).copy()
        form_op = {"type": "form", "r_bottom": 60, "r_top": 60, "bulge": 0, "bulge_pos": 0.5}
    return r, form_op


def _default_stack_from_flat(p):
    """Build an operator stack from the legacy flat SHADE params so old presets
    and any flat-param callers keep working unchanged."""
    return [
        {"type": "form", "on": 1, "r_bottom": p["r_bottom"], "r_top": p["r_top"],
         "bulge": p["bulge"], "bulge_pos": p["bulge_pos"]},
        {"type": "twist", "on": 1, "turns": p["twist_turns"]},
        {"type": "flute", "on": 1 if p["lobes"] and p["lobe_amp"] else 0,
         "count": p["lobes"], "amp": p["lobe_amp"]},
        {"type": "ripple", "on": 1 if p["ripple_waves"] and p["ripple_amp"] else 0,
         "waves": p["ripple_waves"], "amp": p["ripple_amp"]},
        {"type": "noise", "on": 1 if p["noise_amp"] else 0,
         "amp": p["noise_amp"], "scale": p["noise_scale"], "seed": p["seed"]},
    ]


def bayonet_geometry(p):
    """Derived bayonet dimensions shared by the shade collar and the base lugs.
    Returns a dict so build_base can machine matching lugs."""
    mount_r = p["r_bottom"] - p["collar_wall"]          # collar inner (wall) radius
    channel_r = mount_r + p["lug_protr"] + p["fit_clr"]  # recessed radius a lug clears
    return {
        "mount_r": mount_r,
        "channel_r": channel_r,
        "base_collar_r": mount_r - p["fit_clr"],         # base collar outer radius
        "lug_tip_r": mount_r - p["fit_clr"] + p["lug_protr"],
        "pocket_center": p["pocket_z0"] + p["pocket_h"] / 2.0,
        "lug_count": int(p["lug_count"]),
        "channel_w_deg": p["channel_w_deg"],
    }


def _bayonet_inner(theta, z, p, mount_r, channel_r):
    """Inner-wall radius field for the collar band: entry channels (full height)
    plus locking pockets with a chamfered (printable) upper ledge."""
    n = max(1, int(p["lug_count"]))
    period = 2.0 * math.pi / n
    cw = math.radians(p["channel_w_deg"])
    lw = math.radians(p["lock_w_deg"])
    pz0, ph = p["pocket_z0"], p["pocket_h"]
    cham = 1.8                                  # 45deg-ish ledge chamfer height

    a = np.mod(theta, period)                   # local angle within one lug period
    r = np.full(theta.shape, mount_r)

    # Entry channel is CENTRED on a=0 so it aligns with a base lug at 0/120/240.
    in_channel = (a <= cw / 2.0) | (a >= period - cw / 2.0)
    r[in_channel] = channel_r                   # entry channel, open full height

    # Locking pocket runs from the channel edge through the twist travel (+side).
    ang_pocket = (a > cw / 2.0) & (a <= cw / 2.0 + lw)
    in_pocket = ang_pocket & (z >= pz0) & (z <= pz0 + ph)
    r[in_pocket] = channel_r                    # the trap the lug twists into

    # Chamfer the downward-facing ledge above the pocket so it prints support-free.
    top = ang_pocket & (z > pz0 + ph) & (z <= pz0 + ph + cham)
    t = (z - (pz0 + ph)) / cham
    r[top] = channel_r + (mount_r - channel_r) * t[top]
    return r


def _perforation_solid(u, v, p):
    """Boolean 'material' mask over cell centres (True = keep wall, False = hole).
    u in [0,1) around the circumference (periodic), v in [0,1] over the perforated
    band. Honeycomb/voronoi share a 'distance-to-nearest-cell web' method; a
    triangular lattice of centres yields true hexagons, random centres yield an
    organic voronoi web."""
    pat = str(p["pattern"]).lower()
    cols = max(2, int(p["pat_cols"]))
    rows = max(2, int(p["pat_rows"]))
    web = float(p["web"])

    if pat == "grid":
        fu = np.abs(((u * cols) % 1.0) - 0.5) * 2.0     # 0 centre -> 1 edge
        fv = np.abs(((v * rows) % 1.0) - 0.5) * 2.0
        return (fu > 1.0 - web) | (fv > 1.0 - web)

    if pat == "gyroid":
        a = 2.0 * math.pi * cols
        b = 2.0 * math.pi * rows
        g = (np.sin(a * u) * np.cos(b * v)
             + np.sin(b * v) * np.cos(a * u + math.pi * v))
        return np.abs(g) < (web * 2.0)                  # struts where |g| small

    # Distance-to-nearest-centre family:
    #   honeycomb -> hexagonal web (triangular lattice, near cell boundary)
    #   voronoi   -> organic web (random centres, near cell boundary)
    #   dots      -> round holes punched on a hex-packed lattice (solid elsewhere)
    asp = float(cols)                                   # scale u to ~cols cells wide
    pts = np.stack([(u * asp), v * rows], axis=-1).reshape(-1, 2)  # (M,2)

    if pat == "voronoi":
        rng = np.random.default_rng(int(p["pat_seed"]) & 0x7FFFFFFF)
        n = max(6, int(cols * rows * 0.5))
        cu = rng.uniform(0, asp, n); cv = rng.uniform(0, rows, n)
    else:  # honeycomb / dots -> triangular (hex-packed) lattice of centres
        jj, ii = np.meshgrid(np.arange(-1, cols + 1), np.arange(-1, rows + 2))
        cu = jj.ravel() + 0.5 * (ii.ravel() % 2)
        cv = ii.ravel() * (math.sqrt(3) / 2.0)
        keep = (cv >= -1) & (cv <= rows + 1)
        cu, cv = cu[keep], cv[keep]

    # Replicate centres across the u-seam so the pattern wraps seamlessly.
    cu = np.concatenate([cu - asp, cu, cu + asp])
    cv = np.concatenate([cv, cv, cv])
    centres = np.stack([cu, cv], axis=-1)               # (N,2)

    need_d2 = pat != "dots"                             # dots only needs nearest
    d1 = np.full(len(pts), 1e9); d2 = np.full(len(pts), 1e9)
    step = 4096
    for s in range(0, len(pts), step):
        chunk = pts[s:s + step]
        dd = np.sqrt(((chunk[:, None, :] - centres[None, :, :]) ** 2).sum(-1))
        if need_d2:
            part = np.partition(dd, 1, axis=1)
            d1[s:s + step] = part[:, 0]; d2[s:s + step] = part[:, 1]
        else:
            d1[s:s + step] = dd.min(axis=1)

    if pat == "dots":
        solid = d1 > web                                # hole within `web` of a centre
    else:
        solid = (d2 - d1) < web                         # web near a cell boundary
    return solid.reshape(u.shape)


def _declink(solid, passes=4):
    """Remove diagonal-only (checkerboard) touches from the solid mask. A corner
    where two solid cells meet only diagonally makes the shared vertical rim edge
    belong to four faces (non-manifold) and is an unprintable razor pinch; filling
    one orthogonal neighbour makes the material 4-connected and manifold."""
    m = solid.copy()
    nt = m.shape[1]
    for _ in range(passes):
        a = m[:-1, :]; c = m[1:, :]
        b = np.roll(m, -1, axis=1)[:-1, :]
        d = np.roll(m, -1, axis=1)[1:, :]
        t1 = a & d & ~b & ~c        # solid on the (i,j)-(i+1,j+1) diagonal -> fill b
        t2 = b & c & ~a & ~d        # solid on the (i,j+1)-(i+1,j) diagonal -> fill a
        if not (t1.any() or t2.any()):
            break
        bi, bj = np.nonzero(t1); m[bi, (bj + 1) % nt] = True
        ai, aj = np.nonzero(t2); m[ai, aj] = True
    return m


def _form_params(shade_params):
    """The effective profile keys (r_bottom/r_top/bulge/bulge_pos) whatever drives
    the shape -- a Phase-6 graph `form` node, a Phase-5 stack `form` op, or flat
    params. Single source of truth so the SHADE and the BASE couple to the same
    numbers (otherwise the base is built for the flat default while the shade uses
    the graph/stack form -> the twist-lock never mates)."""
    shade_params = shade_params or {}
    graph = shade_params.get("graph")
    if graph:
        fnode = next((n for n in graph.get("nodes", []) if n.get("type") == "form"), None)
        src = (fnode or {}).get("params") or {}
    else:
        stack = shade_params.get("stack")
        src = (next((o for o in stack if o.get("type") == "form"), None) or {}) if stack \
            else shade_params
    out = {}
    for k in ("r_bottom", "r_top", "bulge", "bulge_pos"):
        if k in src:
            try:
                out[k] = float(src[k])
            except (TypeError, ValueError):
                pass
    return out


def build_shade_mesh(params):
    """Return (verts Nx3 float32, faces Mx3 int32) for a watertight thin-wall shade."""
    p = dict(SHADE_DEFAULTS); p.update({k: params[k] for k in params if k in SHADE_DEFAULTS})
    # Surface shape comes from EITHER a field node-graph (Phase 6) or the operator
    # stack (Phase 5); either way synthesise a fallback so legacy callers render.
    graph = params.get("graph")
    stack = None if graph else (params.get("stack") or _default_stack_from_flat(p))
    p.update(_form_params(params))           # couple bayonet/base to the active form
    nt = max(24, int(p["res_theta"]))
    nz = max(4, int(p["res_z"]))
    H = float(p["height"])
    wall = max(0.4, float(p["wall"]))

    bayo = bool(p["bayonet"]) and p["collar_h"] > 0 and p["collar_wall"] > 0
    collar_h = float(p["collar_h"]) if bayo else 0.0

    # Grid. theta has nt distinct columns (seam handled by wrap in indexing, so
    # we do NOT duplicate the last column). z rows span 0..H, with extra density
    # inside the collar band so the bayonet ledges/pockets resolve cleanly.
    theta1d = np.linspace(0.0, 2.0 * math.pi, nt, endpoint=False)
    if bayo:
        zc = collar_h / H
        z_collar = np.linspace(0.0, zc, max(30, int(nz * zc) + 24), endpoint=False)
        z_body = np.linspace(zc, 1.0, nz)
        zf1d = np.unique(np.concatenate([z_collar, z_body]))
    else:
        zf1d = np.linspace(0.0, 1.0, nz)
    nz = len(zf1d)
    theta = np.broadcast_to(theta1d[None, :], (nz, nt)).copy()
    zf = np.broadcast_to(zf1d[:, None], (nz, nt)).copy()
    z = zf * H

    if graph:
        r_out = graph_engine.evaluate(graph, theta, zf, zf1d,
                                      need_holes=False)["radius"].astype(float).copy()
        # A graph can drive radius below the wall (e.g. a 0..1 pattern wired straight
        # into radius) -> the inner wall crosses outside the outer = inverted,
        # self-intersecting shell that still reports "watertight". Floor it.
        r_out = np.maximum(r_out, wall + 0.8)
    else:
        r_out, _ = eval_stack(theta, zf, stack)
    r_in = np.maximum(r_out - wall, 0.5)     # keep inner radius positive

    if bayo:
        # Collar: straight outer cylinder + bayonet inner field. The decorative
        # surface fades in over a short blend just above the collar.
        g = bayonet_geometry(p)
        collar = z < collar_h
        r_out[collar] = p["r_bottom"]
        r_in[collar] = _bayonet_inner(theta[collar], z[collar], p,
                                      g["mount_r"], g["channel_r"])
        blend = 12.0
        w = np.clip((z - collar_h) / blend, 0.0, 1.0)
        prof = np.array([_profile_radius(float(zz), p) for zz in zf1d])[:, None]
        r_out = np.where(collar, r_out, prof + (r_out - prof) * w)
        r_in = np.where(collar, r_in, np.maximum(r_out - wall, 0.5))

    cos_t, sin_t = np.cos(theta), np.sin(theta)

    def ring(r):
        return np.stack([r * cos_t, r * sin_t, z], axis=-1)  # (nz, nt, 3)

    OUT = ring(r_out)
    IN = ring(r_in)

    verts = np.concatenate([OUT.reshape(-1, 3), IN.reshape(-1, 3)], axis=0)
    n_surf = nz * nt          # verts per surface

    def gi(surf, i, j):       # vectorized global index; j wraps around theta
        return surf * n_surf + i * nt + (j % nt)

    ii, jj = np.meshgrid(np.arange(nz - 1), np.arange(nt), indexing="ij")
    ii = ii.ravel(); jj = jj.ravel()

    # --- solid/hole mask over cells (nz-1, nt). All-solid unless a pattern is on ---
    # Graph mode: sample the graph's `holes` output at cell centres (matching how
    # _perforation_solid samples), on the TRUE height fraction so patterns line up
    # with the visible surface. Stack mode: the Phase-3 perforation patterns.
    graph_holes = None
    top_solid = float(p["top_solid"])
    if graph and graph_engine.output_wants(graph, "holes"):    # only if `holes` is wired
        zc = (z[:-1, 0] + z[1:, 0]) / 2.0
        zf_c = zc / H
        th_c = 2.0 * math.pi * (np.arange(nt) + 0.5) / nt
        TH = np.broadcast_to(th_c[None, :], (nz - 1, nt)).copy()
        ZF = np.broadcast_to(zf_c[:, None], (nz - 1, nt)).copy()
        graph_holes = graph_engine.evaluate(graph, TH, ZF, zf_c, need_radius=False)["holes"]
        top_solid = graph_engine.output_param(graph, "top_solid", top_solid)  # graph owns it
    pat_on = (graph_holes is not None) if graph else (str(p["pattern"]).lower() != "none")
    solid = np.ones((nz - 1, nt), dtype=bool)
    if pat_on:
        zc = (z[:-1, 0] + z[1:, 0]) / 2.0                       # cell-centre heights
        z_lo = collar_h + 2.0
        z_hi = H - top_solid
        if z_hi <= z_lo + 5.0:
            z_hi = z_lo + 5.0
        band = (zc >= z_lo) & (zc <= z_hi)                      # (nz-1,)
        if graph:
            keep = ~graph_holes                                 # solid where NOT a hole
        else:
            ucol = ((np.arange(nt) + 0.5) / nt)[None, :]
            ugrid = np.broadcast_to(ucol, (nz - 1, nt))
            vgrid = np.clip((zc[:, None] - z_lo) / (z_hi - z_lo), 0.0, 1.0)
            vgrid = np.broadcast_to(vgrid, (nz - 1, nt))
            keep = _perforation_solid(ugrid, vgrid, p)
        solid = np.where(band[:, None], keep, True)
        # The bottom/top cap rings are emitted for every column, and _hole_rims
        # treats off-grid row neighbours as solid, so a hole in the first or last
        # cell row would be left unsealed (boundary + non-manifold edges). Keep
        # those two rows solid; _declink only ever fills, so it can't undo this.
        solid[0, :] = True
        solid[-1, :] = True
        solid = _declink(solid)          # kill diagonal pinches -> manifold + printable

    def quads_all(surf, flip):
        a = gi(surf, ii, jj);      b = gi(surf, ii, jj + 1)
        c = gi(surf, ii + 1, jj);  d = gi(surf, ii + 1, jj + 1)
        if not flip:
            return np.stack([np.stack([a, b, d], 1), np.stack([a, d, c], 1)])
        return np.stack([np.stack([a, d, b], 1), np.stack([a, c, d], 1)])

    if not pat_on:
        side_out = quads_all(0, flip=False).reshape(-1, 3)
        side_in = quads_all(1, flip=True).reshape(-1, 3)
        rims = np.empty((0, 3), np.int64)
    else:
        si, sj = np.nonzero(solid)
        O00 = gi(0, si, sj); O01 = gi(0, si, sj + 1)
        O11 = gi(0, si + 1, sj + 1); O10 = gi(0, si + 1, sj)
        side_out = np.concatenate([np.stack([O00, O01, O11], 1),
                                   np.stack([O00, O11, O10], 1)])
        I00 = gi(1, si, sj); I01 = gi(1, si, sj + 1)
        I11 = gi(1, si + 1, sj + 1); I10 = gi(1, si + 1, sj)
        side_in = np.concatenate([np.stack([I00, I11, I01], 1),
                                  np.stack([I00, I10, I11], 1)])
        rims = _hole_rims(solid, gi)

    # Bottom + top rings join outer<->inner (opposite windings at the two ends).
    j = np.arange(nt)
    ob, ob1 = gi(0, 0, j), gi(0, 0, j + 1)
    ib, ib1 = gi(1, 0, j), gi(1, 0, j + 1)
    bot = np.concatenate([np.stack([ob, ib, ib1], 1), np.stack([ob, ib1, ob1], 1)])
    ot, ot1 = gi(0, nz - 1, j), gi(0, nz - 1, j + 1)
    it, it1 = gi(1, nz - 1, j), gi(1, nz - 1, j + 1)
    top = np.concatenate([np.stack([ot, it1, it], 1), np.stack([ot, ot1, it1], 1)])

    faces = np.concatenate([side_out, side_in, rims, bot, top], axis=0)
    return verts.astype(np.float32), faces.astype(np.int32)


def _hole_rims(solid, gi):
    """Rim walls that seal every hole boundary, connecting the outer wall to the
    inner wall so the perforated shell stays a closed manifold. A rim is emitted
    from each solid cell along any edge whose neighbour cell is a hole (cells off
    the grid top/bottom count as solid, so only real hole edges get a rim)."""
    nzc, nt = solid.shape

    def rows_shift(m, d):                       # neighbour in +d row dir; off-grid=solid
        out = np.ones_like(m)
        if d > 0:
            out[:-d] = m[d:]
        elif d < 0:
            out[-d:] = m[:d]
        else:
            out = m.copy()
        return out

    tris = []

    def add(mask, oa, ob):
        """oa, ob: (surf,di,dj) picking the two grid corners of the shared edge."""
        ri, rj = np.nonzero(mask)
        A = gi(0, ri + oa[0], rj + oa[1]); B = gi(0, ri + ob[0], rj + ob[1])
        C = gi(1, ri + ob[0], rj + ob[1]); D = gi(1, ri + oa[0], rj + oa[1])
        tris.append(np.stack([A, B, C], 1)); tris.append(np.stack([A, C, D], 1))

    # Corner order per family is chosen so every rim normal points INTO the hole
    # (outward from the material). Getting it backwards still yields a closed
    # mesh -- verify_mesh counts undirected edges -- but slicers see inverted
    # facets, so the two theta-facing families must be wound as below.
    right = solid & ~np.roll(solid, -1, axis=1)
    add(right, (1, 1), (0, 1))
    left = solid & ~np.roll(solid, 1, axis=1)
    add(left, (0, 0), (1, 0))
    topn = solid & ~rows_shift(solid, 1)
    add(topn, (1, 0), (1, 1))
    botn = solid & ~rows_shift(solid, -1)
    add(botn, (0, 1), (0, 0))

    return np.concatenate(tris, axis=0) if tris else np.empty((0, 3), np.int64)


# --------------------------------------------------------------------------- #
#  Mesh utilities: STL export + watertight verify gate
# --------------------------------------------------------------------------- #

def write_binary_stl(path, verts, faces):
    """Write a binary STL with per-facet normals computed from the winding."""
    tris = verts[faces].astype(np.float32)    # (M, 3, 3)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 1e-12).astype(np.float32)
    dt = np.dtype([("n", "<3f4"), ("v0", "<3f4"), ("v1", "<3f4"),
                   ("v2", "<3f4"), ("attr", "<u2")])
    rec = np.zeros(len(faces), dtype=dt)
    rec["n"] = n
    rec["v0"] = tris[:, 0]; rec["v1"] = tris[:, 1]; rec["v2"] = tris[:, 2]
    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(faces)))
        f.write(rec.tobytes())


def verify_mesh(verts, faces):
    """Watertight/manifold sanity gate. Returns (ok, report dict)."""
    f = np.asarray(faces, dtype=np.int64)
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]], axis=0)
    lo = np.minimum(e[:, 0], e[:, 1]); hi = np.maximum(e[:, 0], e[:, 1])
    key = lo * (int(len(verts)) + 1) + hi          # unique 1-D edge key
    _, counts = np.unique(key, return_counts=True)
    boundary = int(np.count_nonzero(counts == 1))
    nonmanifold = int(np.count_nonzero(counts > 2))
    V, E, F = len(verts), len(counts), len(faces)
    euler = V - E + F
    components = _count_components(f, V)
    ok = boundary == 0 and nonmanifold == 0 and components == 1
    return ok, {
        "verts": V, "edges": E, "tris": F, "euler": euler,
        "boundary_edges": boundary, "nonmanifold_edges": nonmanifold,
        "components": components, "watertight": boundary == 0 and nonmanifold == 0,
        "single_piece": components == 1,
    }


def _count_components(faces, nverts):
    """Number of connected pieces (union-find over vertices sharing a triangle).
    A watertight mesh can still be several DISCONNECTED closed shells -- e.g. a
    hole pattern that severs the wall into floating islands -- which prints as
    loose confetti. Only 1 component is a real single printable part."""
    if len(faces) == 0:
        return 0
    parent = np.arange(nverts, dtype=np.int64)

    def find(a):
        root = a
        while parent[root] != root:
            root = parent[root]
        while parent[a] != root:            # path-compress
            parent[a], a = root, parent[a]
        return root

    for tri in faces:
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        ra, rb, rc = find(a), find(b), find(c)
        if rb != ra:
            parent[rb] = ra
        if rc != ra:
            parent[rc] = ra
    used = np.unique(faces.reshape(-1))
    roots = {find(int(x)) for x in used}
    return len(roots)


def min_wall_ok(params):
    """Guardrail: warn if the wall is below a printable/translucent range."""
    w = float(params.get("wall", SHADE_DEFAULTS["wall"]))
    return w >= 0.8, w


# --------------------------------------------------------------------------- #
#  Base adapter  (build123d BREP -- imported lazily)
# --------------------------------------------------------------------------- #

def _base_dims(params, shade_params):
    """Resolve every base dimension, coupling the collar + lugs to the shade's
    bayonet so the two parts actually mate."""
    b = dict(BASE_DEFAULTS); b.update({k: params[k] for k in params if k in BASE_DEFAULTS})
    sp = dict(SHADE_DEFAULTS); sp.update(shade_params or {})
    sp.update(_form_params(shade_params or {}))    # resolve graph/stack form -> mate the parts
    g = bayonet_geometry(sp)
    d = dict(b)
    d["collar_r"] = g["base_collar_r"]                 # collar outer radius
    d["lug_tip_r"] = g["lug_tip_r"]
    d["lug_z"] = b["plate_thick"] + g["pocket_center"] # lug height above the plate
    d["seat_h"] = g["pocket_center"] + b["seat_extra"]
    d["lug_count"] = g["lug_count"]
    d["lug_arc_deg"] = max(4.0, g["channel_w_deg"] - b["lug_arc_trim"])
    d["plate_r"] = sp["r_bottom"] + b["rim_over"]      # shade outer + overhang
    d["pocket_h"] = sp["pocket_h"]
    return d, g


def build_base(params, shade_params=None):
    """Build the lamp-holder base as a build123d Solid: a plate the shade rests
    on, a hollow bayonet collar with matching lugs, a parametric holder mount
    (m10 / b22 / e27 / ikea), a centre cord bore, and an underside cord slot."""
    import math as _m
    from build123d import (
        BuildPart, BuildSketch, Circle, Rectangle, RegularPolygon, Locations,
        PolarLocations, extrude, Mode, Plane,
    )
    d, g = _base_dims(params, shade_params)
    plate_t, collar_r, seat_wall = d["plate_thick"], d["collar_r"], d["seat_wall"]
    seat_h, bore_r = d["seat_h"], d["bore"] / 2.0
    lug_h = max(2.0, d["pocket_h"] - 1.4)
    ctr_r = (collar_r - 1.0 + d["lug_tip_r"]) / 2.0          # lug box centre radius
    radial_len = d["lug_tip_r"] - (collar_r - 1.0)
    arc_len = 2.0 * ctr_r * _m.sin(_m.radians(d["lug_arc_deg"]) / 2.0)

    with BuildPart() as part:
        with BuildSketch():
            Circle(d["plate_r"])
        extrude(amount=plate_t)
        # Hollow bayonet collar.
        with BuildSketch(Plane.XY.offset(plate_t)):
            Circle(collar_r)
            Circle(collar_r - seat_wall, mode=Mode.SUBTRACT)
        extrude(amount=seat_h)
        # Three (or lug_count) bayonet lugs on the collar's outer wall.
        with BuildSketch(Plane.XY.offset(d["lug_z"] - lug_h / 2.0)):
            with PolarLocations(ctr_r, d["lug_count"]):
                Rectangle(radial_len, arc_len)
        extrude(amount=lug_h)
        # Centre bore all the way through.
        with BuildSketch():
            Circle(bore_r)
        extrude(amount=plate_t + seat_h, mode=Mode.SUBTRACT)
        # Holder mount on the plate.
        _cut_holder_mount(part, d, BuildSketch, Circle, RegularPolygon, Rectangle,
                          Locations, PolarLocations, extrude, Mode, Plane)
        # Underside cord-exit slot from the bore to the rim.
        if d["cord_slot"] > 0:
            with BuildSketch(Plane.XY):
                with Locations((d["plate_r"] / 2.0, 0)):
                    Rectangle(d["plate_r"], d["cord_slot"])
            extrude(amount=min(2.5, plate_t - 1.5), mode=Mode.SUBTRACT)

    return part.part


def _cut_holder_mount(part, d, BuildSketch, Circle, RegularPolygon, Rectangle,
                      Locations, PolarLocations, extrude, Mode, Plane):
    """Holder-specific features. m10: nut pocket underside. b22: seat recess +
    2 screw holes. e27/ikea: seat recess to locate the holder body."""
    # NB: extrude() must be given the sketch explicitly (to_extrude=) -- the
    # implicit "pending sketch" of the active BuildPart is not picked up across
    # this nested function call.
    ht = str(d.get("holder_type", "m10")).lower()
    plate_t = d["plate_thick"]
    if ht == "m10":
        # Across-corners hexagonal lock-nut pocket cut up from the underside.
        with BuildSketch(Plane.XY) as sk:
            RegularPolygon(radius=d["nut_dia"] / 2.0, side_count=6)
        extrude(to_extrude=sk.sketch, amount=d["nut_depth"], mode=Mode.SUBTRACT)
        return
    # b22 / e27 / ikea: recess the holder body into the plate top.
    with BuildSketch(Plane.XY.offset(plate_t)) as sk:
        Circle(d["holder_dia"] / 2.0)
    extrude(to_extrude=sk.sketch, amount=-min(d["holder_depth"], plate_t - 1.0),
            mode=Mode.SUBTRACT)
    if ht == "b22":
        with BuildSketch(Plane.XY) as sk:
            with Locations((d["screw_spacing"] / 2.0, 0), (-d["screw_spacing"] / 2.0, 0)):
                Circle(d["screw_dia"] / 2.0)
        extrude(to_extrude=sk.sketch, amount=plate_t, mode=Mode.SUBTRACT)


def build_testfit_ring(params, shade_params=None):
    """A short disc carrying only the holder mount -- a ~10-minute print to check
    that a real, purchased holder fits before committing a full base."""
    from build123d import BuildPart, BuildSketch, Circle, extrude, Mode, Plane
    d, _ = _base_dims(params, shade_params)
    h = d["plate_thick"] + (0 if str(d["holder_type"]).lower() == "m10" else d["holder_depth"]) + 3.0
    r = (d["holder_dia"] / 2.0 + 5.0) if str(d["holder_type"]).lower() != "m10" \
        else (d["nut_dia"] / 2.0 + 5.0)
    dd = dict(d); dd["plate_thick"] = h; dd["plate_r"] = r
    from build123d import (RegularPolygon, Rectangle, Locations, PolarLocations)
    with BuildPart() as part:
        with BuildSketch():
            Circle(r)
        extrude(amount=h)
        with BuildSketch():
            Circle(dd["bore"] / 2.0)
        extrude(amount=h, mode=Mode.SUBTRACT)
        _cut_holder_mount(part, dd, BuildSketch, Circle, RegularPolygon, Rectangle,
                          Locations, PolarLocations, extrude, Mode, Plane)
    return part.part


# --------------------------------------------------------------------------- #
#  CLI smoke test:  python lamp_engine.py
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import os, sys, time
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out, exist_ok=True)

    t0 = time.time()
    v, f = build_shade_mesh(SHADE_DEFAULTS)
    ok, rep = verify_mesh(v, f)
    write_binary_stl(os.path.join(out, "shade_test.stl"), v, f)
    print("shade:  %d tris in %.2fs  watertight=%s  %s"
          % (len(f), time.time() - t0, ok, rep))
    if not ok:
        print("!! shade mesh is NOT watertight", file=sys.stderr); sys.exit(1)

    if "--base" in sys.argv:
        t1 = time.time()
        try:
            from build123d import export_stl
            base = build_base(BASE_DEFAULTS, SHADE_DEFAULTS)
            export_stl(base, os.path.join(out, "base_test.stl"))
            print("base:   built + exported in %.2fs  volume=%.0f mm^3"
                  % (time.time() - t1, base.volume))
        except Exception as e:
            print("base FAILED:", e, file=sys.stderr); sys.exit(2)
    print("OK")
