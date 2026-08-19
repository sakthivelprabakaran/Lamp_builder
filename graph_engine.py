"""
graph_engine.py  --  Field node-graph evaluator for Lamp Studio (Phase 6).

A Grasshopper-style *field* graph. Every wire carries a scalar FIELD sampled over
the shade's parametric surface -- a numpy array of shape (nz, nt) where the column
axis is theta (0..2pi, periodic) and the row axis is height fraction zf (0..1).

Two conventions:
  * PATTERN fields are normalised to roughly [0, 1] (so mix / threshold / warp all
    behave predictably).
  * The `form` generator and the `displace` terminal work in MILLIMETRES: `form`
    emits a base radius field R(z); `displace` perturbs it with a pattern field.

The graph has exactly one `output` node with two input ports:
  * radius  (mm field, required) -> the shade wall radius r(theta, z)
  * holes   ([0,1] field, optional) -> thresholded into the perforation mask

The evaluator is pure numpy (no new deps) and is handed the mesher's actual grid,
so it works on the mesher's non-uniform z rows (the collar densifies them). Domain
warps resample fields with a periodic-in-theta bilinear sampler that inverts the
row spacing via zf1d, so twist/warp/kaleido stay correct on the real grid.

Graph JSON shape (from the UI):
    {
      "nodes": [{"id": "n1", "type": "noise", "params": {...}}, ...],
      "edges": [{"from": "n1", "to": "n3", "toPort": "a"}, ...],   # fromPort optional
    }
The single node of type "output" is the sink.
"""

import math
import numpy as np


# --------------------------------------------------------------------------- #
#  Node registry
# --------------------------------------------------------------------------- #
# Each entry:  inputs  -> list of input port names (fields)
#              params  -> [(key, label, min, max, step, default), ...] for the UI
#              missing -> default fill for an unconnected input port (0.0 or 1.0)
#              fn      -> (ins: dict[str, ndarray], p: dict, ctx: Ctx) -> ndarray
#
# ctx carries the sampling grid so generators are exact and warps can resample:
#   ctx.u   (nz,nt) theta/2pi in [0,1)      ctx.v  (nz,nt) height fraction zf
#   ctx.theta (nz,nt)  ctx.zf (nz,nt)  ctx.zf1d (nz,) rows  ctx.nt  ctx.nz
REGISTRY = {}


class Ctx:
    def __init__(self, theta, zf, zf1d):
        self.theta = theta
        self.zf = zf
        self.zf1d = np.asarray(zf1d, dtype=float)
        self.u = theta / (2.0 * math.pi)
        self.v = zf
        self.nz, self.nt = theta.shape
        # Column origin as a fraction of a cell: 0 for the vertex grid (columns at
        # j/nt), 0.5 for the cell-centre grid (columns at (j+0.5)/nt). The warp
        # sampler needs this so a warped field lines up with the surface it modifies
        # instead of sitting half a cell off.
        self.col_off = float(self.u.flat[0] * self.nt) if self.nt else 0.0


def _reg(kind, inputs, params, missing=None, category="", label=None):
    missing = missing or {}

    def deco(fn):
        REGISTRY[kind] = {
            "kind": kind, "label": label or kind, "category": category,
            "inputs": inputs, "params": params, "missing": missing, "fn": fn,
        }
        return fn
    return deco


def _p(p, key, default):
    try:
        return float(p.get(key, default))
    except Exception:
        return default


def _field(ctx, value):
    """Broadcast a scalar to a full field."""
    return np.full((ctx.nz, ctx.nt), float(value))


def _norm01(a):
    """Clamp a field to [0, 1] (patterns should stay in range before combining)."""
    return np.clip(a, 0.0, 1.0)


# ----- periodic bilinear sampler (used by all domain-warp nodes) ----------- #
def sample(field, u_new, v_new, ctx):
    """Resample `field` at continuous surface coords (u_new in [0,1) periodic,
    v_new in [0,1]). Theta columns are uniform; z rows follow ctx.zf1d, so the
    row index is recovered by interpolating against zf1d (handles the collar's
    non-uniform rows)."""
    nz, nt = ctx.nz, ctx.nt
    uu = np.mod(u_new, 1.0) * nt - ctx.col_off   # account for the grid's column origin
    c0 = np.floor(uu).astype(np.intp)
    cf = uu - c0
    c0m = c0 % nt
    c1m = (c0 + 1) % nt

    rows = np.interp(np.clip(v_new, 0.0, 1.0).ravel(), ctx.zf1d,
                     np.arange(nz, dtype=float)).reshape(v_new.shape)
    r0 = np.floor(rows).astype(np.intp)
    rf = rows - r0
    r0 = np.clip(r0, 0, nz - 1)
    r1 = np.clip(r0 + 1, 0, nz - 1)

    f00 = field[r0, c0m]; f01 = field[r0, c1m]
    f10 = field[r1, c0m]; f11 = field[r1, c1m]
    top = f00 * (1 - cf) + f01 * cf
    bot = f10 * (1 - cf) + f11 * cf
    return top * (1 - rf) + bot * rf


# --------------------------------------------------------------------------- #
#  Generators  (no field inputs)
# --------------------------------------------------------------------------- #

@_reg("form", [], [("r_bottom", "Bottom radius", 20, 140, 1, 70),
                   ("r_top", "Top radius", 15, 140, 1, 55),
                   ("bulge", "Bulge / waist", -40, 60, 1, 18),
                   ("bulge_pos", "Bulge position", 0.05, 0.95, 0.01, 0.5)],
      category="generator", label="Form (mm)")
def _n_form(ins, p, ctx):
    r0, r1 = _p(p, "r_bottom", 70), _p(p, "r_top", 55)
    bulge = _p(p, "bulge", 18)
    bp = min(max(_p(p, "bulge_pos", 0.5), 0.02), 0.98)
    v = ctx.v
    base = r0 + (r1 - r0) * v
    w = np.where(v <= bp,
                 0.5 - 0.5 * np.cos(np.pi * v / bp),
                 0.5 - 0.5 * np.cos(np.pi * (1 - v) / (1 - bp)))
    return base + bulge * w


@_reg("gradZ", [], [], category="generator", label="Gradient Z")
def _n_gradz(ins, p, ctx):
    return ctx.v.copy()


@_reg("gradTheta", [], [], category="generator", label="Gradient θ")
def _n_gradt(ins, p, ctx):
    return ctx.u.copy()


@_reg("const", [], [("value", "Value", 0, 1, 0.01, 0.5)],
      category="generator", label="Constant")
def _n_const(ins, p, ctx):
    return _field(ctx, _p(p, "value", 0.5))


@_reg("sine", [], [("axis", "Axis (0=θ 1=z)", 0, 1, 1, 0),
                   ("freq", "Frequency", 0, 40, 0.5, 8),
                   ("phase", "Phase", 0, 1, 0.01, 0)],
      category="generator", label="Sine wave")
def _n_sine(ins, p, ctx):
    axis = int(round(_p(p, "axis", 0)))
    f = _p(p, "freq", 8); ph = _p(p, "phase", 0) * 2 * math.pi
    coord = ctx.theta if axis == 0 else (ctx.v * 2 * math.pi)
    return 0.5 + 0.5 * np.sin(f * coord + ph)


@_reg("noise", [], [("scale", "Scale", 1, 24, 1, 6),
                    ("octaves", "Octaves", 1, 5, 1, 4),
                    ("seed", "Seed", 1, 99, 1, 1)],
      category="generator", label="Value noise")
def _n_noise(ins, p, ctx):
    scale = _p(p, "scale", 6); seed = int(_p(p, "seed", 1))
    oct_ = int(round(_p(p, "octaves", 4)))
    rng = np.random.default_rng(seed & 0x7FFFFFFF)
    out = np.zeros((ctx.nz, ctx.nt)); amp = 1.0; total = 0.0
    for h in range(1, oct_ + 1):
        kt = max(1, int(round(scale * h / 3.0)))     # integer -> seamless in theta
        pt = rng.uniform(0, 2 * math.pi); pz = rng.uniform(0, 2 * math.pi)
        out += amp * np.sin(kt * ctx.theta + pt) * np.sin(h * math.pi * ctx.v + pz)
        total += amp; amp *= 0.55
    return _norm01(0.5 + 0.5 * out / total)


@_reg("voronoi", [], [("cells_u", "Cells θ", 2, 40, 1, 10),
                      ("cells_v", "Cells z", 1, 30, 1, 8),
                      ("jitter", "Jitter", 0, 1, 0.05, 0.8),
                      ("metric", "F2-F1 (0=F1)", 0, 1, 1, 0),
                      ("seed", "Seed", 1, 99, 1, 7)],
      category="generator", label="Voronoi")
def _n_voronoi(ins, p, ctx):
    cu = max(2, int(_p(p, "cells_u", 10))); cv = max(1, int(_p(p, "cells_v", 8)))
    jit = _p(p, "jitter", 0.8); seed = int(_p(p, "seed", 7))
    metric = int(round(_p(p, "metric", 0)))
    rng = np.random.default_rng(seed & 0x7FFFFFFF)
    gu, gv = np.meshgrid((np.arange(cu) + 0.5) / cu, (np.arange(cv) + 0.5) / cv)
    seeds = np.stack([gu.ravel(), gv.ravel()], axis=1).astype(np.float32)
    seeds[:, 0] += (rng.uniform(-0.5, 0.5, len(seeds)) * jit / cu).astype(np.float32)
    seeds[:, 1] += (rng.uniform(-0.5, 0.5, len(seeds)) * jit / cv).astype(np.float32)
    su = seeds[:, 0]; sv = seeds[:, 1]
    u = ctx.u.ravel().astype(np.float32); v = ctx.v.ravel().astype(np.float32)
    npts = u.size
    field = np.empty(npts, dtype=np.float32)
    # Chunk over points so the (points x seeds) distance matrix stays bounded in
    # memory even at export res with many cells (a 36k x 1200 float64 array is ~350 MB).
    step = max(1, int(2_000_000 // max(1, len(seeds))))
    for s in range(0, npts, step):
        e_ = min(npts, s + step)
        du = np.abs(u[s:e_, None] - su[None, :]); du = np.minimum(du, 1.0 - du)  # periodic in u
        dv = v[s:e_, None] - sv[None, :]
        d = np.sqrt((du * cu) ** 2 + (dv * cv) ** 2)     # cell-normalised distance
        if metric:
            d2 = np.partition(d, 1, axis=1)[:, :2]
            field[s:e_] = d2[:, 1] - d2[:, 0]
        else:
            field[s:e_] = d.min(axis=1)
    # Normalise by a RESOLUTION-INDEPENDENT constant (not the empirical max, which
    # drifts between preview and export res so holes shift between preview and print).
    norm = 0.6 if metric else 1.0
    return _norm01((field / norm).reshape(ctx.nz, ctx.nt))


@_reg("gyroid", [], [("period_u", "Period θ", 1, 20, 1, 6),
                     ("period_v", "Period z", 1, 20, 1, 6)],
      category="generator", label="Gyroid")
def _n_gyroid(ins, p, ctx):
    a = _p(p, "period_u", 6) * 2 * math.pi; b = _p(p, "period_v", 6) * 2 * math.pi
    u = ctx.u; v = ctx.v
    g = (np.sin(a * u) * np.cos(b * v) + np.sin(b * v) * np.cos(a * u))
    return _norm01(0.5 + 0.5 * g)


@_reg("stripes", [], [("axis", "Axis (0=θ 1=z)", 0, 1, 1, 1),
                      ("count", "Count", 1, 40, 1, 10),
                      ("duty", "Duty", 0.05, 0.95, 0.01, 0.5),
                      ("soft", "Softness", 0, 0.5, 0.01, 0.05)],
      category="generator", label="Stripes")
def _n_stripes(ins, p, ctx):
    axis = int(round(_p(p, "axis", 1)))
    n = _p(p, "count", 10); duty = _p(p, "duty", 0.5); soft = _p(p, "soft", 0.05) + 1e-6
    coord = (ctx.u if axis == 0 else ctx.v) * n
    saw = np.mod(coord, 1.0)
    # smooth band: ~1 inside [0, duty], ~0 outside, soft edges of width `soft`
    return _norm01(np.clip(np.minimum(saw, duty - saw) / soft + 0.5, 0, 1))


@_reg("checker", [], [("cols", "Columns", 1, 40, 1, 8),
                      ("rows", "Rows", 1, 40, 1, 8)],
      category="generator", label="Checker")
def _n_checker(ins, p, ctx):
    c = max(1, int(_p(p, "cols", 8))); r = max(1, int(_p(p, "rows", 8)))
    a = np.floor(ctx.u * c).astype(int) + np.floor(ctx.v * r).astype(int)
    return (a % 2).astype(float)


# --------------------------------------------------------------------------- #
#  Math  (field inputs, elementwise)
# --------------------------------------------------------------------------- #

@_reg("add", ["a", "b"], [], missing={"a": 0.0, "b": 0.0}, category="math", label="Add")
def _n_add(ins, p, ctx):
    return ins["a"] + ins["b"]


@_reg("sub", ["a", "b"], [], missing={"a": 0.0, "b": 0.0}, category="math", label="Subtract")
def _n_sub(ins, p, ctx):
    return ins["a"] - ins["b"]


@_reg("mul", ["a", "b"], [], missing={"a": 1.0, "b": 1.0}, category="math", label="Multiply")
def _n_mul(ins, p, ctx):
    return ins["a"] * ins["b"]


@_reg("mix", ["a", "b", "t"], [("t", "Blend (if unwired)", 0, 1, 0.01, 0.5)],
      missing={"a": 0.0, "b": 1.0, "t": None}, category="math", label="Mix / Lerp")
def _n_mix(ins, p, ctx):
    t = ins["t"] if ins.get("t") is not None else _field(ctx, _p(p, "t", 0.5))
    return ins["a"] * (1 - t) + ins["b"] * t


@_reg("min", ["a", "b"], [], missing={"a": 1.0, "b": 1.0}, category="math", label="Min")
def _n_min(ins, p, ctx):
    return np.minimum(ins["a"], ins["b"])


@_reg("max", ["a", "b"], [], missing={"a": 0.0, "b": 0.0}, category="math", label="Max")
def _n_max(ins, p, ctx):
    return np.maximum(ins["a"], ins["b"])


@_reg("abs", ["x"], [], missing={"x": 0.0}, category="math", label="Abs")
def _n_abs(ins, p, ctx):
    return np.abs(ins["x"])


@_reg("invert", ["x"], [], missing={"x": 0.0}, category="math", label="Invert (1-x)")
def _n_invert(ins, p, ctx):
    return 1.0 - ins["x"]


@_reg("pow", ["x"], [("exp", "Exponent", 0.1, 6, 0.1, 2)],
      missing={"x": 0.0}, category="math", label="Power")
def _n_pow(ins, p, ctx):
    return np.power(np.clip(ins["x"], 0, None), _p(p, "exp", 2))


@_reg("clamp", ["x"], [("lo", "Low", 0, 1, 0.01, 0), ("hi", "High", 0, 1, 0.01, 1)],
      missing={"x": 0.0}, category="math", label="Clamp")
def _n_clamp(ins, p, ctx):
    return np.clip(ins["x"], _p(p, "lo", 0), _p(p, "hi", 1))


@_reg("remap", ["x"], [("in_lo", "In low", -1, 2, 0.01, 0), ("in_hi", "In high", -1, 2, 0.01, 1),
                       ("out_lo", "Out low", -1, 2, 0.01, 0), ("out_hi", "Out high", -1, 2, 0.01, 1)],
      missing={"x": 0.0}, category="math", label="Remap")
def _n_remap(ins, p, ctx):
    il, ih = _p(p, "in_lo", 0), _p(p, "in_hi", 1)
    ol, oh = _p(p, "out_lo", 0), _p(p, "out_hi", 1)
    t = (ins["x"] - il) / (ih - il if abs(ih - il) > 1e-9 else 1e-9)
    return ol + (oh - ol) * t


@_reg("smoothstep", ["x"], [("edge0", "Edge 0", 0, 1, 0.01, 0.35),
                            ("edge1", "Edge 1", 0, 1, 0.01, 0.65)],
      missing={"x": 0.0}, category="math", label="Smoothstep")
def _n_smoothstep(ins, p, ctx):
    e0, e1 = _p(p, "edge0", 0.35), _p(p, "edge1", 0.65)
    t = np.clip((ins["x"] - e0) / (e1 - e0 if abs(e1 - e0) > 1e-9 else 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------- #
#  Domain warps  (resample a field along modified surface coords)
# --------------------------------------------------------------------------- #

@_reg("twist", ["x"], [("turns", "Turns", -3, 3, 0.05, 0.5)],
      missing={"x": 0.0}, category="warp", label="Twist")
def _n_twist(ins, p, ctx):
    turns = _p(p, "turns", 0.5)
    return sample(ins["x"], ctx.u - turns * ctx.v, ctx.v, ctx)


@_reg("warp", ["x", "disp"], [("amount", "Amount", 0, 0.5, 0.01, 0.15)],
      missing={"x": 0.0, "disp": 0.5}, category="warp", label="Warp θ")
def _n_warp(ins, p, ctx):
    amt = _p(p, "amount", 0.15)
    return sample(ins["x"], ctx.u + amt * (2 * ins["disp"] - 1), ctx.v, ctx)


@_reg("kaleido", ["x"], [("sectors", "Sectors", 1, 24, 1, 6)],
      missing={"x": 0.0}, category="warp", label="Kaleidoscope")
def _n_kaleido(ins, p, ctx):
    n = max(1, int(_p(p, "sectors", 6)))
    folded = np.abs(np.mod(ctx.u * n, 2.0) - 1.0) / n     # mirror into n sectors
    return sample(ins["x"], folded, ctx.v, ctx)


@_reg("mirror", ["x"], [], missing={"x": 0.0}, category="warp", label="Mirror θ")
def _n_mirror(ins, p, ctx):
    return sample(ins["x"], np.abs(2 * ctx.u - 1.0) * 0.5, ctx.v, ctx)


@_reg("tile", ["x"], [("reps_u", "Repeat θ", 1, 12, 1, 2),
                      ("reps_v", "Repeat z", 1, 12, 1, 2)],
      missing={"x": 0.0}, category="warp", label="Tile")
def _n_tile(ins, p, ctx):
    ru = max(1, int(_p(p, "reps_u", 2))); rv = max(1, int(_p(p, "reps_v", 2)))
    return sample(ins["x"], np.mod(ctx.u * ru, 1.0), np.mod(ctx.v * rv, 1.0), ctx)


# --------------------------------------------------------------------------- #
#  Terminals
# --------------------------------------------------------------------------- #

@_reg("displace", ["base", "detail"], [("amp", "Amount", 0, 0.6, 0.01, 0.12),
                                       ("mode", "Add(0)/Mul(1)", 0, 1, 1, 1)],
      missing={"base": 60.0, "detail": 0.5}, category="terminal", label="Displace (mm)")
def _n_displace(ins, p, ctx):
    amp = _p(p, "amp", 0.12); mode = int(round(_p(p, "mode", 1)))
    d = 2 * ins["detail"] - 1.0                     # centre a [0,1] pattern to [-1,1]
    if mode:
        return ins["base"] * (1 + amp * d)
    return ins["base"] + amp * 40.0 * d             # add mode: amp scaled to mm


# `output` is handled specially by evaluate(); it just names radius + holes ports.
REGISTRY["output"] = {
    "kind": "output", "label": "Output", "category": "terminal",
    "inputs": ["radius", "holes"],
    "params": [("threshold", "Hole threshold", 0.05, 0.95, 0.01, 0.5),
               ("invert", "Invert holes", 0, 1, 1, 0),
               ("top_solid", "Top solid band mm", 0, 40, 1, 12)],
    "missing": {}, "fn": None,
}


# --------------------------------------------------------------------------- #
#  Evaluator
# --------------------------------------------------------------------------- #

class GraphError(Exception):
    pass


def _index(graph):
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    # incoming[node_id][port] = source_node_id
    incoming = {nid: {} for nid in nodes}
    for e in graph.get("edges", []):
        dst, port = e.get("to"), e.get("toPort")
        if dst in incoming and port:
            incoming[dst][port] = e.get("from")
    return nodes, incoming


def _find_output(nodes):
    outs = [nid for nid, n in nodes.items() if n.get("type") == "output"]
    if not outs:
        raise GraphError("graph has no output node")
    return outs[0]


def output_node(graph):
    for n in graph.get("nodes", []):
        if n.get("type") == "output":
            return n
    return None


def output_wants(graph, port):
    """True if the output node's `port` (e.g. 'holes') is wired."""
    out = output_node(graph)
    if out is None:
        return False
    return any(e.get("to") == out["id"] and e.get("toPort") == port
               for e in graph.get("edges", []))


def output_param(graph, key, default):
    out = output_node(graph)
    if out is None:
        return default
    return _p(out.get("params", {}), key, default)


def evaluate(graph, theta, zf, zf1d, need_radius=True, need_holes=True):
    """Evaluate the graph on the given grid. Returns dict:
       {"radius": (nz,nt) mm float or None, "holes": (nz,nt) bool or None,
        "warnings": [...]}. `need_radius`/`need_holes` skip a branch the caller
       won't use (the mesher evaluates radius on the vertex grid and holes on the
       cell-centre grid, so each call only needs one)."""
    ctx = Ctx(theta, zf, zf1d)
    nodes, incoming = _index(graph)
    out_id = _find_output(nodes)
    warnings = []
    cache = {}
    visiting = set()

    def evparam(node, key, default):
        return _p(node.get("params", {}), key, default)

    def ev(nid):
        if nid in cache:
            return cache[nid]
        if nid in visiting:
            raise GraphError("cycle detected at node %s" % nid)
        node = nodes.get(nid)
        if node is None:
            raise GraphError("edge points at missing node %s" % nid)
        kind = node.get("type")
        spec = REGISTRY.get(kind)
        if spec is None:
            raise GraphError("unknown node type %r" % kind)
        visiting.add(nid)
        ins = {}
        for port in spec["inputs"]:
            src = incoming.get(nid, {}).get(port)
            if src is not None:
                ins[port] = ev(src)
            else:
                fill = spec["missing"].get(port, 0.0)
                ins[port] = None if fill is None else _field(ctx, fill)
        val = spec["fn"](ins, node.get("params", {}), ctx)
        visiting.discard(nid)
        cache[nid] = val
        return val

    out_node = nodes[out_id]

    # radius (required when the caller needs it)
    radius = None
    if need_radius:
        rad_src = incoming.get(out_id, {}).get("radius")
        if rad_src is None:
            raise GraphError("output.radius is not connected -- wire a Form/Displace into it")
        radius = np.asarray(ev(rad_src), dtype=float)
        if float(np.nanmean(radius)) < 5.0:
            warnings.append("Radius averages <5 mm -- did you wire a 0..1 pattern straight "
                            "into radius? Route it through a Displace node.")

    # holes (optional)
    holes = None
    if need_holes:
        hole_src = incoming.get(out_id, {}).get("holes")
        if hole_src is not None:
            field = _norm01(ev(hole_src))
            thr = evparam(out_node, "threshold", 0.5)
            inv = int(round(evparam(out_node, "invert", 0)))
            open_ = field >= thr
            holes = ~open_ if inv else open_       # True where a HOLE is cut

    return {"radius": radius, "holes": holes, "warnings": warnings}


def registry_for_ui():
    """Serialisable node catalogue for the front-end node palette."""
    out = {}
    for kind, spec in REGISTRY.items():
        out[kind] = {
            "label": spec["label"], "category": spec["category"],
            "inputs": list(spec["inputs"]),
            "params": [{"key": k, "label": l, "min": mn, "max": mx, "step": st, "def": dv}
                       for (k, l, mn, mx, st, dv) in spec["params"]],
        }
    return out


# The default graph: form -> displace(voronoi) -> output, voronoi -> holes.
# Reproduces a pleasant perforated vase so the canvas is never empty.
DEFAULT_GRAPH = {
    "nodes": [
        {"id": "form", "type": "form", "x": 60, "y": 60,
         "params": {"r_bottom": 70, "r_top": 55, "bulge": 18, "bulge_pos": 0.5}},
        {"id": "vor", "type": "voronoi", "x": 60, "y": 240,
         "params": {"cells_u": 12, "cells_v": 10, "jitter": 0.8, "metric": 1, "seed": 7}},
        {"id": "disp", "type": "displace", "x": 360, "y": 90,
         "params": {"amp": 0.10, "mode": 1}},
        {"id": "out", "type": "output", "x": 640, "y": 140,
         "params": {"threshold": 0.35, "invert": 0, "top_solid": 12}},
    ],
    "edges": [
        {"from": "form", "to": "disp", "toPort": "base"},
        {"from": "vor", "to": "disp", "toPort": "detail"},
        {"from": "disp", "to": "out", "toPort": "radius"},
        {"from": "vor", "to": "out", "toPort": "holes"},
    ],
}


if __name__ == "__main__":
    # Smoke test: evaluate the default graph on a small uniform grid.
    nt, nz = 120, 90
    th = np.broadcast_to(np.linspace(0, 2 * math.pi, nt, endpoint=False)[None, :], (nz, nt)).copy()
    zf1d = np.linspace(0, 1, nz)
    zf = np.broadcast_to(zf1d[:, None], (nz, nt)).copy()
    res = evaluate(DEFAULT_GRAPH, th, zf, zf1d)
    r = res["radius"]
    print("nodes:", len(REGISTRY), "| radius mm  min=%.1f mean=%.1f max=%.1f"
          % (r.min(), r.mean(), r.max()))
    print("holes:", None if res["holes"] is None else
          "%d/%d cells open" % (int(res["holes"].sum()), res["holes"].size))
    print("warnings:", res["warnings"] or "none")
    # exercise every node type once for shape/no-crash
    bad = []
    for kind, spec in REGISTRY.items():
        if kind == "output":
            continue
        ins = {port: np.full((nz, nt), 0.5) for port in spec["inputs"]}
        try:
            v = spec["fn"](ins, {k: dv for (k, _l, _mn, _mx, _s, dv) in spec["params"]}, Ctx(th, zf, zf1d))
            assert v.shape == (nz, nt), "shape %s" % (v.shape,)
        except Exception as e:
            bad.append("%s: %s" % (kind, e))
    print("per-node check:", "ALL OK" if not bad else bad)
