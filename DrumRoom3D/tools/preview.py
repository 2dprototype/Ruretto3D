"""
preview.py - optional dev tool: renders the generated OBJ/PNG assets with a tiny numpy rasteriser
so you can eyeball the scene without launching the engine.

    python tools/preview.py                       # writes preview_*.png next to the project
    python tools/preview.py x y z yaw pitch out.png
"""
import math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS, TEX = os.path.join(HERE, "assets", "models"), os.path.join(HERE, "assets", "textures")

def load_obj(name):
    v, vt, vn, tris = [], [], [], []
    for line in open(os.path.join(MODELS, name)):
        p = line.split()
        if not p: continue
        if p[0] == "v": v.append([float(x) for x in p[1:4]])
        elif p[0] == "vt": vt.append([float(x) for x in p[1:3]])
        elif p[0] == "vn": vn.append([float(x) for x in p[1:4]])
        elif p[0] == "f":
            idx = [tuple(int(i) - 1 for i in q.split("/")) for q in p[1:]]
            for k in range(1, len(idx) - 1): tris.append((idx[0], idx[k], idx[k + 1]))
    v, vt, vn = np.array(v), np.array(vt), np.array(vn)
    P = np.array([[v[c[0]] for c in t] for t in tris]); U = np.array([[vt[c[1]] for c in t] for t in tris]); N = np.array([[vn[c[2]] for c in t] for t in tris])
    return P, U, N

def render(items, cam, size=(640, 360), light=None, points=(), ambient=(0.4, 0.38, 0.45), fov=65, bg=(18, 16, 24), unlit_items=()):
    Wd, Ht = size; img = np.zeros((Ht, Wd, 3), float); img[:] = bg; zb = np.full((Ht, Wd), 1e9)
    x, y, z, yaw, pit = cam; yaw, pit = math.radians(yaw), math.radians(pit)
    f = np.array([math.cos(pit)*math.sin(yaw), math.sin(pit), -math.cos(pit)*math.cos(yaw)])
    r = np.array([math.cos(yaw), 0, math.sin(yaw)]); u = np.cross(r, f)
    eye = np.array([x, y, z]); th = math.tan(math.radians(fov)/2); asp = Wd/Ht
    L = None if light is None else (np.array(light[0], float)/np.linalg.norm(light[0]), np.array(light[1], float))
    near = 0.05
    for (name, texname, off, unlit) in items:
        P, U, N = load_obj(name); P = P + np.array(off)
        tex = None if texname is None else np.array(Image.open(os.path.join(TEX, texname)).convert("RGBA")).astype(float)/255
        # per-vertex lighting
        lit = np.zeros(P.shape[:2] + (3,)) + np.array(ambient)
        if L is not None: lit += np.clip(-(N @ L[0]), 0, 1)[..., None]*L[1]
        for (pp, col, rad, inten) in points:
            d = np.array(pp) - P; dist = np.linalg.norm(d, axis=-1); dd = d/np.maximum(dist[..., None], 1e-6)
            att = np.clip(1 - dist/rad, 0, 1)**1.5*inten
            lit += (np.clip((N*dd).sum(-1), 0, 1)*att)[..., None]*np.array(col)
        if unlit: lit[:] = 1
        rel = P - eye; cx = rel @ r; cy = rel @ u; cz = rel @ f
        for t in range(len(P)):
            vs = [(cx[t, i], cy[t, i], cz[t, i], U[t, i, 0], U[t, i, 1], *lit[t, i]) for i in range(3)]
            if all(v[2] < near for v in vs): continue
            poly = vs
            if any(v[2] < near for v in vs):          # clip against near plane
                out = []
                for i in range(3):
                    a, b = vs[i], vs[(i+1) % 3]; ina, inb = a[2] >= near, b[2] >= near
                    if ina: out.append(a)
                    if ina != inb:
                        k = (near - a[2])/(b[2] - a[2]); out.append(tuple(a[j] + (b[j] - a[j])*k for j in range(len(a))))
                poly = out
            for k in range(1, len(poly) - 1): raster(img, zb, tex, (poly[0], poly[k], poly[k+1]), Wd, Ht, th, asp)
    return np.clip(img*255, 0, 255).astype(np.uint8)

def raster(img, zb, tex, tri, Wd, Ht, th, asp):
    sx = [(v[0]/v[2]/(th*asp)*0.5 + 0.5)*Wd for v in tri]; sy = [(0.5 - v[1]/v[2]/th*0.5)*Ht for v in tri]
    x0, x1 = max(int(math.floor(min(sx))), 0), min(int(math.ceil(max(sx))), Wd - 1); y0, y1 = max(int(math.floor(min(sy))), 0), min(int(math.ceil(max(sy))), Ht - 1)
    if x0 > x1 or y0 > y1: return
    den = (sy[1]-sy[2])*(sx[0]-sx[2]) + (sx[2]-sx[1])*(sy[0]-sy[2])
    if abs(den) < 1e-9: return
    px, py = np.meshgrid(np.arange(x0, x1+1) + 0.5, np.arange(y0, y1+1) + 0.5)
    w0 = ((sy[1]-sy[2])*(px-sx[2]) + (sx[2]-sx[1])*(py-sy[2]))/den
    w1 = ((sy[2]-sy[0])*(px-sx[2]) + (sx[0]-sx[2])*(py-sy[2]))/den; w2 = 1 - w0 - w1
    m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
    if not m.any(): return
    iz = [1/v[2] for v in tri]; q = w0*iz[0] + w1*iz[1] + w2*iz[2]; depth = 1/np.maximum(q, 1e-9)
    sub = zb[y0:y1+1, x0:x1+1]; m &= depth < sub - 1e-5
    if not m.any(): return
    def attr(i): return (w0*tri[0][i]*iz[0] + w1*tri[1][i]*iz[1] + w2*tri[2][i]*iz[2])*depth
    col = np.stack([attr(5), attr(6), attr(7)], -1)
    if tex is not None:
        th_, tw_ = tex.shape[:2]; u_ = np.clip(attr(3), 0, 1); v_ = np.clip(attr(4), 0, 1)
        ti = tex[np.clip(((1 - v_)*th_).astype(int), 0, th_-1), np.clip((u_*tw_).astype(int), 0, tw_-1)]
        a = ti[..., 3:4]; base = img[y0:y1+1, x0:x1+1]
        col = ti[..., :3]*col
        sel = m & (a[..., 0] > 0.02)
        blend = np.where((a < 0.999)[..., 0:1], a, 1.0)
        base[sel] = (base[sel]*(1 - blend[sel]) + col[sel]*blend[sel]); sub[sel & (a[..., 0] > 0.999)] = depth[sel & (a[..., 0] > 0.999)]
    else:
        base = img[y0:y1+1, x0:x1+1]; base[m] = col[m]; sub[m] = depth[m]
    return

def kit_items():
    import kit
    items = [("kit_hw.obj", "kit.png", (0, 0, 0), False)]
    for nm in ("kick", "tom1", "tom2", "snare", "floortom"):
        items.append((nm + ".obj", "kit.png", kit.W(kit.DRUMS[nm]["c"]), False))
    items.append(("hat_top.obj", "kit.png", kit.W(kit.HAT["c"]), False))
    items.append(("crash_0.obj", "kit.png", kit.W(kit.CRASH["c"]), False))
    items.append(("ride_0.obj", "kit.png", kit.W(kit.RIDE["c"]), False))
    return items

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    items = kit_items()
    views = {"front": (3.2, 1.45, 4.3, 0, -8), "left34": (1.2, 1.5, 3.9, -30, -10), "right34": (5.2, 1.5, 3.9, 30, -10), "back": (3.3, 1.6, -0.3, 180, -12)}
    lights = dict(light=((0.3, -0.5, -0.8), (0.55, 0.5, 0.45)), points=[((3.2, 2.4, 3.6), (1, 0.95, 0.85), 8, 1.2)])
    for k, c in views.items():
        Image.fromarray(render(items, c, **lights)).save(f"/home/claude/prev_kit_{k}.png"); print("wrote", k)
