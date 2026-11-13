"""Contour mesh for upright A1 shades; numpy only, millimetres.

Every opening is a convex pointed diamond in a staggered rhombus tessellation. Its upper contour rises at least
2.0 mm per mm of circumferential travel; no horizontal roof or floating strand.
Tiles leave a continuous web and connect to solid bottom/top bands. Pattern
fields vary opening size, not topology. Preview and export share the contours.
"""
import math
import numpy as np

MIN_WEB = 1.6                 # four nominal 0.4 mm nozzle widths
ROOF_RISE = 2.0
MAX_RADIAL_SLOPE = 0.55       # reserve slope budget for hole roofs
BUILD_LIMIT = 250.0           # 6 mm margin inside the A1's 256 mm envelope


def constrain_shell(r_out, r_in, z, wall, collar_h):
    """Limit outward growth and compensate radial thickness on sloped surfaces.

Keep the mounting collar's original cross section. The body's shape is projected
onto a bounded vertical slope, starting at the collar. Return adjustment extent.
    """
    if not np.isfinite(r_out).all() or not np.isfinite(r_in).all():
        raise ValueError('Radius fields must contain finite millimetre values.')
    ro = r_out.copy(); ri = r_in.copy()
    for i in range(1, len(z)):
        dz = z[i] - z[i - 1]
        ro[i] = np.clip(ro[i], ro[i - 1] - MAX_RADIAL_SLOPE * dz,
                        ro[i - 1] + MAX_RADIAL_SLOPE * dz)
    drdz = np.gradient(ro, z, axis=0)
    drdt = (np.roll(ro, -1, axis=1) - np.roll(ro, 1, axis=1)) / (4 * math.pi / ro.shape[1])
    gap = wall * np.sqrt(1 + drdz ** 2 + (drdt / np.maximum(ro, 1)) ** 2)
    body = z >= collar_h
    ri[body] = ro[body] - gap[body]
    # Inward growth of material on the inner skin must also be supported. This
    # includes the locking-pocket roof; its entry dimensions at z=0 are preserved.
    for i in range(1, len(z)):
        ri[i] = np.maximum(ri[i], ri[i - 1] - MAX_RADIAL_SLOPE * (z[i] - z[i - 1]))
    if np.any(ri <= 0) or np.any(ro - ri < 0.79):
        raise ValueError('Shape/collar cannot maintain a 0.8 mm wall within the support-free slope limit.')
    return ro, ri, float(np.max(np.abs(ro - r_out)))


def contour_mesh(r_out, r_in, z, height, collar_h, top_band, cols, rows, openness, seed, style, web_mm=MIN_WEB, refinement=2, hole_mm=3.2, distribution="uniform"):
    """Triangulate rhombus tiles around exact diamond contours, then refine.

openness is a (rows, cols) field. Values near zero leave tiles solid. Variation
never creates disconnected islands or moves the pointed roof sideways.
    """
    web_mm = 1.2 * max(MIN_WEB, float(web_mm))  # clearance reserve for the flow shear
    cols = max(4, min(120 if style == "micro_round" else 40, int(cols))); rows = max(2, min(60 if style == "micro_round" else 30, int(rows)))
    lo = max(collar_h + 3.2, 3.2); hi = height - max(top_band, MIN_WEB)
    if hi - lo < 8:
        raise ValueError('Not enough height between collar and rim for pointed perforations.')
    pitch = (hi - lo) / rows
    uvtris = []
    hole_count = 0
    rng = np.random.default_rng(int(seed) & 0x7fffffff)

    def radius_at(u, zz, field):
        fi = np.searchsorted(z, zz, side='right') - 1
        fi = np.clip(fi, 0, len(z) - 2)
        wz = (zz - z[fi]) / (z[fi + 1] - z[fi])
        tj = np.mod(u, 1.) * field.shape[1]
        j = np.floor(tj).astype(int); wt = tj - j
        a = field[fi, j % field.shape[1]] * (1 - wt) + field[fi, (j + 1) % field.shape[1]] * wt
        b = field[fi + 1, j % field.shape[1]] * (1 - wt) + field[fi + 1, (j + 1) % field.shape[1]] * wt
        return a * (1 - wz) + b * wz

    def clip_triangle(triangle):
        poly = list(triangle)
        for bound, lower in ((lo, True), (hi, False)):
            result=[]
            for a,b in zip(poly, poly[1:]+poly[:1]):
                ina = a[1]>=bound if lower else a[1]<=bound
                inb = b[1]>=bound if lower else b[1]<=bound
                if ina: result.append(a)
                if ina != inb:
                    result.append(a+(b-a)*((bound-a[1])/(b[1]-a[1])))
            poly=result
            if len(poly)<3:return
        for i in range(1,len(poly)-1):
            tri=np.array([poly[0],poly[i],poly[i+1]])
            if abs(np.linalg.det(np.stack([tri[1]-tri[0],tri[2]-tri[0]])))>1e-12:
                uvtris.append(tri)

    # Rhombus tiles tessellate without the broad solid corners of rectangular
    # aperture cells. Adjacent rows shift half a cell: the remaining material
    # forms two continuous crossing rib families, not separate punched panels.
    for row in range(-1, rows+1):
        cz=lo+(row+.5)*pitch
        for col in range(cols):
            cu=(col + .5*(row%2))/cols; hu=.5/cols
            outer=np.array([[cu,cz-pitch],[cu+hu*.5,cz-pitch*.5],
                [cu+hu,cz],[cu+hu*.5,cz+pitch*.5],[cu,cz+pitch],
                [cu-hu*.5,cz+pitch*.5],[cu-hu,cz],[cu-hu*.5,cz-pitch*.5]])
            # Conservative radius over the complete tile bounds, including the
            # source grid's extrema. This makes the strut clearance physical.
            iz=np.flatnonzero((z>=max(0,cz-pitch))&(z<=min(height,cz+pitch)))
            if not len(iz): iz=np.array([int(np.clip(np.searchsorted(z,cz),0,len(z)-1))])
            js=np.arange(math.floor((cu-hu)*r_in.shape[1]),math.ceil((cu+hu)*r_in.shape[1])+1)%r_in.shape[1]
            rad=float(r_in[np.ix_(iz,js)].min())
            hw=2*math.pi*rad*hu
            inradius=hw*pitch/math.sqrt(hw*hw+pitch*pitch)
            amount=float(openness[np.clip(row,0,rows-1),col])
            if style=='voronoi':
                amount*=rng.uniform(.85,1.)*(.72+.28*math.sin(math.pi*(np.clip(row,0,rows-1)+.5)/rows))
            elif style=='gyroid':
                amount*=.93+.07*math.cos(2*math.pi*(col/cols+row/rows))
            # A minimum normal gap between adjacent parallel diamond edges.
            amount=min(amount,1-web_mm/(2*inradius),.94)
            # Upper halves rise steeply; global flow below has its own bounded
            # tangential slope budget. No opening crosses a solid rim boundary.
            compression=min(1.,pitch/(ROOF_RISE*hw))
            if hw*amount*compression<.8 or amount<.15 or cz-amount*pitch<lo+web_mm or cz+amount*pitch>hi-web_mm:
                for k in range(8):clip_triangle(np.array([outer[k],outer[(k+1)%8],[cu,cz]]))
                continue
            hole_count+=1
            inner=np.array([cu,cz])+(outer-np.array([cu,cz]))*amount
            inner[:,0]=cu+(inner[:,0]-cu)*compression
            if style == 'micro_round':
                # Rounded lower half, steep crown: small-hole visual character
                # without the unsupported final arc of a true horizontal circle.
                factor=1.
                if distribution=='graded':factor=.58+.42*math.sin(math.pi*(np.clip(row,0,rows-1)+.5)/rows)**2
                elif distribution=='botanical':factor=.62+.38*(.5+.5*math.sin(2*math.pi*(col/cols*3-row/rows)))
                radius=min(float(hole_mm)*.5*factor,hw*.48,(pitch-web_mm)*.28)
                if radius<.65:
                    for k in range(8):clip_triangle(np.array([outer[k],outer[(k+1)%8],[cu,cz]]))
                    hole_count-=1
                    continue
                # Keep inside the tile's original printable diamond so clearances
                # and common outer edges remain valid. The upper crown rises 2:1.
                half_u=radius/(2*math.pi*rad)
                center=cz-radius*.5
                inner=np.array([[cu,center-radius],[cu+half_u*.5,center-radius*.866],
                    [cu+half_u,center],[cu+half_u*.5,center+radius],
                    [cu,center+2*radius],[cu-half_u*.5,center+radius],
                    [cu-half_u,center],[cu-half_u*.5,center-radius*.866]])
            for k in range(8):
                n=(k+1)%8
                clip_triangle(np.array([outer[k],outer[n],inner[n]]))
                clip_triangle(np.array([outer[k],inner[n],inner[k]]))
    if not hole_count:
        raise ValueError('Requested cells leave no printable openings; reduce cells up or increase height.')
    # Join the irregular clipped tile boundary to filled mounting/top bands,
    # using exactly the same edges. Subdivide everything together afterward.
    t=np.round(np.asarray(uvtris,float),8)
    pts=t.reshape(-1,2).copy();pts[:,0]=np.mod(pts[:,0],1.)
    uv0,inv0=np.unique(np.round(pts,8),axis=0,return_inverse=True)
    f0=inv0.reshape(-1,3)
    ee=np.concatenate([f0[:,[0,1]],f0[:,[1,2]],f0[:,[2,0]]])
    _,ix,cnt=np.unique(np.sort(ee,axis=1),axis=0,return_index=True,return_counts=True)
    for a,b in ee[ix[cnt==1]]:
        pa,pb=uv0[a].copy(),uv0[b].copy()
        if abs(pa[0]-pb[0])>.5:
            if pa[0]<pb[0]:pa[0]+=1
            else:pb[0]+=1
        if abs(pa[1]-lo)<1e-7 and abs(pb[1]-lo)<1e-7:
            levels=np.linspace(0,lo,max(4,int(lo/1.5)+1))
        elif abs(pa[1]-hi)<1e-7 and abs(pb[1]-hi)<1e-7:
            levels=np.linspace(hi,height,max(3,int((height-hi)/2)+1))
        else:continue
        left,right=sorted([pa[0],pb[0]])
        for z0,z1 in zip(levels[:-1],levels[1:]):
            a0,b0,c0,d0=np.array([[left,z0],[right,z0],[right,z1],[left,z1]])
            uvtris.extend([[a0,b0,c0],[a0,c0,d0]])
    t = np.round(np.asarray(uvtris, float),8)
    # Uniform refinement preserves shared edges; geometry resolution no longer
    # decides which strands survive. Quality refines the curved host surface.
    for _ in range(int(refinement)):
        a,b,c=t[:,0],t[:,1],t[:,2]; ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
        t=np.concatenate([np.stack([a,ab,ca],1),np.stack([ab,b,bc],1),
                          np.stack([ca,bc,c],1),np.stack([ab,bc,ca],1)])
    points=t.reshape(-1,2)
    # Shear the entire tessellation continuously. The same map is applied to
    # every shared edge. Bound circumferential travel to 0.30 mm per mm rise.
    # The 20% web reserve above covers the corresponding shear contraction.
    turns=.30*(hi-lo)/(2*math.pi*float(r_out.max()))
    if style=='gyroid':
        phase=np.clip((points[:,1]-lo)/(hi-lo),0.,1.)
        flow=turns*(.65*phase+.04*np.sin(2*math.pi*phase))
    elif style in ('grid','dots','honeycomb','micro_round'):
        flow=np.zeros(len(points))
    elif style=='voronoi':
        phase=np.clip((points[:,1]-lo)/(hi-lo),0.,1.)
        flow=-turns*.75*phase
    else:
        flow=turns*np.clip((points[:,1]-lo)/(hi-lo),0.,1.)
    points[:,0]=np.mod(points[:,0]+flow,1.)
    uv, inv=np.unique(np.round(points,8),axis=0,return_inverse=True)
    f=inv.reshape(-1,3); u=uv[:,0]; zz=uv[:,1]
    theta=2*math.pi*u
    ro=radius_at(u,zz,r_out); ri=radius_at(u,zz,r_in)
    out=np.column_stack([ro*np.cos(theta),ro*np.sin(theta),zz])
    inn=np.column_stack([ri*np.cos(theta),ri*np.sin(theta),zz]); n=len(uv)
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    keys=np.sort(edges,axis=1)
    _,idx,counts=np.unique(keys,axis=0,return_index=True,return_counts=True)
    e=edges[idx[counts==1]]; a=e[:,0];b=e[:,1]
    rims=np.concatenate([np.column_stack([a,a+n,b+n]),np.column_stack([a,b+n,b])])
    faces=np.concatenate([f,f[:,::-1]+n,rims])
    return np.concatenate([out,inn]).astype(np.float32), faces.astype(np.int32)


def manufacturing_report(verts, faces):
    """Geometric screen, not a slicer/physical-print certification.

Undersides above the bed must rise within 45 degrees from vertical. This screen
also catches collar ledges, sharp decorative ridges and roofs, not just holes.
    """
    tri=verts[faces].astype(float)
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    xy=np.linalg.norm(normal[:,:2],axis=1)
    bed=np.max(tri[:,:,2],axis=1)<.01
    unsupported=(normal[:,2]<-1e-8)&(~bed)&(-normal[:,2]>xy*1.001)
    size=np.ptp(verts,axis=0)
    errors=[]
    if np.any(size>BUILD_LIMIT+1e-3):errors.append('Model exceeds the 250 mm A1 design envelope.')
    if unsupported.any():errors.append('%d underside triangles exceed the upright 45° overhang limit.'%unsupported.sum())
    return {'passed':not errors,'errors':errors,'unsupported_triangles':int(unsupported.sum()),
            'size_mm':size.tolist(),'orientation':'upright Z','nozzle_mm':.4,
            'minimum_web_mm':MIN_WEB,'roof_rise':ROOF_RISE,'slicer_verified':False}


def measure_features(verts, faces, collar_h=0.):
    """Measure 3D separation of distinct aperture contours and estimate skin wall.

The web result is the minimum exact segment-to-segment distance between the
triangulated outer and inner aperture contours, including diagonal neighbours.
Normal wall projection is an estimate, not a full medial-axis thickness test.
Requires the engine's paired outer/inner vertex layout.
    """
    n=len(verts)//2
    outer=faces[np.all(faces<n,axis=1)]
    tr=verts[outer].astype(float)
    nn=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0])
    lengths=np.linalg.norm(nn,axis=1)
    good=(lengths>1e-9)&(tr[:,:,2].min(axis=1)>collar_h+2.)
    gaps=(verts[outer]-verts[outer+n]).mean(axis=1)
    normal_wall=np.einsum('ij,ij->i',gaps[good],nn[good]/lengths[good,None])
    wall=float(normal_wall.min()) if len(normal_wall) else None
    e=np.concatenate([outer[:,[0,1]],outer[:,[1,2]],outer[:,[2,0]]])
    _,idx,cnt=np.unique(np.sort(e,axis=1),axis=0,return_index=True,return_counts=True)
    e=e[idx[cnt==1]]
    # Exclude only the top and bottom shell boundaries; all remaining closed
    # loops are aperture contours in a validated engine mesh.
    zz=verts[e,2]
    e=e[~((np.abs(zz).max(axis=1)<1e-6)|(np.abs(zz-verts[:,2].max()).max(axis=1)<1e-6))]
    parent={int(x):int(x) for x in e.ravel()}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    for a,b in e:parent[find(int(a))]=find(int(b))
    loops={}
    for a,b in e:loops.setdefault(find(int(a)),[]).append([int(a),int(b)])
    segments=[verts[np.asarray(edges)].astype(float) for edges in loops.values()]
    boxes=[(v.min(axis=(0,1)),v.max(axis=(0,1))) for v in segments]
    best=float('inf')
    def distance(p,q):
        p0=p[:,0,None,:];q0=q[None,:,0,:]
        u=p[:,1,None,:]-p0;v=q[None,:,1,:]-q0;w=p0-q0
        a=(u*u).sum(-1);b=(u*v).sum(-1);c=(v*v).sum(-1)
        d=(u*w).sum(-1);ee=(v*w).sum(-1);den=a*c-b*b
        ss=np.divide(b*ee-c*d,den,out=np.zeros_like(den),where=den>1e-14)
        tt=np.divide(a*ee-b*d,den,out=np.zeros_like(den),where=den>1e-14)
        interior=(den>1e-14)&(ss>=0)&(ss<=1)&(tt>=0)&(tt<=1)
        dd=np.where(interior,((w+ss[...,None]*u-tt[...,None]*v)**2).sum(-1),np.inf)
        for s0 in (0.,1.):
            t0=np.clip((ee+s0*b)/c,0,1)
            dd=np.minimum(dd,((w+s0*u-t0[...,None]*v)**2).sum(-1))
        for t0 in (0.,1.):
            s0=np.clip((t0*b-d)/a,0,1)
            dd=np.minimum(dd,((w+s0[...,None]*u-t0*v)**2).sum(-1))
        return float(np.sqrt(dd.min()))
    for skin in (0,n):
        segments=[verts[np.asarray(edges)+skin].astype(float) for edges in loops.values()]
        boxes=[(v.min(axis=(0,1)),v.max(axis=(0,1))) for v in segments]
        for i,p in enumerate(segments):
            for j in range(i):
                lo=np.maximum(boxes[i][0]-boxes[j][1],boxes[j][0]-boxes[i][1])
                if np.linalg.norm(np.maximum(lo,0))>=best:continue
                best=min(best,distance(p,segments[j]))
    return {'minimum_aperture_clearance_mm':None if not math.isfinite(best) else best,
            'minimum_normal_wall_estimate_mm':wall,'aperture_count':len(segments),
            'wall_method':'paired facet normal projection; not medial-axis analysis'}
