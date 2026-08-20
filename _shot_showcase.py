import os, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); SHOTS=os.path.join(HERE,"screenshots")
URL="http://127.0.0.1:8776/"
EXPECT=[("Showcase - Perforated Crown",82432),("Showcase - Twisted Voronoi",67248),("Showcase - Gyroid Lattice",74396)]
errors=[]
def wait_tris(page,target,timeout=60):
    end=time.time()+timeout
    while time.time()<end:
        try:
            if page.evaluate("()=>window.__shade&&window.__shade.tris")==target: return True
        except Exception: pass
        time.sleep(0.4)
    return False
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True,args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"])
    pg=b.new_context(viewport={"width":1280,"height":900}).new_page()
    pg.on("pageerror",lambda e:errors.append(str(e)))
    pg.goto(URL,wait_until="networkidle",timeout=45000)
    # ensure preset options are populated
    pg.wait_for_function("()=>document.querySelectorAll('#presetSel option').length>5",timeout=20000)
    for i,(name,tgt) in enumerate(EXPECT,1):
        pg.select_option("#presetSel", name)
        ok=wait_tris(pg,tgt)
        got=pg.evaluate("()=>window.__shade&&window.__shade.tris")
        pg.evaluate("()=>{document.getElementById('ndrawer').style.display='none';document.getElementById('hud').style.display='none';}")
        time.sleep(0.5)
        pg.locator("#view").screenshot(path=os.path.join(SHOTS,"showcase_%d_lamp.png"%i))
        if i==1:
            pg.evaluate("()=>{document.getElementById('ndrawer').style.display='';}")
            time.sleep(0.5); pg.screenshot(path=os.path.join(SHOTS,"showcase_1_graph.png"))
            pg.evaluate("()=>{document.getElementById('ndrawer').style.display='none';}")
        print("%d) %-28s target=%d got=%s match=%s"%(i,name,tgt,got,ok))
    b.close()
print("pageerrors:",errors or "none")
