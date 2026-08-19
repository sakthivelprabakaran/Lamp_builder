"""Headless-browser UI verification for Lamp Studio (Phase 2: twist-lock + holders)."""
import os, time, json, urllib.request
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots"); os.makedirs(SHOTS, exist_ok=True)
URL = "http://127.0.0.1:8776/"
errors, console = [], []

# Pre-warm the build123d worker OUTSIDE the browser so Chromium's software-WebGL
# CPU load doesn't starve the (one-time) OCP import and blow the in-page poll.
print("pre-warming base worker...")
_t = time.time()
try:
    req = urllib.request.Request(URL + "api/base", method="POST",
        data=json.dumps({"params": {}, "shade_params": {}, "export": False}).encode(),
        headers={"Content-Type": "application/json", "Origin": URL.rstrip("/"),
                 "Host": "127.0.0.1:8776"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    print("warm base ok=%s in %.0fs" % (r.get("ok"), time.time() - _t))
except Exception as e:
    print("warm failed:", e)


def wait_for(page, expr, timeout=30, poll=0.2):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if page.evaluate(expr):
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=[
        "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
    page.on("console", lambda m: console.append("%s: %s" % (m.type, m.text)))
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    wait_for(page, "() => !!window.__shade", 30)
    print("initial shade bbox:", page.evaluate("() => window.__shade.bbox"),
          "| bayonet:", page.evaluate("() => window.LS.shade.bayonet"))
    page.screenshot(path=os.path.join(SHOTS, "p2_01_shade.png"))

    # Generate base (has bayonet lugs + m10 holder mount), show Both.
    print("generating base (worker pre-warmed)...")
    page.click("#genBase")
    ok = wait_for(page, "() => !!window.__base", 60)
    print("base rendered:", ok, page.evaluate("() => window.__base"))
    page.click("#showSeg button[data-show='both']"); time.sleep(1.2)
    page.screenshot(path=os.path.join(SHOTS, "p2_02_both.png"))
    page.click("#showSeg button[data-show='base']"); time.sleep(0.8)
    page.screenshot(path=os.path.join(SHOTS, "p2_03_base.png"))

    # Switch holder type to B22, regenerate, screenshot underside-ish.
    page.select_option("#sel_holder_type", "b22")
    print("holder type now:", page.evaluate("() => window.LS.base.holder_type"))
    page.click("#genBase")
    wait_for(page, "() => window.__base && window.__base.verts>0", 60)
    time.sleep(0.8); page.screenshot(path=os.path.join(SHOTS, "p2_04_base_b22.png"))

    # Test-fit ring.
    page.click("#genTestfit")
    time.sleep(6)
    print("after test-fit HUD:", page.eval_on_selector("#hud", "el=>el.textContent"))

    browser.close()

print("\npageerrors:", errors or "none")
print("console errors/warnings:", [c for c in console if c.startswith(("error", "warning"))] or "none")
print("shots:", sorted(f for f in os.listdir(SHOTS) if f.startswith("p2_")))
