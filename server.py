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


def make_shade(params, preview=True, export=False):
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
        path = os.path.join(OUTDIR, "shade.stl")
        lamp_engine.write_binary_stl(path, v, f)
        result["metrics"] = rep
        result["files"] = {"stl": "shade.stl"}
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
        return self._send(404, json.dumps({"error": "not found"}))

    def _download(self):
        fname = os.path.basename(self.path.split("/download/")[1].split("?")[0])
        fp = os.path.join(OUTDIR, fname)
        if not (fname and os.path.exists(fp)):
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
                  "/api/preset/save")
        if self.path not in routes:
            return self._send(404, json.dumps({"error": "not found"}))
        if not self._origin_ok():
            return self._send(403, json.dumps({"error": "forbidden"}))
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length) or b"{}")
        try:
            if self.path == "/api/shade":
                return self._send(200, json.dumps(make_shade(req.get("params", {}), preview=True)))
            if self.path == "/api/export_shade":
                return self._send(200, json.dumps(make_shade(req.get("params", {}), preview=False, export=True)))
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
