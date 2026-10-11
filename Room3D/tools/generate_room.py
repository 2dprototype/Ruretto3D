#!/usr/bin/env python3
"""
Room3D - procedural room generator for the Crayon Engine
=========================================================
Builds every model (.obj) and texture (.png) of a small Japanese-style bedroom
(desk + CRT, chair, bookshelf, window with curtain, bed, speakers, ...), arranges
them in world space, and writes the collision boxes into main.lua.

    pip install pillow numpy
    python tools/generate_room.py

World: Y up. Room spans x 0..6 (left wall x=0), z 0..5 (window wall z=0), height 2.6.
"""
import math, os, random, re
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS, TEXTURES = (os.path.join(ROOT, "assets", d) for d in ("models", "textures"))
os.makedirs(MODELS, exist_ok=True); os.makedirs(TEXTURES, exist_ok=True)
random.seed(3); np.random.seed(3)
W, D, H = 6.0, 5.0, 2.6
FLIP_V = False       # set True if textures appear upside-down in your build

# ----------------------------------------------------------------------------- math
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vadd(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vmul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def vcross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vdot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def vlen(a): return math.sqrt(vdot(a, a))
def vnorm(a):
    l = vlen(a); return (a[0]/l, a[1]/l, a[2]/l) if l > 1e-12 else (0, 1, 0)
I3 = ((1,0,0),(0,1,0),(0,0,1))
def rotY(a): c, s = math.cos(a), math.sin(a); return ((c,0,s),(0,1,0),(-s,0,c))
def rotZ(a): c, s = math.cos(a), math.sin(a); return ((c,-s,0),(s,c,0),(0,0,1))
def rotX(a): c, s = math.cos(a), math.sin(a); return ((1,0,0),(0,c,-s),(0,s,c))
def mv(R, p): return tuple(R[i][0]*p[0] + R[i][1]*p[1] + R[i][2]*p[2] for i in range(3))

# ----------------------------------------------------------------------------- palette
PAL = ["cream", "plastic", "navy", "black", "dgrey", "metal", "chrome", "green", "mug", "penblue", "red", "yellow",
       "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "cardboard", "whitebox", "slipper", "glass",
       "bulb", "spkgrey", "navybox", "pinkbox", "rubber", "ac", "acvent", "pillow", "rod", "bin", "paper", "deskpanel", "base"]
PAL_HEX = ["#e8e0d4", "#d9d2c5", "#1d2440", "#1b1b1f", "#3a3a42", "#9aa0a8", "#c8ccd2", "#3f8f3a", "#d9a52b", "#243a8a",
           "#c0392b", "#e0b800", "#26334f", "#6b2a2a", "#2f4a33", "#b59b6b", "#4d5f78", "#9a4b36", "#6f7a3a", "#2b211c",
           "#c9a77c", "#e6e2da", "#2a2220", "#0d1012", "#fff2b0", "#8a8a8c", "#1a2745", "#d8b8a0", "#101010", "#ddd5cc",
           "#2a2a2a", "#f1ece4", "#b5b9c0", "#cbb9a2", "#f1efe8", "#232a3a", "#ccc4b6"]
CI = {n: i for i, n in enumerate(PAL)}
def cell_uv(name):
    i = CI[name]; return ((i % 8 + 0.5) / 8, 1 - (i // 8 + 0.5) / 8)

# ----------------------------------------------------------------------------- mesh
class Mesh:
    def __init__(self):
        self.v, self.vt, self.vn, self.f = [], [], [], []
        self._v, self._vt, self._vn = {}, {}, {}
        self.stack, self.fixed = [], None
    def _idx(self, tab, lst, val):
        k = tuple(round(x, 5) for x in val)
        if k not in tab: lst.append(val); tab[k] = len(lst)
        return tab[k]
    def tri(self, a, b, c):
        pts = []
        for p, n, uv in (a, b, c):
            for R, t in reversed(self.stack):
                p = vadd(mv(R, p), t); n = mv(R, n)
            if self.fixed: uv = self.fixed
            pts.append((p, vnorm(n), uv))
        a, b, c = pts
        gn = vcross(vsub(b[0], a[0]), vsub(c[0], a[0]))
        if vlen(gn) < 1e-10: return
        if vdot(gn, vadd(vadd(a[1], b[1]), c[1])) < 0: b, c = c, b
        ids = []
        for p, n, uv in (a, b, c):
            if FLIP_V: uv = (uv[0], 1 - uv[1])
            ids.append((self._idx(self._v, self.v, p), self._idx(self._vt, self.vt, uv), self._idx(self._vn, self.vn, n)))
        self.f.append(ids)
    def quad(self, a, b, c, d): self.tri(a, b, c); self.tri(a, c, d)
    def save(self, name):
        with open(os.path.join(MODELS, name), "w") as fh:
            fh.write(f"# Room3D {name}\n")
            for p in self.v: fh.write("v %.5f %.5f %.5f\n" % p)
            for t in self.vt: fh.write("vt %.5f %.5f\n" % t)
            for n in self.vn: fh.write("vn %.5f %.5f %.5f\n" % n)
            for f in self.f: fh.write("f " + " ".join(f"{a}/{b}/{c}" for a, b, c in f) + "\n")
        print("  model", name, len(self.f), "tris")

@contextmanager
def placed(m, R=I3, t=(0, 0, 0)):
    m.stack.append((R, t)); yield; m.stack.pop()
@contextmanager
def colored(m, name):
    old = m.fixed; m.fixed = cell_uv(name); yield; m.fixed = old

def box(m, c, h, yaw=0.0, uv=None):
    R = rotY(yaw)
    faces = [((1,0,0), ((1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1))), ((-1,0,0), ((-1,-1,1),(-1,-1,-1),(-1,1,-1),(-1,1,1))),
             ((0,1,0), ((-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1))), ((0,-1,0), ((-1,-1,1),(1,-1,1),(1,-1,-1),(-1,-1,-1))),
             ((0,0,1), ((-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))), ((0,0,-1), ((1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1)))]
    for fi, (nrm, cs) in enumerate(faces):
        pts = []
        for j, q in enumerate(cs):
            p = mv(R, (q[0]*h[0], q[1]*h[1], q[2]*h[2])); pos = vadd(c, p)
            u, v = [(0,0),(1,0),(1,1),(0,1)][j]
            if uv and fi in uv: u, v = uv[fi](u, v)
            pts.append((pos, mv(R, nrm), (u, v)))
        m.quad(*pts)

def pbox(m, name, c, h, yaw=0.0):
    with colored(m, name): box(m, c, h, yaw)

def lathe(m, profile, seg=32, flip=1, crease=45):
    n = len(profile) - 1; segn = []
    for i in range(n):
        dr, dy = profile[i+1][0]-profile[i][0], profile[i+1][1]-profile[i][1]
        l = math.hypot(dr, dy) or 1e-9; segn.append((flip*dy/l, -flip*dr/l))
    def pn(i, side):
        a = segn[side]; o = side-1 if i == side else side+1
        if 0 <= o < n:
            b = segn[o]
            if a[0]*b[0]+a[1]*b[1] > math.cos(math.radians(crease)):
                mm = (a[0]+b[0], a[1]+b[1]); l = math.hypot(*mm) or 1; return (mm[0]/l, mm[1]/l)
        return a
    for s in range(n):
        for k in range(seg):
            p0, p1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
            def V(i, side, p, kk):
                r, y = profile[i]; nr, ny = pn(i, side)
                return ((r*math.cos(p), y, -r*math.sin(p)), (nr*math.cos(p), ny, -nr*math.sin(p)), (kk/seg, i/max(1, n)))
            m.quad(V(s, s, p0, k), V(s, s, p1, k+1), V(s+1, s, p1, k+1), V(s+1, s, p0, k))

def cyl(m, name, r, y0, y1, seg=24):
    with colored(m, name): lathe(m, [(0, y0), (r, y0), (r, y1), (0, y1)], seg, 1, 30)

def sphere(m, name, c, r, seg=16, rings=10):
    with colored(m, name):
        for i in range(rings):
            t0, t1 = math.pi*i/rings, math.pi*(i+1)/rings
            for k in range(seg):
                p0, p1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
                def V(t, p):
                    n = (math.sin(t)*math.cos(p), math.cos(t), -math.sin(t)*math.sin(p))
                    return (vadd(c, vmul(n, r)), n, (0, 0))
                m.quad(V(t0, p0), V(t0, p1), V(t1, p1), V(t1, p0))

def torus(m, name, R, tube, seg=32, ring=8):
    prof = [(R + tube*math.cos(2*math.pi*i/ring), tube*math.sin(2*math.pi*i/ring)) for i in range(ring+1)]
    with colored(m, name): lathe(m, prof, seg, 1, 180)

def tube(m, name, p0, p1, r, seg=10):
    a = vsub(p1, p0); L = vlen(a); ax = vnorm(a)
    h = (0, 1, 0) if abs(ax[1]) < 0.9 else (1, 0, 0)
    u = vnorm(vcross(ax, h)); w = vcross(ax, u)
    with colored(m, name):
        for k in range(seg):
            a0, a1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
            def ring(ang, base):
                n = vadd(vmul(u, math.cos(ang)), vmul(w, math.sin(ang)))
                return (vadd(base, vmul(n, r)), n, (0, 0))
            m.quad(ring(a0, p0), ring(a1, p0), ring(a1, p1), ring(a0, p1))
            for base, nn in ((p0, vmul(ax, -1)), (p1, ax)):
                m.tri((base, nn, (0, 0)), (ring(a0, base)[0], nn, (0, 0)), (ring(a1, base)[0], nn, (0, 0)))

def planar(m, pts, n, uvf):
    m.quad(*[(p, n, uvf(p)) for p in pts])

COLLIDERS = []
def collider(x0, z0, x1, z1): COLLIDERS.append((x0, z0, x1, z1))

# ----------------------------------------------------------------------------- textures
def save(img, name): img.save(os.path.join(TEXTURES, name)); print("  texture", name, img.size)
def tfont(sz):
    for f in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf"):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()

def blotch(w, h, scale, amp):
    small = np.random.rand(max(2, h // scale), max(2, w // scale)) * 255
    return (np.array(Image.fromarray(small.astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float) / 255 - 0.5) * amp

def tex_plaster(name, base):
    w = 512
    n = blotch(w, w, 64, 26) + blotch(w, w, 8, 12) + np.random.randn(w, w) * 4
    a = np.clip(np.array(base, float)[None, None, :] + n[:, :, None], 0, 255).astype(np.uint8)
    save(Image.fromarray(a, "RGB"), name)

def tex_wood(name, base):
    w = 512; y = np.arange(w)[:, None]; x = np.arange(w)[None, :]
    g = np.sin(x * 0.07 + np.sin(y * 0.02) * 3) * 0.5 + np.sin(x * 0.29) * 0.15 + np.random.randn(w, w) * 0.08
    a = np.clip(np.array(base, float)[None, None, :] * (1 + g[:, :, None] * 0.3), 0, 255).astype(np.uint8)
    save(Image.fromarray(a, "RGB").filter(ImageFilter.GaussianBlur(0.5)), name)

def tex_floor():
    S = 1024; im = Image.new("RGB", (S, S)); d = ImageDraw.Draw(im)
    strips = 40; sh = S // strips
    for r in range(strips):
        x = -random.randint(0, 300)
        while x < S:
            ln = random.randint(180, 330); f = random.uniform(0.82, 1.12)
            col = tuple(int(c * f) for c in (150, 92, 54))
            d.rectangle([x, r * sh, x + ln - 2, r * sh + sh - 2], fill=col)
            x += ln
    a = np.array(im).astype(float)
    yy = np.arange(S)[:, None]
    grain = np.sin(np.arange(S)[None, :] * 0.05 + yy * 0.3) * 6 + np.random.randn(S, S) * 5
    a += grain[:, :, None]
    save(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"), "floor.png")

def tex_palette():
    im = Image.new("RGB", (128, 128)); d = ImageDraw.Draw(im)
    for i, hx in enumerate(PAL_HEX):
        x, y = (i % 8) * 16, (i // 8) * 16
        d.rectangle([x, y, x + 15, y + 15], fill=hx)
    save(im, "palette.png")

def tex_calendar():
    w, h = 256, 400; im = Image.new("RGB", (w, h), (244, 241, 232)); d = ImageDraw.Draw(im)
    for y in range(230):                                   # dusk sky
        t = y / 230; d.line([(0, y), (w, y)], fill=(int(60 + 190*t), int(80 + 90*t), int(150 - 40*t)))
    d.polygon([(10, 190), (90, 95), (112, 82), (134, 95), (230, 190)], fill=(70, 40, 60))
    d.polygon([(100, 100), (112, 82), (124, 100), (112, 108)], fill=(245, 240, 235))
    d.polygon([(40, 190), (112, 108), (190, 190)], fill=(150, 60, 55))
    for cx, cy in ((50, 190), (130, 200), (200, 195), (90, 210)):
        d.ellipse([cx - 60, cy - 14, cx + 60, cy + 14], fill=(240, 220, 225))
    f = tfont(13); fs = tfont(10)
    d.text((100, 238), "OCTOBER", fill=(40, 40, 40), font=f)
    n = 1
    for r in range(6):
        for c in range(7):
            x, y = 14 + c * 33, 262 + r * 22
            d.rectangle([x, y, x + 31, y + 20], outline=(150, 150, 150))
            if (r > 0 or c > 2) and n <= 31: d.text((x + 6, y + 4), str(n), fill=(70, 70, 70), font=fs); n += 1
    d.rectangle([0, 0, w - 1, h - 1], outline=(60, 50, 40), width=3)
    save(im, "calendar.png")

def tex_curtain():
    w = 256; x = np.linspace(0, 1, w)[None, :]; y = np.linspace(0, 1, w)[:, None]
    g = 0.86 + 0.14 * np.sin(x * 2 * math.pi * 7) + y * 0 + np.random.randn(w, w) * 0.01
    a = np.clip(np.array((236, 232, 222), float)[None, None, :] * g[:, :, None], 0, 255).astype(np.uint8)
    save(Image.fromarray(a, "RGB"), "curtain.png")

def tex_mattress():
    w = 256; im = Image.new("RGB", (w, w), (206, 200, 190)); d = ImageDraw.Draw(im)
    for k in range(0, w, 32): d.line([(k, 0), (k, w)], fill=(188, 182, 172)); d.line([(0, k), (w, k)], fill=(188, 182, 172))
    save(im, "mattress.png")

def tex_speaker():
    S = 256; im = Image.new("RGB", (S, S), (214, 206, 192)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=(150, 142, 130), width=6)
    for cx, cy, r in ((128, 66, 36), (128, 176, 66)):
        d.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=(120, 120, 124))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(34, 34, 38))
        d.ellipse([cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55], fill=(60, 60, 66))
        d.ellipse([cx - r * .2, cy - r * .2, cx + r * .2, cy + r * .2], fill=(150, 150, 154))
    save(im, "speaker.png")

def tex_crate():
    S = 128; im = Image.new("RGB", (S, S), (226, 220, 208)); d = ImageDraw.Draw(im)
    d.rectangle([30, 36, 44, 50], fill=(70, 70, 76)); d.rectangle([84, 36, 98, 50], fill=(70, 70, 76))
    d.rounded_rectangle([44, 76, 84, 90], radius=4, fill=(70, 70, 76))
    save(im, "crate_face.png")

def tex_glow():
    w = 128; y = np.linspace(0, 1, w)[:, None] * np.ones((w, w))
    r = np.full((w, w), 255.0); g = 246 - 56 * y; b = 214 - 100 * y
    save(Image.fromarray(np.stack([r, g, b], -1).astype(np.uint8), "RGB"), "glow.png")

def tex_sunpatch():
    S = 512; a = np.zeros((S, S, 4), np.uint8); a[:, :] = (255, 176, 84, 150)
    im = Image.fromarray(a, "RGBA"); d = ImageDraw.Draw(im)
    for c in (1, 2): d.line([(c * S // 3, 0), (c * S // 3, S)], fill=(255, 176, 84, 0), width=10)
    for r in range(1, 5): d.line([(0, r * S // 5), (S, r * S // 5)], fill=(255, 176, 84, 0), width=10)
    im = im.filter(ImageFilter.GaussianBlur(5))
    arr = np.array(im); arr[:6, :, 3] = 0; arr[-6:, :, 3] = 0; arr[:, :6, 3] = 0; arr[:, -6:, 3] = 0
    save(Image.fromarray(arr, "RGBA"), "sunpatch.png")

# ----------------------------------------------------------------------------- scene
WX0, WX1, WY0, WY1 = 2.6, 4.6, 0.9, 1.9          # window opening on the z=0 wall
SUN = (0.35, -0.55, 0.75)

def build_walls():
    warm, cool = Mesh(), Mesh()
    up, dn = (0, 1, 0), (0, -1, 0)
    # left wall (x=0): faces +x
    planar(warm, [(0,0,D),(0,0,0),(0,H,0),(0,H,D)], (1,0,0), lambda p: (1 - p[2]/D, p[1]/H))
    planar(warm, [(0,H,0),(W,H,0),(W,H,D),(0,H,D)], dn, lambda p: (p[0]/W, p[2]/D))    # ceiling
    # window wall (z=0) with an opening
    for x0, x1, y0, y1 in ((0, WX0, 0, H), (WX1, W, 0, H), (WX0, WX1, 0, WY0), (WX0, WX1, WY1, H)):
        planar(cool, [(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)], (0,0,1), lambda p: (p[0]/W, p[1]/H))
    dpt = 0.12                                                                       # window reveal
    box(cool, ((WX0+WX1)/2, WY0 - 0.02, -dpt/2), ((WX1-WX0)/2, 0.02, dpt/2))
    box(cool, ((WX0+WX1)/2, WY1 + 0.02, -dpt/2), ((WX1-WX0)/2, 0.02, dpt/2))
    box(cool, (WX0 - 0.02, (WY0+WY1)/2, -dpt/2), (0.02, (WY1-WY0)/2, dpt/2))
    box(cool, (WX1 + 0.02, (WY0+WY1)/2, -dpt/2), (0.02, (WY1-WY0)/2, dpt/2))
    planar(cool, [(W,0,0),(W,0,D),(W,H,D),(W,H,0)], (-1,0,0), lambda p: (p[2]/D, p[1]/H))      # right wall
    planar(cool, [(W,0,D),(0,0,D),(0,H,D),(W,H,D)], (0,0,-1), lambda p: (1 - p[0]/W, p[1]/H))  # front wall
    warm.save("walls_warm.obj"); cool.save("walls_cool.obj")

def build_floor():
    m = Mesh()
    planar(m, [(0,0,D),(W,0,D),(W,0,0),(0,0,0)], (0,1,0), lambda p: (p[0]/W, 1 - p[2]/D)); m.save("floor.obj")

def build_window_and_wood():
    brown = Mesh(); orange = Mesh(); glow = Mesh()
    dz = -0.07
    # window frame, mullions and sill
    cx, cy = (WX0+WX1)/2, (WY0+WY1)/2
    box(brown, (cx, WY0 + 0.025, dz), ((WX1-WX0)/2 + 0.04, 0.03, 0.05)); box(brown, (cx, WY1 - 0.025, dz), ((WX1-WX0)/2 + 0.04, 0.03, 0.05))
    box(brown, (WX0 + 0.025, cy, dz), (0.03, (WY1-WY0)/2, 0.05)); box(brown, (WX1 - 0.025, cy, dz), (0.03, (WY1-WY0)/2, 0.05))
    for x in (WX0 + 0.62, WX0 + 1.3): box(brown, (x, cy, dz), (0.02, (WY1-WY0)/2, 0.04))
    for y in (1.1, 1.3, 1.5, 1.7): box(brown, (cx, y, dz), ((WX1-WX0)/2, 0.015, 0.04))
    box(brown, (cx, WY0 - 0.045, 0.06), ((WX1-WX0)/2 + 0.12, 0.025, 0.14))
    planar(glow, [(WX0,WY0,-0.1),(WX1,WY0,-0.1),(WX1,WY1,-0.1),(WX0,WY1,-0.1)], (0,0,1), lambda p: ((p[0]-WX0)/(WX1-WX0), (p[1]-WY0)/(WY1-WY0)))
    glow.save("window_glow.obj")

    # ---- desk (left wall) : orange top + drawers, navy side panel
    dx0, dx1, dz0, dz1 = 0.02, 0.72, 1.3, 3.0
    box(orange, ((dx0+dx1)/2, 0.72, (dz0+dz1)/2), ((dx1-dx0)/2, 0.02, (dz1-dz0)/2))
    box(orange, (0.37, 0.36, 1.53), (0.33, 0.35, 0.22))                                  # drawer carcass
    for i in range(3):
        box(orange, (0.72, 0.12 + i * 0.22, 1.53), (0.015, 0.1, 0.2))                    # drawer fronts
    box(orange, (0.36, 0.45, 2.98), (0.33, 0.25, 0.015))                                 # modesty panel
    collider(0.0, 1.3, 0.75, 3.0)
    # ---- bookshelf (back wall)
    bx0, bx1, bz0, bz1 = 0.8, 1.6, 0.02, 0.38
    for x in (bx0 + 0.015, bx1 - 0.015): box(brown, (x, 0.9, (bz0+bz1)/2), (0.015, 0.9, (bz1-bz0)/2))
    for y in (0.03, 0.55, 1.05, 1.45, 1.79): box(brown, ((bx0+bx1)/2, y, (bz0+bz1)/2), ((bx1-bx0)/2, 0.015, (bz1-bz0)/2))
    box(brown, ((bx0+bx1)/2, 0.9, bz0 + 0.01), ((bx1-bx0)/2, 0.9, 0.01))
    collider(bx0, 0.0, bx1, bz1 + 0.05)
    # ---- bed (back wall, right corner)
    box(brown, (4.72, 0.42, 0.55), (1.25, 0.07, 0.5))
    for x in (3.5, 5.94):
        for z in (0.07, 1.03): box(brown, (x, 0.2, z), (0.04, 0.2, 0.04))
    box(brown, (5.95, 0.5, 0.55), (0.04, 0.5, 0.55))                                     # headboard
    box(brown, (3.5, 0.62, 0.55), (0.04, 0.2, 0.55))                                    # footboard
    collider(3.45, 0.0, 6.0, 1.1)
    brown.save("wood_brown.obj"); orange.save("wood_orange.obj")

def build_props():
    m = Mesh()
    # ---- skirting
    for (c, h) in [((W/2, 0.04, 0.01), (W/2, 0.04, 0.01)), ((W/2, 0.04, D - 0.01), (W/2, 0.04, 0.01)),
                   ((0.01, 0.04, D/2), (0.01, 0.04, D/2)), ((W - 0.01, 0.04, D/2), (0.01, 0.04, D/2))]:
        pbox(m, "paper", c, h)
    # ---- desk: navy side panel
    pbox(m, "deskpanel", (0.37, 0.36, 3.0), (0.35, 0.36, 0.02))
    # drawer handles
    for i in range(3): pbox(m, "dgrey", (0.74, 0.12 + i * 0.22, 1.53), (0.01, 0.015, 0.06))
    T = 0.74                                                       # desk surface height
    # PC tower + monitor (CRT)
    pbox(m, "plastic", (0.36, T + 0.04, 2.15), (0.19, 0.04, 0.17))
    pbox(m, "dgrey", (0.56, T + 0.04, 2.15), (0.005, 0.008, 0.1))
    with placed(m, I3, (0.26, T + 0.08, 2.2)):
        pbox(m, "plastic", (0.0, 0.14, 0.0), (0.1, 0.14, 0.17))
        pbox(m, "plastic", (-0.14, 0.13, 0.0), (0.09, 0.1, 0.12))
        pbox(m, "glass", (0.1, 0.14, 0.0), (0.004, 0.115, 0.14))
        pbox(m, "plastic", (0.0, 0.01, 0.0), (0.07, 0.01, 0.08))
    pbox(m, "plastic", (0.55, T + 0.012, 2.2), (0.08, 0.012, 0.19))          # keyboard
    sphere(m, "green", (0.2, T + 0.1, 2.5), 0.035)                           # green mug / apple on a book
    pbox(m, "b3", (0.2, T + 0.03, 2.5), (0.14, 0.03, 0.1)); pbox(m, "b1", (0.2, T + 0.065, 2.5), (0.12, 0.012, 0.09))
    with placed(m, I3, (0.4, T, 2.72)): cyl(m, "mug", 0.04, 0.0, 0.1)
    with placed(m, rotX(math.pi/2), (0.4, T + 0.05, 2.72 + 0.04)): torus(m, "mug", 0.025, 0.007)
    with placed(m, I3, (0.18, T, 2.88)):                                      # pen holder
        cyl(m, "penblue", 0.045, 0.0, 0.11)
        for col, dx, dz, tz in (("red", 0.01, 0.0, 0.12), ("yellow", -0.01, 0.015, -0.1), ("penblue", 0.0, -0.015, 0.0)):
            tube(m, col, (dx, 0.04, dz), (dx + tz * 0.4, 0.21, dz + tz * 0.2), 0.005)
    # lamp
    with placed(m, I3, (0.3, T, 1.82)):
        cyl(m, "dgrey", 0.06, 0.0, 0.015)
        tube(m, "dgrey", (0, 0.015, 0), (0, 0.3, 0), 0.007); tube(m, "dgrey", (0, 0.3, 0), (0.09, 0.4, 0), 0.007)
        with placed(m, rotZ(-0.9), (0.09, 0.4, 0)):
            with colored(m, "chrome"): lathe(m, [(0.012, 0.05), (0.075, -0.07), (0.07, -0.072), (0.01, 0.045)], 20, -1, 90)
    # table fan
    with placed(m, I3, (0.3, T, 1.5)):
        cyl(m, "plastic", 0.07, 0.0, 0.02); tube(m, "plastic", (0, 0.02, 0), (0, 0.18, 0), 0.012)
        sphere(m, "plastic", (0.02, 0.27, 0), 0.05)
        with placed(m, rotZ(math.pi/2), (0.06, 0.27, 0)): torus(m, "metal", 0.14, 0.006, 32, 6)
        for k in range(3):
            with placed(m, rotX(2 * math.pi * k / 3), (0.06, 0.27, 0)): pbox(m, "chrome", (0, 0.065, 0), (0.004, 0.065, 0.03))
    # trash bin under the desk
    with placed(m, I3, (0.38, 0, 2.6)): cyl(m, "bin", 0.14, 0.0, 0.32)
    # ---- chair (faces -x, toward the desk)
    with placed(m, rotY(math.pi), (1.1, 0, 2.15)):
        pbox(m, "navy", (0, 0.46, 0), (0.23, 0.04, 0.23))
        pbox(m, "navy", (-0.24, 0.78, 0), (0.035, 0.26, 0.2))
        pbox(m, "black", (-0.24, 0.78, 0), (0.045, 0.28, 0.215))
        tube(m, "rubber", (0, 0.1, 0), (0, 0.43, 0), 0.025)
        for sgn in (-1, 1):
            tube(m, "rubber", (-0.15, 0.5, sgn * 0.25), (0.12, 0.62, sgn * 0.26), 0.014)      # arms
            tube(m, "rubber", (-0.15, 0.44, sgn * 0.22), (-0.15, 0.62, sgn * 0.25), 0.012)
            tube(m, "rubber", (0.12, 0.44, sgn * 0.24), (0.12, 0.62, sgn * 0.26), 0.012)
        for k in range(5):
            a = 2 * math.pi * k / 5; e = (0.3 * math.cos(a), 0.06, 0.3 * math.sin(a))
            tube(m, "rubber", (0, 0.1, 0), e, 0.017); sphere(m, "rubber", (e[0], 0.035, e[2]), 0.035, 10, 6)
    collider(0.78, 1.82, 1.42, 2.48)
    # ---- shelf contents: books on the top compartment
    x = 0.86
    for i, col in enumerate(("b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b1", "b5")):
        w = random.uniform(0.025, 0.045); h = random.uniform(0.22, 0.32)
        pbox(m, col, (x + w, 1.465 + h/2, 0.17), (w, h/2, 0.1)); x += 2 * w + 0.005
        if x > 1.4: break
    # ---- under-bed storage
    pbox(m, "navybox", (3.95, 0.14, 0.45), (0.25, 0.14, 0.2)); pbox(m, "navybox", (4.45, 0.12, 0.5), (0.24, 0.12, 0.2))
    pbox(m, "navybox", (4.6, 0.3, 0.5), (0.18, 0.06, 0.15), 0.2); pbox(m, "navybox", (4.2, 0.32, 0.5), (0.2, 0.04, 0.13))
    pbox(m, "pinkbox", (5.05, 0.2, 0.55), (0.2, 0.2, 0.35)); pbox(m, "pinkbox", (4.85, 0.18, 0.4), (0.002, 0.18, 0.3))
    pbox(m, "navybox", (5.9, 0.15, 0.55), (0.05, 0.15, 0.3))
    # AC
    pbox(m, "ac", (4.95, 2.32, 0.15), (0.6, 0.2, 0.15)); pbox(m, "acvent", (4.95, 2.22, 0.305), (0.45, 0.012, 0.005))
    # curtain rod
    tube(m, "rod", (2.0, 2.0, 0.26), (5.5, 2.0, 0.26), 0.015, 12)
    sphere(m, "chrome", (1.97, 2.0, 0.26), 0.035); sphere(m, "chrome", (5.53, 2.0, 0.26), 0.035)
    for x in (2.3, 4.6): pbox(m, "chrome", (x, 2.0, 0.17), (0.012, 0.025, 0.1))
    # pillow
    pbox(m, "pillow", (5.6, 0.68, 0.55), (0.25, 0.07, 0.28))
    # slippers (two pairs)
    for (sx, sz, ya) in ((1.7, 2.9, 0.3), (0.6, 4.4, -0.5)):
        for off in (-0.08, 0.08):
            with placed(m, rotY(ya), (sx, 0, sz + off)):
                pbox(m, "slipper", (0, 0.015, 0), (0.13, 0.015, 0.05)); pbox(m, "slipper", (0.08, 0.035, 0), (0.05, 0.015, 0.045))
    m.save("props.obj")

    # emissive: lamp bulb
    e = Mesh()
    with placed(e, I3, (0.3, 0.74, 1.82)):
        with placed(e, rotZ(-0.9), (0.09, 0.4, 0)): sphere(e, "bulb", (0, -0.05, 0), 0.032)
    e.save("emissive.obj")

def build_special():
    c = Mesh()                                                         # shelf boxes with faces
    for cx in (0.98, 1.38):
        box(c, (cx, 1.2, 0.2), (0.17, 0.15, 0.17), 0, uv={i: (lambda u, v: (0.01, 0.01)) for i in (0, 1, 2, 3, 5)})
    c.save("crates.obj")
    s = Mesh()                                                         # speakers (front = +x)
    def spk(R, t):
        with placed(s, R, t):
            box(s, (0, 0.3, 0), (0.15, 0.3, 0.15), 0, uv={i: (lambda u, v: (0.01, 0.01)) for i in (1, 2, 3, 4, 5)})
    spk(I3, (0.22, 0, 3.6)); collider(0.05, 3.4, 0.4, 3.8)
    spk(rotY(-math.pi/2), (5.55, 0, 0.62))
    s.save("speakers.obj")
    cu = Mesh()                                                        # curtain
    with placed(cu, I3, (4.78, 0, 0.26)):
        lathe(cu, [(0.0, 1.98), (0.13, 1.98), (0.15, 1.2), (0.12, 0.35), (0.0, 0.35)], 24, 1, 80)
    cu.save("curtain.obj")
    cal = Mesh()                                                       # calendar + hanging string
    z0, z1, y0, y1 = 4.0, 4.45, 1.4, 2.05
    planar(cal, [(0.012, y0, z1), (0.012, y0, z0), (0.012, y1, z0), (0.012, y1, z1)], (1, 0, 0),
           lambda p: ((z1 - p[2]) / (z1 - z0), (p[1] - y0) / (y1 - y0)))
    cal.save("calendar.obj")
    mt = Mesh()
    box(mt, (4.72, 0.55, 0.55), (1.2, 0.06, 0.46)); mt.save("mattress.obj")
    sp = Mesh()                                                        # sunlight patch on the floor
    sx0 = (SUN[0] / -SUN[1]); sz0 = (SUN[2] / -SUN[1])
    def proj(x, y): return (x + sx0 * y, 0.006, sz0 * y)
    a, b, cc, d = proj(WX0, WY0), proj(WX1, WY0), proj(WX1, WY1), proj(WX0, WY1)
    sp.quad((a, (0, 1, 0), (0, 1)), (b, (0, 1, 0), (1, 1)), (cc, (0, 1, 0), (1, 0)), (d, (0, 1, 0), (0, 0)))
    sp.save("sunpatch.obj")

def patch_main():
    p = os.path.join(ROOT, "main.lua")
    if not os.path.exists(p): return
    s = open(p).read()
    rows = "\n".join("    { %.2f, %.2f, %.2f, %.2f }," % c for c in COLLIDERS)
    s = re.sub(r"-- BEGIN COLLIDERS\n.*?-- END COLLIDERS", "-- BEGIN COLLIDERS\n" + rows + "\n    -- END COLLIDERS", s, flags=re.S)
    open(p, "w").write(s); print("  colliders written to main.lua:", len(COLLIDERS))

if __name__ == "__main__":
    print("textures")
    tex_plaster("plaster_warm.png", (222, 190, 160)); tex_plaster("plaster_cool.png", (176, 166, 198))
    tex_wood("wood_orange.png", (205, 128, 52)); tex_wood("wood_brown.png", (88, 58, 40))
    tex_floor(); tex_palette(); tex_calendar(); tex_curtain(); tex_mattress(); tex_speaker(); tex_crate(); tex_glow(); tex_sunpatch()
    print("models")
    build_walls(); build_floor(); build_window_and_wood(); build_props(); build_special()
    patch_main(); print("done.")
