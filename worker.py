"""
worker.py  --  Persistent build123d worker for the BASE adapter only.

Spawned once by server.py (`worker.py --serve`) so the heavy build123d / OCP
import is paid a single time, not per request. Reads one JSON job per line on
stdin, writes one JSON result per line on stdout. The shade itself is pure numpy
and is built in-process by the server -- this worker is used only for the
build123d base, which needs a real BREP kernel.

Job:    {"params": {...}, "shade_params": {...}, "outdir": "...",
         "tolerance": 0.2, "export": true}
Result: {"ok": true, "positions": [...], "metrics": {...}, "files": {...}}
"""
import sys, json, os, time


def _log(msg):
    # Under pythonw (windowless launch) the inherited stderr is None; never let a
    # diagnostic write crash the worker.
    try:
        if sys.stderr is not None:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
    except Exception:
        pass


def _serve():
    # Warm the kernel once, up front.
    t0 = time.time()
    from build123d import export_stl, export_step  # noqa: F401
    import lamp_engine  # noqa: F401
    _log("[worker] build123d warm in %.1fs" % (time.time() - t0))

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
            res = _build(job, export_stl, export_step, lamp_engine)
        except Exception as e:
            res = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
        sys.stdout.write(json.dumps(res) + "\n")
        sys.stdout.flush()


def _build(job, export_stl, export_step, lamp_engine):
    t0 = time.time()
    params = job.get("params", {})
    shade_params = job.get("shade_params", {})
    outdir = job.get("outdir", "output")
    tol = float(job.get("tolerance", 0.2))
    os.makedirs(outdir, exist_ok=True)

    kind = job.get("kind", "base")
    if kind == "testfit":
        solid = lamp_engine.build_testfit_ring(params, shade_params)
        outbase = "testfit"
    else:
        solid = lamp_engine.build_base(params, shade_params)
        outbase = "base"

    # Tessellate for the live preview.
    verts, tris = solid.tessellate(tol)
    positions = []
    for a, b, c in tris:
        for idx in (a, b, c):
            v = verts[idx]
            positions.extend([v.X, v.Y, v.Z])

    files = {}
    if job.get("export", True):
        export_stl(solid, os.path.join(outdir, outbase + ".stl"), tolerance=tol)
        files["stl"] = outbase + ".stl"
        try:
            export_step(solid, os.path.join(outdir, outbase + ".step"))
            files["step"] = outbase + ".step"
        except Exception:
            pass

    return {
        "ok": True,
        "positions": positions,
        "metrics": {
            "triangles": len(tris),
            "volume_mm3": round(float(solid.volume), 1),
            "bbox_mm": _bbox(solid),
            "build_s": round(time.time() - t0, 2),
        },
        "files": files,
    }


def _bbox(solid):
    try:
        bb = solid.bounding_box()
        return [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)]
    except Exception:
        return None


if __name__ == "__main__":
    if "--serve" in sys.argv:
        _serve()
    else:
        # One-shot debug: python worker.py > /dev/null
        import lamp_engine
        from build123d import export_stl
        s = lamp_engine.build_base(lamp_engine.BASE_DEFAULTS, lamp_engine.SHADE_DEFAULTS)
        print("base volume", s.volume)
