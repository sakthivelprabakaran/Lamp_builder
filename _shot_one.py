import os,sys,time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")
SHOTS=os.path.join(os.path.dirname(os.path.abspath(__file__)),"screenshots")
def wait_tris(pg,t,to=60):
    end=time.time()+to
    while time.time()<end:
        try:
            if pg.evaluate("()=>window.__shade&&window.__shade.tris")==t: return True
        except: pass
        time.sleep(0.4)
    return False
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"])
    pg=b.new_context(viewport={"width":1280,"height":900}).new_page()
    pg.goto("http://127.0.0.1:8776/",wait_until="networkidle",timeout=45000)
    pg.wait_for_function("()=>document.querySelectorAll('#presetSel option').length>5",timeout=20000)
    pg.select_option("#presetSel","Showcase - Gyroid Lattice")
    ok=wait_tris(pg,91072)
    pg.evaluate("()=>{document.getElementById('ndrawer').style.display='none';document.getElementById('hud').style.display='none';}")
    time.sleep(0.5)
    pg.locator("#view").screenshot(path=os.path.join(SHOTS,"showcase_3_lamp.png"))
    print("gyroid match=%s got=%s"%(ok,pg.evaluate("()=>window.__shade.tris")))
    b.close()
