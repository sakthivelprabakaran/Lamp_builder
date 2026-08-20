import json, os, copy, lamp_engine as e

HERE=os.path.dirname(os.path.abspath(__file__)); PRESETS=os.path.join(HERE,"presets")

def out(**kw):
    p={"threshold":0.5,"invert":0,"top_solid":12}; p.update(kw); return p

# --- A) Perforated crown: connected-web voronoi holes only in the TOP, solid base ---
A={"nodes":[
    {"id":"form","type":"form","x":40,"y":40,"params":{"r_bottom":72,"r_top":58,"bulge":22,"bulge_pos":0.45}},
    {"id":"vor","type":"voronoi","x":40,"y":230,"params":{"cells_u":14,"cells_v":14,"jitter":0.7,"metric":1,"seed":5}},
    {"id":"gz","type":"gradZ","x":40,"y":470,"params":{}},
    {"id":"mask","type":"smoothstep","x":250,"y":470,"params":{"edge0":0.4,"edge1":0.6}},
    {"id":"mul","type":"mul","x":460,"y":330,"params":{}},
    {"id":"out","type":"output","x":700,"y":120,"params":out(threshold=0.28)}],
   "edges":[
    {"from":"form","to":"out","toPort":"radius"},
    {"from":"vor","to":"mul","toPort":"a"},
    {"from":"gz","to":"mask","toPort":"x"},
    {"from":"mask","to":"mul","toPort":"b"},
    {"from":"mul","to":"out","toPort":"holes"}]}

# --- B) Twisted voronoi: cells sheared into a spiral, driving BOTH shape + holes ---
B={"nodes":[
    {"id":"form","type":"form","x":40,"y":40,"params":{"r_bottom":68,"r_top":52,"bulge":10,"bulge_pos":0.5}},
    {"id":"vor","type":"voronoi","x":40,"y":230,"params":{"cells_u":10,"cells_v":12,"jitter":0.55,"metric":1,"seed":9}},
    {"id":"tw","type":"twist","x":250,"y":230,"params":{"turns":1.1}},
    {"id":"disp","type":"displace","x":470,"y":90,"params":{"amp":0.12,"mode":1}},
    {"id":"out","type":"output","x":710,"y":150,"params":out(threshold=0.30)}],
   "edges":[
    {"from":"form","to":"disp","toPort":"base"},
    {"from":"vor","to":"tw","toPort":"x"},
    {"from":"tw","to":"disp","toPort":"detail"},
    {"from":"disp","to":"out","toPort":"radius"},
    {"from":"tw","to":"out","toPort":"holes"}]}

# --- C) Gyroid lattice: wavy-strut lattice holes, gentle gyroid surface ripple ---
C={"nodes":[
    {"id":"form","type":"form","x":40,"y":40,"params":{"r_bottom":66,"r_top":60,"bulge":6,"bulge_pos":0.5}},
    {"id":"gy","type":"gyroid","x":40,"y":230,"params":{"period_u":7,"period_v":9}},
    {"id":"disp","type":"displace","x":300,"y":90,"params":{"amp":0.06,"mode":1}},
    {"id":"out","type":"output","x":560,"y":150,"params":out(threshold=0.55)}],
   "edges":[
    {"from":"form","to":"disp","toPort":"base"},
    {"from":"gy","to":"disp","toPort":"detail"},
    {"from":"disp","to":"out","toPort":"radius"},
    {"from":"gy","to":"out","toPort":"holes"}]}

INTENT={"Showcase - Perforated Crown":("A voronoi web that only opens in the top ~half; solid lower body.",A),
        "Showcase - Twisted Voronoi":("Voronoi cells sheared into a spiral, same field bumps the wall.",B),
        "Showcase - Gyroid Lattice":("Wavy gyroid-strut lattice holes, slight gyroid surface ripple.",C)}

for name,(intent,G) in INTENT.items():
    v,f=e.build_shade_mesh({"graph":G,"res_theta":200,"res_z":180,"bayonet":1})
    ok,rep=e.verify_mesh(v,f)
    open_cells=None
    print("%-30s comps=%d watertight=%s ok=%s tris=%d  | INTENT: %s"%(
        name,rep["components"],rep["watertight"],ok,rep["tris"],intent))
    with open(os.path.join(PRESETS,name+".json"),"w") as fh:
        json.dump({"shade":{"graph":G,"height":190,"wall":1.2},"base":{}},fh,indent=2)
print("saved presets:", [f for f in os.listdir(PRESETS) if f.startswith("Showcase")])
