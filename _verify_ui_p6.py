"""Headless-browser UI verification for Lamp Studio Phase 6 (field node graph).

Checks: page loads clean, Stack<->Node-graph toggle, default graph renders as
node cards + wires, the graph drives a watertight-preview mesh, adding a node and
wiring it regenerates, and switching back to Stack restores the old path. Server
must be up on :8776.
"""
import os, sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots"); os.makedirs(SHOTS, exist_ok=True)
URL = "http://127.0.0.1:8776/"
errors, console = [], []


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
    page = browser.new_context(viewport={"width": 1360, "height": 860}).new_page()
    page.on("console", lambda m: console.append("%s: %s" % (m.type, m.text)))
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(URL, wait_until="networkidle", timeout=30000)
    wait_for(page, "() => !!window.__shade", 30)
    print("1) initial gmode :", page.evaluate("() => window.LS.gmode"),
          "| shade tris:", page.evaluate("() => window.__shade.tris"))

    # 2) switch to node graph
    page.click("#shapemode .seg button[data-mode='graph']")
    wait_for(page, "() => window.LS.gmode==='graph'", 10)
    wait_for(page, "() => document.querySelectorAll('.ncard').length>0", 10)
    time.sleep(1.2)  # debounced graph regen
    cards = page.eval_on_selector_all(".ncard", "els => els.length")
    wires = page.eval_on_selector_all("#nwires path", "els => els.length")
    drawer = page.eval_on_selector("#ndrawer", "el => getComputedStyle(el).display")
    print("2) graph mode    : cards=%d wires=%d drawer=%s tris=%s"
          % (cards, wires, drawer, page.evaluate("() => window.__shade.tris")))
    print("   node types    :", page.evaluate("() => window.LS.graph.nodes.map(n=>n.type)"))
    page.screenshot(path=os.path.join(SHOTS, "p6_01_graph.png"))

    # 3) add a node (gyroid) via the palette
    page.select_option("#naddSel", "gyroid")
    page.click("#naddBtn")
    time.sleep(0.4)
    cards2 = page.eval_on_selector_all(".ncard", "els => els.length")
    print("3) after +gyroid : cards=%d (was %d)" % (cards2, cards))

    # 4) change a param on the voronoi node -> shade regenerates
    t_before = page.evaluate("() => window.__shade.tris")
    # bump voronoi cells_u via its first slider (voronoi card is 2nd node in default graph)
    changed = page.evaluate("""() => {
        const cards=[...document.querySelectorAll('.ncard')];
        const vor=cards.find(c=>c.querySelector('.nh').textContent.startsWith('Voronoi'));
        if(!vor) return false;
        const inp=vor.querySelector('input[type=range]'); if(!inp) return false;
        inp.value = Math.min(parseFloat(inp.max), parseFloat(inp.value)+6);
        inp.dispatchEvent(new Event('input',{bubbles:true})); return true; }""")
    wait_for(page, "() => window.__shade.tris !== %d" % t_before, 10)
    t_after = page.evaluate("() => window.__shade.tris")
    print("4) voronoi param : changed=%s tris %s -> %s (%s)"
          % (changed, t_before, t_after, "regened" if t_after != t_before else "same"))
    page.screenshot(path=os.path.join(SHOTS, "p6_02_edited.png"))

    # 5) back to stack
    page.click("#shapemode .seg button[data-mode='stack']")
    wait_for(page, "() => window.LS.gmode==='stack'", 10)
    time.sleep(0.8)
    print("5) back to stack : gmode=%s drawer=%s tris=%s"
          % (page.evaluate("() => window.LS.gmode"),
             page.eval_on_selector("#ndrawer", "el => getComputedStyle(el).display"),
             page.evaluate("() => window.__shade.tris")))

    browser.close()

print("\npageerrors:", errors or "none")
print("console errors/warnings:", [c for c in console if c.startswith(("error", "warning"))] or "none")
print("shots:", sorted(f for f in os.listdir(SHOTS) if f.startswith("p6_")))
