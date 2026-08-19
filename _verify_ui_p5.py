"""Headless-browser UI verification for Lamp Studio Phase 5 (operator-stack editor).

Exercises the ◆ SHAPE panel: initial stack render, add an operator, reorder,
mute, and confirm the shade regenerates (tri count / bbox changes) each time and
the page stays error-free. Server must already be up on :8776.
"""
import os, sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")  # Windows console is cp1252; prints use ▲/◆

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


def stack_types(page):
    return page.evaluate("() => (window.LS.shade.stack||[]).map(o=>o.type+(o.on?'':'(off)'))")


def shade_sig(page):
    return page.evaluate("() => window.__shade")


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=[
        "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
    page.on("console", lambda m: console.append("%s: %s" % (m.type, m.text)))
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    wait_for(page, "() => !!window.__shade", 30)

    print("1) initial stack :", stack_types(page))
    print("   shade         :", shade_sig(page))
    op_cards = page.eval_on_selector_all(".opcard", "els => els.length")
    print("   op cards       :", op_cards)
    page.screenshot(path=os.path.join(SHOTS, "p5_01_initial.png"))

    # 2) Add a 'ripple' operator via the dropdown + Add button.
    sig0 = shade_sig(page)
    page.select_option("#opadd_sel", "ripple")
    page.click("#opadd_btn")
    ok = wait_for(page, "() => (window.LS.shade.stack||[]).some(o=>o.type==='ripple')", 10)
    time.sleep(1.0)  # let debounced scheduleShade fire + regen
    print("2) after +ripple :", stack_types(page), "added=%s" % ok)
    print("   shade         :", shade_sig(page), "(was %s)" % sig0)
    page.screenshot(path=os.path.join(SHOTS, "p5_02_add_ripple.png"))

    # 3) Reorder: move the last op up one slot (▲ on last card).
    n = page.eval_on_selector_all(".opcard", "els => els.length")
    before = stack_types(page)
    page.eval_on_selector_all(".ophd button[data-a='up']",
                              "els => els[els.length-1] && els[els.length-1].click()")
    time.sleep(1.0)
    print("3) after ▲ last  :", stack_types(page), "(was", before, ")")

    # 4) Mute the ripple op and confirm regen.
    sig_before_mute = shade_sig(page)
    page.eval_on_selector_all("input[data-a='mute']",
                              "els => { const c=els[els.length-1]; c.checked=false; "
                              "c.dispatchEvent(new Event('change',{bubbles:true})); }")
    time.sleep(1.0)
    print("4) after mute    :", stack_types(page))
    print("   shade         :", shade_sig(page), "(was %s)" % sig_before_mute)
    page.screenshot(path=os.path.join(SHOTS, "p5_03_muted.png"))

    browser.close()

print("\npageerrors:", errors or "none")
print("console errors/warnings:", [c for c in console if c.startswith(("error", "warning"))] or "none")
print("shots:", sorted(f for f in os.listdir(SHOTS) if f.startswith("p5_")))
