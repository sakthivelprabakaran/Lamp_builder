"""
server.py  --  Localhost web app for Lamp Studio (parametric lamp-shade engine).

Stdlib only (no Flask needed). Binds 127.0.0.1 exclusively and rejects foreign
Origin / Host headers -- it never listens off this machine.

The SHADE is generated in-process (pure numpy, ~50 ms) for instant slider
preview. The build123d BASE is generated through a single persistent worker
subprocess (warms the OCP kernel once). Presets are saved as JSON under presets/.

Run:  python server.py     ->  http://127.0.0.1:8776
"""
import os, sys, json, subprocess, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "output")
PRESETS = os.path.join(HERE, "presets")
PORT = 8776
BASE_TIMEOUT = 300  # seconds -- generous so a cold build123d import under machine
                    # load (other servers running) can't trip a false "crash".

sys.path.insert(0, HERE)
import lamp_engine   # numpy only; no build123d import here
import graph_engine  # Phase 6 field node-graph (numpy only)

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(PRESETS, exist_ok=True)

ALLOWED_HOSTS = {"127.0.0.1:%d" % PORT, "localhost:%d" % PORT}
ALLOWED_ORIGINS = {"http://127.0.0.1:%d" % PORT, "http://localhost:%d" % PORT}


# --------------------------------------------------------------------------- #
#  Base worker (persistent build123d subprocess)
# --------------------------------------------------------------------------- #

class BaseWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None

    def _spawn(self):
        # Route worker stderr to a real file. Under a windowless pythonw launch the
        # inherited stderr is invalid, which otherwise crashes the worker on its
        # first diagnostic write; a file handle is always valid and gives us logs.
        errlog = open(os.path.join(HERE, "_worker.log"), "ab", buffering=0)
        self._proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "worker.py"), "--serve"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errlog,
            text=True, bufsize=1, cwd=HERE,
        )

    def start(self):
        with self._lock:
            if self._proc is None or self._proc.poll() is not None:
                self._spawn()

    def _kill(self):
        if self._proc is not None:
            try:
                self._proc.kill()
            except Exception:
                pass
            self._proc = None

    def run(self, job):
        err = {"ok": False, "error": "Base build timed out or the worker crashed."}
        with self._lock:
            if self._proc is None or self._proc.poll() is not None:
                self._spawn()
            try:
                self._proc.stdin.write(json.dumps(job) + "\n")
                self._proc.stdin.flush()
            except Exception:
                self._kill(); self._spawn()
                return err
            box = {}

            def _read():
                try:
                    box["line"] = self._proc.stdout.readline()
                except Exception:
                    box["line"] = ""

            t = threading.Thread(target=_read, daemon=True)
            t.start(); t.join(BASE_TIMEOUT)
            line = box.get("line")
            if t.is_alive() or not line:
                self._kill(); self._spawn()
                return err
            try:
                return json.loads(line)
            except Exception:
                return {"ok": False, "error": "Worker produced invalid output."}


WORKER = BaseWorker()


# --------------------------------------------------------------------------- #
#  Shade (in-process, numpy)
# --------------------------------------------------------------------------- #

def _num(params, defaults):
    out = dict(defaults)
    for k in defaults:
        if k in params:
            try:
                out[k] = type(defaults[k])(params[k])
            except Exception:
                pass
    return out


def _safe_out(rel):
    """Absolute path for a caller-supplied path under output/, or None if it tries
    to escape. Batch exports name their own files, so never trust the string."""
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel:
        return None
    parts = [q for q in rel.split("/") if q not in ("", ".")]
    if any(q == ".." or os.path.isabs(q) or ":" in q for q in parts):
        return None
    fp = os.path.abspath(os.path.join(OUTDIR, *parts))
    root = os.path.abspath(OUTDIR)
    if os.path.commonpath([fp, root]) != root:
        return None
    return fp


def _slug(s, fallback="item"):
    out = "".join(c if (c.isalnum() or c in "-_ .") else "_" for c in str(s)).strip()
    return out or fallback


def _slug_path(s):
    """Slug each segment of a relative path, keeping the separators."""
    segs = [_slug(q, "") for q in str(s or "").replace("\\", "/").split("/")]
    return "/".join(q for q in segs if q)


def make_shade(params, preview=True, export=False, dest=None):
    """dest: {"subdir": "catalogue/<batch>", "name": "<slug>"} -- write the STL there
    instead of the shared output/shade.stl (so a catalogue run can't race itself)."""
    p = _num(params, lamp_engine.SHADE_DEFAULTS)
    if isinstance(params.get("stack"), list):   # operator stack (Phase 5)
        p["stack"] = params["stack"]
    if isinstance(params.get("graph"), dict):    # field node-graph (Phase 6) -- wins
        p["graph"] = params["graph"]
    if preview:                       # cap resolution for a snappy preview
        p["res_theta"] = min(p["res_theta"], 160)
        p["res_z"] = min(p["res_z"], 120)
    v, f = lamp_engine.build_shade_mesh(p)
    wall_ok, wall = lamp_engine.min_wall_ok(p)
    warnings = []
    if not wall_ok:
        warnings.append("Wall %.1f mm is thin; <0.8 mm may be fragile." % wall)

    result = {"ok": True, "warnings": warnings}
    if export:
        ok, rep = lamp_engine.verify_mesh(v, f)
        rel = "shade.stl"
        if dest:
            rel = "/".join(x for x in (_slug_path(dest.get("subdir", "")),
                                       _slug(dest.get("name", "shade")) + ".stl") if x)
        path = _safe_out(rel)
        if path is None:
            return {"ok": False, "error": "Bad export path."}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lamp_engine.write_binary_stl(path, v, f)
        result["metrics"] = rep
        result["files"] = {"stl": rel}
        if not rep["watertight"]:
            result["warnings"].append("Mesh is not watertight -- do not print.")
        elif rep.get("components", 1) > 1:
            result["warnings"].append(
                "Pattern splits the shade into %d disconnected pieces -- it would print "
                "as loose parts. Lower the hole threshold, reduce hole size, or keep a "
                "connecting web." % rep["components"])
    else:
        result["vertices"] = v.reshape(-1).tolist()
        result["indices"] = f.reshape(-1).tolist()
        result["metrics"] = {"tris": int(len(f)), "verts": int(len(v))}
    return result


# --------------------------------------------------------------------------- #
#  HTTP
# --------------------------------------------------------------------------- #

class Handler(BaseHTTPRequestHandler):
    # HTTP/1.1 keep-alive. Without this the default HTTP/1.0 races with a
    # browser reusing a socket the server is closing, so rapid repeated fetches
    # (live sliders) hang. Every response sets Content-Length, so keep-alive is
    # safe; idle connections close after `timeout`.
    protocol_version = "HTTP/1.1"
    timeout = 30

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _origin_ok(self):
        origin = self.headers.get("Origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return False
        return self.headers.get("Host") in ALLOWED_HOSTS

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if not self._origin_ok():
            return self._send(403, json.dumps({"error": "forbidden"}))
        if self.path == "/api/defaults":
            return self._send(200, json.dumps({
                "shade": lamp_engine.SHADE_DEFAULTS,
                "base": lamp_engine.BASE_DEFAULTS,
                "op_schema": lamp_engine.OP_SCHEMA,
                "stack_default": lamp_engine.STACK_DEFAULT,
            }))
        if self.path == "/api/graph_defaults":
            return self._send(200, json.dumps({
                "registry": graph_engine.registry_for_ui(),
                "default_graph": graph_engine.DEFAULT_GRAPH,
            }))
        if self.path == "/api/presets":
            return self._send(200, json.dumps({"presets": _list_presets()}))
        if self.path.startswith("/api/preset/"):
            from urllib.parse import unquote
            name = os.path.basename(unquote(self.path.split("/api/preset/")[1].split("?")[0]))
            fp = os.path.join(PRESETS, name + ".json")
            if os.path.exists(fp):
                with open(fp) as f:
                    return self._send(200, f.read())
            return self._send(404, json.dumps({"error": "not found"}))
        if self.path.startswith("/download/"):
            return self._download()
        if self.path.startswith("/view/"):
            return self._view()
        return self._send(404, json.dumps({"error": "not found"}))

    # /download/ forces an attachment, which is right for STLs but useless for the
    # catalogue contact sheet -- it has to render in a tab, with its <img> tags
    # resolving. /view/ serves the same output/ tree inline, html/png/csv only.
    # .stl is included so the sheet's relative <a href="v01.stl"> works in-tab; it
    # stays relative so the copy inside the zip still works offline.
    VIEW_TYPES = {".html": "text/html; charset=utf-8", ".png": "image/png",
                  ".csv": "text/csv; charset=utf-8", ".json": "application/json",
                  ".stl": "application/octet-stream"}

    def _view(self):
        from urllib.parse import unquote
        rel = unquote(self.path.split("/view/")[1].split("?")[0])
        fp = _safe_out(rel)
        ctype = self.VIEW_TYPES.get(os.path.splitext(rel)[1].lower())
        if not (fp and ctype and os.path.isfile(fp)):
            return self._send(404, json.dumps({"error": "not found"}))
        with open(fp, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        # The contact sheet is a generated static page: no scripts, inline <style>,
        # local images only. 'unsafe-inline' for style is required or the sheet renders
        # unstyled; everything else stays denied.
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _download(self):
        from urllib.parse import unquote
        rel = unquote(self.path.split("/download/")[1].split("?")[0])
        fp = _safe_out(rel)            # may sit in a catalogue subdirectory
        fname = os.path.basename(rel)
        if not (fp and fname and os.path.isfile(fp)):
            return self._send(404, json.dumps({"error": "not found"}))
        with open(fp, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", 'attachment; filename="%s"' % fname)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        routes = ("/api/shade", "/api/export_shade", "/api/base", "/api/testfit",
                  "/api/preset/save", "/api/batch/thumb", "/api/batch/finish")
        if self.path not in routes:
            return self._send(404, json.dumps({"error": "not found"}))
        if not self._origin_ok():
            return self._send(403, json.dumps({"error": "forbidden"}))
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/shade":
                return self._send(200, json.dumps(make_shade(req.get("params", {}), preview=True)))
            if self.path == "/api/export_shade":
                return self._send(200, json.dumps(make_shade(
                    req.get("params", {}), preview=bool(req.get("fast")), export=True,
                    dest=req.get("dest"))))
            if self.path == "/api/batch/thumb":
                return self._send(200, json.dumps(_save_thumb(req)))
            if self.path == "/api/batch/finish":
                return self._send(200, json.dumps(_finish_batch(req)))
            if self.path in ("/api/base", "/api/testfit"):
                job = {"params": req.get("params", {}),
                       "shade_params": req.get("shade_params", {}),
                       "outdir": OUTDIR, "tolerance": req.get("tolerance", 0.2),
                       "export": req.get("export", True),
                       "kind": "testfit" if self.path == "/api/testfit" else "base"}
                return self._send(200, json.dumps(WORKER.run(job)))
            if self.path == "/api/preset/save":
                return self._send(200, json.dumps(_save_preset(req)))
        except Exception as e:
            return self._send(200, json.dumps({"ok": False, "error": "%s: %s" % (type(e).__name__, e)}))


def _list_presets():
    try:
        return sorted(f[:-5] for f in os.listdir(PRESETS) if f.endswith(".json"))
    except Exception:
        return []


def _save_preset(req):
    name = "".join(c if (c.isalnum() or c in "-_ ") else "_" for c in str(req.get("name", "")).strip())
    if not name:
        return {"ok": False, "error": "A preset name is required."}
    payload = {"shade": req.get("shade", {}), "base": req.get("base", {})}
    with open(os.path.join(PRESETS, name + ".json"), "w") as f:
        json.dump(payload, f, indent=2)
    return {"ok": True, "presets": _list_presets(), "name": name}


# --------------------------------------------------------------------------- #
#  Batch / catalogue export (Phase 4)
# --------------------------------------------------------------------------- #
#  The sweep is driven from the browser: it walks the axis grid, POSTs each
#  variant to /api/export_shade with its own `dest`, snapshots the WebGL canvas
#  and POSTs the PNG here, then calls /api/batch/finish to get a contact sheet +
#  manifest + zip. Client-driven because only the browser can render thumbnails,
#  and it keeps the server free of long-running job state.

def _save_thumb(req):
    png = str(req.get("png", ""))
    if "," in png:
        png = png.split(",", 1)[1]                 # strip the data: URL prefix
    rel = "/".join(x for x in (_slug_path(req.get("subdir", "")),
                               _slug(req.get("name", "thumb")) + ".png") if x)
    fp = _safe_out(rel)
    if fp is None:
        return {"ok": False, "error": "Bad thumbnail path."}
    import base64
    try:
        data = base64.b64decode(png, validate=True)
    except Exception:
        return {"ok": False, "error": "Thumbnail was not valid base64 PNG data."}
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "wb") as f:
        f.write(data)
    return {"ok": True, "file": rel}


def _mark_duplicates(items):
    """Tag variants whose STL is byte-identical to an earlier one.

    A swept parameter can be completely inert -- e.g. pat_cols does nothing unless
    the shape actually has a perforation op -- and the user would otherwise wait out
    the whole sweep for a folder of clones. Equal triangle counts don't prove it, so
    hash the files (they're on disk already and the zip re-reads them anyway)."""
    import hashlib
    seen = {}
    for it in items:
        fp = _safe_out(it.get("stl") or "")
        if not (fp and os.path.isfile(fp)):
            continue
        h = hashlib.md5()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        d = h.hexdigest()
        if d in seen:
            it["dup_of"] = seen[d]
        else:
            seen[d] = it.get("name", "")
    return items


def _finish_batch(req):
    """Write manifest.csv + a browsable index.html contact sheet, then zip the
    whole catalogue folder for one-click download."""
    import csv, io, zipfile
    sub = _slug_path(req.get("subdir", ""))
    root = _safe_out(sub)
    if not sub or root is None or not os.path.isdir(root):
        return {"ok": False, "error": "Unknown catalogue folder."}
    items = req.get("items") or []
    title = str(req.get("title") or sub.split("/")[-1])
    axes = req.get("axes") or []
    _mark_duplicates(items)

    cols = ["name", "stl", "thumb", "tris", "watertight", "single_piece",
            "components", "printable", "dup_of"] + \
           ["axis%d" % (i + 1) for i in range(len(axes))]
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(cols + ["axis_labels"])
    for it in items:
        vals = it.get("values") or []
        w.writerow([it.get("name", ""), it.get("stl", ""), it.get("thumb", ""),
                    it.get("tris", ""), it.get("watertight", ""),
                    it.get("single_piece", ""), it.get("components", ""),
                    it.get("printable", ""), it.get("dup_of", "")] + list(vals) +
                   ["; ".join("%s=%s" % (a.get("label", "?"), v)
                             for a, v in zip(axes, vals))])
    with open(os.path.join(root, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())

    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))
    cards = []
    for it in items:
        vals = it.get("values") or []
        label = " · ".join("%s %s" % (esc(a.get("label", "?")), esc(v))
                           for a, v in zip(axes, vals))
        bad = (not it.get("watertight")) or not it.get("single_piece", True)
        if bad:
            note = "NOT PRINTABLE — %s" % esc(it.get("why", "failed the mesh gate"))
        elif it.get("dup_of"):
            note = "identical to %s — this axis does nothing to this shape" % esc(it["dup_of"])
        else:
            note = "%s tris" % esc(it.get("tris", "?"))
        thumb = esc(os.path.basename(it.get("thumb") or ""))
        stl = esc(os.path.basename(it.get("stl") or ""))
        cls = "bad" if bad else ("dup" if it.get("dup_of") else "ok")
        cards.append(
            '<figure class="%s"><a href="%s"><img src="%s" alt="%s"></a>'
            '<figcaption><b>%s</b><span>%s</span></figcaption></figure>'
            % (cls, stl, thumb, esc(it.get("name", "")),
               label or esc(it.get("name", "")), note))
    html = """<!doctype html><meta charset="utf-8"><title>%s — Lamp Studio catalogue</title>
<style>
 body{background:#16191f;color:#e8e8ea;font:13px/1.5 system-ui,sans-serif;margin:24px}
 h1{font-size:18px;font-weight:600;margin:0 0 4px} p.sub{color:#9aa3af;margin:0 0 20px}
 .grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
 figure{margin:0;background:#1e222a;border:1px solid #2c323c;border-radius:8px;overflow:hidden}
 figure.bad{border-color:#a4443a} figure.dup{opacity:.6}
 img{display:block;width:100%%;background:#0f1216}
 figcaption{padding:8px 10px;display:flex;flex-direction:column;gap:2px}
 figcaption b{font-weight:600} figcaption span{color:#9aa3af;font-size:12px}
 figure.bad figcaption span{color:#e0796d} figure.dup figcaption span{color:#ffcf5c}
 a{color:inherit;text-decoration:none}
</style>
<h1>%s</h1>
<p class="sub">%d variants · click a thumbnail to open its STL · sweep: %s</p>
<div class="grid">%s</div>
""" % (esc(title), esc(title), len(items),
       esc(" × ".join("%s %s→%s in %s steps" % (a.get("label", "?"), a.get("from"),
                                                a.get("to"), a.get("steps"))
                      for a in axes)) or "n/a",
       "\n".join(cards))
    with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    parent = os.path.dirname(sub)                 # zip sits NEXT TO the folder, not in
    zrel = (parent + "/" if parent else "") + sub.split("/")[-1] + ".zip"
    zpath = _safe_out(zrel)
    if zpath is None:
        return {"ok": False, "error": "Bad zip path."}
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                full = os.path.join(dirpath, fn)
                z.write(full, os.path.relpath(full, root))
    return {"ok": True, "count": len(items), "dir": sub,
            "dupes": sum(1 for it in items if it.get("dup_of")),
            "files": {"index": sub + "/index.html", "manifest": sub + "/manifest.csv",
                      "zip": zrel}}


def open_browser():
    import time
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:%d/" % PORT)


def prewarm():
    """Spawn + warm the build123d worker at startup so the user's first base
    click is instant rather than waiting on a cold ~20-40s OCP import."""
    try:
        WORKER.run({"params": {}, "shade_params": {}, "outdir": OUTDIR,
                    "tolerance": 0.3, "export": False, "kind": "base"})
    except Exception:
        pass


if __name__ == "__main__":
    print("Lamp Studio running at http://127.0.0.1:%d/  (Ctrl+C to stop)" % PORT)
    print("Shade preview is instant; the base worker is warming in the background.")
    threading.Thread(target=open_browser, daemon=True).start()
    threading.Thread(target=prewarm, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
