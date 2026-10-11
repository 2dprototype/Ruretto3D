#!/usr/bin/env python3
"""
Rūretto 3D - procedural asset generator
=======================================
Generates every 3D model (.obj), texture (.png) and sound effect (.wav)
used by the Crayon Engine version of Rūretto.

    pip install pillow numpy
    python tools/generate_assets.py

Output:
    assets/models/*.obj
    assets/textures/*.png
    assets/sfx/*.wav

World conventions (must match main.lua):
    * Y is up, wheel centre is the world origin.
    * Wheel pocket k is centred at angle  phi = k * 2*pi/37  where a point at
      radius r / angle phi sits at  (r*cos(phi), y, -r*sin(phi)).
    * Texture rows: image row 0 is the TOP of the image = v 1.0 (standard OBJ).
      If textures look upside-down in your build, set FLIP_V = True below.
"""
import math, os, random, struct, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
TEXTURES = os.path.join(ROOT, "assets", "textures")
SFX = os.path.join(ROOT, "assets", "sfx")
FONT = os.path.join(ROOT, "res", "IBMPlexSans-Bold.ttf")
for d in (MODELS, TEXTURES, SFX):
    os.makedirs(d, exist_ok=True)

FLIP_V = False
random.seed(7)
np.random.seed(7)

# ---------------------------------------------------------------- theme (from the original theme.td)
GREEN = "#26cb21"; RED = "#ff2c2c"; BLACK = "#1c1c1c"; WHITE = "#ffffff"
BG = "#1c1c1c"; CHIP = "#ffe72c"; BALL = "#feff2c"

def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ---------------------------------------------------------------- wheel (from the original wheel.td)
WHEEL = [(0,"g"),(32,"r"),(15,"b"),(19,"r"),(4,"b"),(21,"r"),(2,"b"),(25,"r"),(17,"b"),(34,"r"),
         (6,"b"),(27,"r"),(13,"b"),(36,"r"),(11,"b"),(30,"r"),(8,"b"),(23,"r"),(10,"b"),(5,"r"),
         (24,"b"),(16,"r"),(33,"b"),(1,"r"),(20,"b"),(14,"r"),(31,"b"),(9,"r"),(22,"b"),(18,"r"),
         (29,"b"),(7,"r"),(28,"b"),(12,"r"),(35,"b"),(3,"r"),(26,"b")]
COL = {"g": GREEN, "r": RED, "b": BLACK}
COLOR_OF = {n: c for n, c in WHEEL}
SLOTS = 37
SLOT = 2 * math.pi / SLOTS

# ---------------------------------------------------------------- geometry constants (shared with main.lua)
R_HUB, R_IN, R_OUT = 1.18, 1.20, 1.66       # hub wall, pocket ring inner / outer radius
R_BANK_OUT = 2.42                            # outer wall of the ball track
R_BODY = 3.10                                # wooden cabinet radius
TABLE_Y = -0.5                               # table top height
FELT_Y = TABLE_Y + 0.04
FELT_X0, FELT_X1, FELT_Z0, FELT_Z1 = 4.0, 20.0, -3.5, 3.5   # felt slab (16 x 7)
LAY_X0, LAY_Z0 = 5.0, -2.5                   # betting layout origin (zero cell's top-left corner)

def bank_y(r):
    u = max(0.0, (r - R_OUT) / (R_BANK_OUT - R_OUT))
    return 0.62 * u ** 2.4

# ================================================================= mesh helpers
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vadd(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vcross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vdot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def vlen(a): return math.sqrt(vdot(a, a))
def vnorm(a):
    l = vlen(a); return (a[0]/l, a[1]/l, a[2]/l) if l > 1e-12 else (0, 1, 0)

class Mesh:
    def __init__(self):
        self.v, self.vt, self.vn, self.f = [], [], [], []
        self._v, self._vt, self._vn = {}, {}, {}
        self.tris = []   # raw triangles (positions only) for the physics mesh

    def _idx(self, table, lst, val):
        k = tuple(round(x, 5) for x in val)
        if k not in table:
            lst.append(val); table[k] = len(lst)
        return table[k]

    def tri(self, a, b, c):
        """a,b,c = (pos, normal, uv). Winding is fixed up from the supplied normals."""
        gn = vcross(vsub(b[0], a[0]), vsub(c[0], a[0]))
        if vlen(gn) < 1e-10:
            return
        an = vadd(vadd(a[1], b[1]), c[1])
        if vdot(gn, an) < 0:
            b, c = c, b
        ids = []
        for p, n, uv in (a, b, c):
            v = FLIP_V and (uv[0], 1 - uv[1]) or uv
            ids.append((self._idx(self._v, self.v, p), self._idx(self._vt, self.vt, v), self._idx(self._vn, self.vn, n)))
        self.f.append(ids)
        self.tris.append((a[0], b[0], c[0]))

    def quad(self, a, b, c, d):
        self.tri(a, b, c); self.tri(a, c, d)

    def save(self, name, comment=""):
        with open(os.path.join(MODELS, name), "w") as fh:
            fh.write(f"# Ruretto 3D - {name} {comment}\n")
            for p in self.v: fh.write("v %.5f %.5f %.5f\n" % p)
            for t in self.vt: fh.write("vt %.5f %.5f\n" % t)
            for n in self.vn: fh.write("vn %.5f %.5f %.5f\n" % n)
            for f in self.f:
                fh.write("f " + " ".join(f"{a}/{b}/{c}" for a, b, c in f) + "\n")
        print("  model", name, len(self.f), "tris")

    def save_physics(self, name):
        """Double sided, position-only copy used for the static physics mesh."""
        m = Mesh()
        for a, b, c in self.tris:
            n = vnorm(vcross(vsub(b, a), vsub(c, a)))
            nn = (-n[0], -n[1], -n[2])
            m.tri((a, n, (0, 0)), (b, n, (0, 0)), (c, n, (0, 0)))
            m.tri((a, nn, (0, 0)), (c, nn, (0, 0)), (b, nn, (0, 0)))
        m.save(name, "(double sided physics mesh)")

def cyl_pt(r, y, phi):
    return (r * math.cos(phi), y, -r * math.sin(phi))

def lathe(mesh, profile, seg=96, flip=1, crease=45, u_rep=1.0, v_range=(0.0, 1.0)):
    """Revolve a (r, y) profile around Y. normal of a segment = flip*(dy, -dr)."""
    n = len(profile) - 1
    segn, arcs = [], [0.0]
    for i in range(n):
        dr = profile[i+1][0] - profile[i][0]; dy = profile[i+1][1] - profile[i][1]
        l = math.hypot(dr, dy) or 1e-9
        segn.append((flip * dy / l, -flip * dr / l))
        arcs.append(arcs[-1] + l)
    total = arcs[-1] or 1.0
    def pn(i, side):  # smoothed normal at profile point i for segment `side`
        a = segn[side]
        o = side - 1 if i == side else side + 1
        if 0 <= o < n:
            b = segn[o]
            if a[0]*b[0] + a[1]*b[1] > math.cos(math.radians(crease)):
                m = (a[0]+b[0], a[1]+b[1]); l = math.hypot(*m) or 1
                return (m[0]/l, m[1]/l)
        return a
    for s in range(n):
        for k in range(seg):
            p0, p1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
            def V(i, side, phi, kk):
                r, y = profile[i]
                nr, ny = pn(i, side)
                nrm = (nr*math.cos(phi), ny, -nr*math.sin(phi))
                v = v_range[0] + (v_range[1]-v_range[0]) * arcs[i] / total
                return (cyl_pt(r, y, phi), nrm, (kk/seg*u_rep, v))
            a = V(s, s, p0, k); b = V(s, s, p1, k+1)
            c = V(s+1, s, p1, k+1); d = V(s+1, s, p0, k)
            mesh.quad(a, b, c, d)

def box(mesh, c, h, yaw=0.0, uv=None):
    """Axis aligned box (rotated about Y by yaw, same convention as the wheel). h = half sizes."""
    ca, sa = math.cos(yaw), math.sin(yaw)
    def rot(p): return (p[0]*ca + p[2]*sa, p[1], -p[0]*sa + p[2]*ca)
    faces = [((1,0,0), ((1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1))),
             ((-1,0,0), ((-1,-1,1),(-1,-1,-1),(-1,1,-1),(-1,1,1))),
             ((0,1,0), ((-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1))),
             ((0,-1,0), ((-1,-1,1),(1,-1,1),(1,-1,-1),(-1,-1,-1))),
             ((0,0,1), ((-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))),
             ((0,0,-1), ((1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1)))]
    for fi, (nrm, corners) in enumerate(faces):
        pts = []
        for j, q in enumerate(corners):
            p = rot((q[0]*h[0], q[1]*h[1], q[2]*h[2]))
            pos = (c[0]+p[0], c[1]+p[1], c[2]+p[2])
            u, v = [(0,0),(1,0),(1,1),(0,1)][j]
            if uv and fi in uv: u, v = uv[fi](pos, u, v)
            pts.append((pos, vnorm(rot(nrm)), (u, v)))
        mesh.quad(*pts)

def sphere(mesh, c, r, seg=24, rings=14):
    for i in range(rings):
        t0, t1 = math.pi*i/rings, math.pi*(i+1)/rings
        for k in range(seg):
            p0, p1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
            def V(t, p, kk, ii):
                n = (math.sin(t)*math.cos(p), math.cos(t), -math.sin(t)*math.sin(p))
                return ((c[0]+r*n[0], c[1]+r*n[1], c[2]+r*n[2]), n, (kk/seg, 1 - ii/rings))
            mesh.quad(V(t0,p0,k,i), V(t0,p1,k+1,i), V(t1,p1,k+1,i+1), V(t1,p0,k,i+1))

def torus(mesh, R, y, tube, seg=96, ring=10):
    prof = [(R + tube*math.cos(2*math.pi*i/ring), y + tube*math.sin(2*math.pi*i/ring)) for i in range(ring+1)]
    lathe(mesh, prof, seg=seg, flip=1, crease=180)

# ================================================================= textures
def save_tex(img, name):
    img.save(os.path.join(TEXTURES, name)); print("  texture", name, img.size)

def noise_img(w, h, base, var, blur=0):
    arr = np.random.randn(h, w, 1) * var
    a = np.clip(np.array(base, dtype=float)[None, None, :] + arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGB")
    return im.filter(ImageFilter.GaussianBlur(blur)) if blur else im

def font(sz): return ImageFont.truetype(FONT, sz)

def center_text(d, xy, text, fnt, fill):
    bb = d.textbbox((0, 0), text, font=fnt)
    d.text((xy[0] - (bb[0]+bb[2])/2, xy[1] - (bb[1]+bb[3])/2), text, font=fnt, fill=fill)

def tex_wood():
    w, h = 512, 512
    y = np.arange(h)[:, None]; x = np.arange(w)[None, :]
    grain = np.sin(y * 0.09 + np.sin(x * 0.012) * 3.0) * 0.5 + np.sin(y * 0.31) * 0.15 + np.random.randn(h, w) * 0.08
    base = np.array([46, 28, 20], dtype=float)
    a = np.clip(base[None, None, :] * (1 + grain[:, :, None] * 0.35), 0, 255).astype(np.uint8)
    save_tex(Image.fromarray(a, "RGB").filter(ImageFilter.GaussianBlur(0.6)), "wood.png")

def tex_gold():
    w = 256
    x = np.linspace(0, 1, w)[None, :]; y = np.linspace(0, 1, w)[:, None]
    g = 0.78 + 0.22 * np.sin((x + y) * 9) + np.random.randn(w, w) * 0.02
    c = np.array(rgb(CHIP), dtype=float)[None, None, :] * g[:, :, None] * 0.92
    save_tex(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB"), "gold.png")

def tex_trim():
    w = 128
    y = np.linspace(0, 1, w)[:, None]
    g = 0.7 + 0.3 * np.sin(y * math.pi) + np.zeros((w, w))
    c = np.array(rgb(RED), dtype=float)[None, None, :] * g[:, :, None]
    save_tex(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB"), "trim.png")

def tex_ball():
    w = 128
    yy, xx = np.mgrid[0:w, 0:w] / (w - 1)
    g = 0.88 + 0.12 * np.sin(yy * math.pi) * 1.0
    c = np.array(rgb(BALL), dtype=float)[None, None, :] * g[:, :, None]
    im = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for yv in (w*0.5,):    # faint equator so rolling is readable
        d.line([(0, yv), (w, yv)], fill=(235, 235, 40), width=3)
    save_tex(im, "ball.png")

def tex_carpet():
    w = 256
    im = Image.new("RGB", (w, w), rgb("#141414"))
    d = ImageDraw.Draw(im)
    for cx, cy in ((0, 0), (w, 0), (0, w), (w, w), (w/2, w/2)):
        for r, col in ((w*0.36, "#2a0d0d"), (w*0.24, "#3a1010"), (w*0.12, "#1c1c1c")):
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=col)
    arr = np.array(im).astype(float) + np.random.randn(w, w, 1) * 4
    save_tex(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB"), "carpet.png")

def tex_track():
    w, h = 1024, 256
    im = noise_img(w, h, rgb("#202020"), 5, 0.8)
    d = ImageDraw.Draw(im)
    # profile arc-length fractions for rings (outer->inner, same profile as the model)
    pts = track_profile(); arc = [0]
    for i in range(len(pts)-1):
        arc.append(arc[-1] + math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]))
    tot = arc[-1]
    def vpix(r):
        best = min(range(len(pts)), key=lambda i: abs(pts[i][0]-r) + (0 if i > 3 else 9))
        return arc[best] / tot * h
    for r, col, wd in ((2.38, RED, 7), (2.1, "#4a1414", 3), (1.9, "#4a1414", 3), (1.72, RED, 4), (1.68, WHITE, 1)):
        y = vpix(r); d.line([(0, y), (w, y)], fill=col, width=wd)
    # wall / lip painted deep red
    d.rectangle([0, 0, w, vpix(2.42)], fill=rgb("#3a0f0f"))
    save_tex(im, "track.png")

def tex_felt():
    S = 100
    W, H = int((FELT_X1 - FELT_X0) * S), int((FELT_Z1 - FELT_Z0) * S)     # 1600 x 700
    im = noise_img(W, H, rgb(BG), 2.5, 0.6)
    d = ImageDraw.Draw(im, "RGBA")
    ox, oy = int((LAY_X0 - FELT_X0) * S), int((LAY_Z0 - FELT_Z0) * S)     # 100, 100
    f_num, f_sm, f_big = font(46), font(34), font(60)
    line = (255, 255, 255, 70)
    def cell(x, y, w, h, fill=None, text=None, tcol=None, fnt=f_sm):
        if fill: d.rectangle([ox+x*S, oy+y*S, ox+(x+w)*S, oy+(y+h)*S], fill=fill)
        d.rectangle([ox+x*S, oy+y*S, ox+(x+w)*S, oy+(y+h)*S], outline=line, width=2)
        if text: center_text(d, (ox+(x+w/2)*S, oy+(y+h/2)*S), text, fnt, tcol)
    cell(0, 0, 1, 3, rgb(GREEN), "0", rgb(BLACK), f_big)
    for i in range(12):
        for j in range(3):
            n = 3 * (i + 1) - j
            c = COLOR_OF[n]
            tc = rgb(BLACK) if c == "r" else rgb(RED)     # same contrast trick as the original
            cell(1 + i, j, 1, 1, rgb(COL[c]), str(n), tc, f_num)
    for j in range(3):
        cell(13, j, 1, 1, (255, 255, 255, 9), "2-1", (255, 255, 255, 144), f_sm)
    for k in range(3):
        cell(1 + 4*k, 3, 4, 1, (255, 255, 255, 9), f"{12*k+1} to {12*k+12}", (255, 255, 255, 144), f_sm)
    labels = ["1-18", "EVEN", "RED", "BLACK", "ODD", "19-36"]
    for k, lb in enumerate(labels):
        fill = rgb(RED) if lb == "RED" else (rgb(BLACK) if lb == "BLACK" else (255, 255, 255, 9))
        cell(1 + 2*k, 4, 2, 1, fill, lb, (255, 255, 255, 144), f_sm)
    d.rounded_rectangle([ox-14, oy-14, ox+14*S+14, oy+5*S+14], radius=10, outline=rgb(RED) + (255,), width=4)
    center_text(d, (W/2, 48), "R U R E T T O", font(54), rgb(RED))
    center_text(d, (W/2, H-46), "BET ALL ON ZERO LIKE A TRUE GAMBLER", font(26), (255, 255, 255, 80))
    save_tex(im, "felt_layout.png")

# atlas of pockets
ATLAS_COLS, ATLAS_ROWS, CELL_W, CELL_H = 8, 5, 96, 192
def tex_pockets():
    W, H = ATLAS_COLS * CELL_W, ATLAS_ROWS * CELL_H
    im = Image.new("RGB", (W, H), rgb(BG))
    d = ImageDraw.Draw(im)
    fnt = font(54)
    for k, (num, c) in enumerate(WHEEL):
        cx, cy = k % ATLAS_COLS, k // ATLAS_COLS
        x0, y0 = cx * CELL_W, cy * CELL_H
        d.rectangle([x0, y0, x0 + CELL_W - 1, y0 + CELL_H - 1], fill=rgb(COL[c]))
        tc = rgb(RED) if c == "b" else rgb(BLACK)
        center_text(d, (x0 + CELL_W/2, y0 + CELL_H*0.27), str(num), fnt, tc)   # near the inner end, digit tops point to the hub
        d.line([(x0, y0 + CELL_H - 3), (x0 + CELL_W, y0 + CELL_H - 3)], fill=(40, 40, 40), width=3)
    save_tex(im, "pockets.png")

CHIP_VALUES = [10, 50, 100, 500, 1000, 5000, 10000, 50000, 1000000, 5000000, 10000000, 50000000]
def fmt(n):
    if n < 1000: return str(n)
    if n < 1000000: return f"{n//1000}K"
    return f"{n//1000000}M"

def tex_chips():
    S = 256; Hh = 288
    for val in CHIP_VALUES:
        im = Image.new("RGB", (S, Hh), rgb(CHIP))
        d = ImageDraw.Draw(im)
        # --- top cap: same artwork as the original drawchip.td (10 alternating wedges + inner disc)
        cx, cy = S/2, S/2   # circle fills the top 256x256 block; bottom 32 rows hold the side stripes
        R = S/2 - 1
        for k in range(10):
            a0, a1 = 360*k/10, 360*(k+1)/10
            d.pieslice([cx-R, cy-R, cx+R, cy+R], a0, a1, fill=rgb(WHITE if k % 2 == 0 else CHIP))
        r2 = R * 0.78
        d.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], fill=rgb(CHIP))
        d.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], fill=(190, 175, 30))
        d.ellipse([cx-r2+3, cy-r2+3, cx+r2-3, cy+r2-3], fill=rgb(CHIP))
        lab = fmt(val)
        center_text(d, (cx, cy), lab, font(78 if len(lab) <= 3 else 60), (28, 28, 28))
        # --- side strip (bottom 32 rows): alternating white / yellow bars
        for k in range(16):
            d.rectangle([k*16, S, k*16+15, Hh], fill=rgb(WHITE if k % 2 == 0 else CHIP))
        save_tex(im, f"chip_{val}.png")

# ================================================================= models
def track_profile():
    pts = [(2.27, 1.04), (2.36, 1.0), (R_BANK_OUT, 0.92), (R_BANK_OUT, bank_y(R_BANK_OUT))]
    n = 18
    for i in range(1, n + 1):
        r = R_BANK_OUT - (R_BANK_OUT - R_OUT) * i / n
        pts.append((r, bank_y(r)))
    return pts

def model_track():
    m = Mesh(); lathe(m, track_profile(), seg=120, flip=1, crease=50, u_rep=1.0)
    m.save("wheel_track.obj"); m.save_physics("wheel_track_physics.obj")

def model_body():
    m = Mesh()
    # wheel cabinet
    prof = [(2.27, 1.04), (2.9, 1.0), (R_BODY - 0.06, 0.96), (R_BODY, 0.88), (R_BODY, TABLE_Y), (0.0, TABLE_Y)]
    lathe(m, prof, seg=120, flip=-1, crease=50)
    # table slab + legs, uv = wood texture mapped per face
    cx, cz = (-4.6 + 21.0) / 2, 0.0
    box(m, (cx, TABLE_Y - 0.2, cz), (12.8, 0.2, 4.6))
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(m, (cx + sx * 11.8, TABLE_Y - 2.2, cz + sz * 3.8), (0.45, 1.8, 0.45))
    m.save("table_body.obj")

def model_felt():
    m = Mesh()
    cx, cz = (FELT_X0 + FELT_X1) / 2, (FELT_Z0 + FELT_Z1) / 2
    def top_uv(pos, u, v):
        return ((pos[0] - FELT_X0) / (FELT_X1 - FELT_X0), 1 - (pos[2] - FELT_Z0) / (FELT_Z1 - FELT_Z0))
    side_uv = lambda pos, u, v: (0.004, 0.004)
    box(m, (cx, TABLE_Y + 0.02, cz), ((FELT_X1-FELT_X0)/2, 0.02, (FELT_Z1-FELT_Z0)/2),
        uv={2: top_uv, 0: side_uv, 1: side_uv, 3: side_uv, 4: side_uv, 5: side_uv})
    m.save("table_felt.obj")

def model_trim():
    m = Mesh()
    torus(m, 2.62, 1.0, 0.04)           # red ring on the wheel cabinet
    torus(m, 3.08, 0.9, 0.05)           # outer red ring
    cx, cz = (FELT_X0 + FELT_X1) / 2, (FELT_Z0 + FELT_Z1) / 2
    hx, hz = (FELT_X1 - FELT_X0) / 2, (FELT_Z1 - FELT_Z0) / 2
    y = TABLE_Y + 0.06
    box(m, (cx, y, cz - hz - 0.1), (hx + 0.2, 0.06, 0.1))
    box(m, (cx, y, cz + hz + 0.1), (hx + 0.2, 0.06, 0.1))
    box(m, (cx - hx - 0.1, y, cz), (0.1, 0.06, hz))
    box(m, (cx + hx + 0.1, y, cz), (0.1, 0.06, hz))
    m.save("trim.obj")

def model_pockets():
    m = Mesh(); y = 0.004
    half = SLOT / 2
    for k in range(SLOTS):
        cx, cy = k % ATLAS_COLS, k // ATLAS_COLS
        W, H = ATLAS_COLS * CELL_W, ATLAS_ROWS * CELL_H
        ins = 1.5
        u0, u1 = (cx * CELL_W + ins) / W, ((cx + 1) * CELL_W - ins) / W
        vt, vb = 1 - (cy * CELL_H + ins) / H, 1 - ((cy + 1) * CELL_H - ins) / H
        phi = k * SLOT
        n = (0, 1, 0)
        def P(r, a, u, v): return (cyl_pt(r, y, phi + a), n, (u, v))
        # image top (vt) = inner edge, u grows with angle
        m.quad(P(R_IN, -half, u0, vt), P(R_IN, half, u1, vt), P(R_OUT, half, u1, vb), P(R_OUT, -half, u0, vb))
    m.save("rotor_pockets.obj")

def model_metal():
    m = Mesh()
    # hub: wall -> top -> dome -> spindle
    hub = [(R_IN, 0.0), (R_HUB, 0.3), (1.0, 0.34), (0.7, 0.42), (0.4, 0.52), (0.14, 0.58), (0.06, 0.62), (0.06, 1.1)]
    lathe(m, hub, seg=64, flip=1, crease=60)
    sphere(m, (0, 1.17, 0), 0.11, 20, 12)
    for yaw in (0, math.pi / 2):                         # handle spokes + knobs
        box(m, (0, 0.92, 0), (0.42, 0.025, 0.025), yaw)
    for ang in (0, math.pi/2, math.pi, 3*math.pi/2):
        x, _, z = cyl_pt(0.46, 0.92, ang); sphere(m, (x, 0.92, z), 0.06, 12, 8)
    # outer gold rim of the pocket ring
    lathe(m, [(R_OUT, 0.0), (R_OUT, 0.1), (R_OUT + 0.06, 0.1), (R_OUT + 0.06, 0.0)], seg=96, flip=-1, crease=30)
    # 37 frets between pockets (boxes: radial length 0.46, thickness 0.04, height 0.1)
    rc = (R_IN + R_OUT) / 2
    for j in range(SLOTS):
        beta = (j - 0.5) * SLOT
        x, _, z = cyl_pt(rc, 0.05, beta)
        box(m, (x, 0.05, z), ((R_OUT - R_IN) / 2, 0.05, 0.02), beta)
    m.save("rotor_metal.obj")

def model_ball():
    m = Mesh(); sphere(m, (0, 0, 0), 1.0, 28, 16); m.save("ball.obj")

def model_chip():
    m = Mesh(); R, H = 0.34, 0.07; seg = 40
    cu, cv, ru, rv = 0.5, (32 + 128) / 288, 126 / 256, 126 / 288
    for k in range(seg):
        a0, a1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
        def top(a): return (cyl_pt(R, H, a), (0, 1, 0), (cu + ru*math.cos(a), cv + rv*math.sin(a)))
        # top cap
        c = ((0, H, 0), (0, 1, 0), (cu, cv))
        m.tri(c, top(a0), top(a1))
        # underside (reuse centre of the same artwork)
        b = ((0, 0, 0), (0, -1, 0), (cu, cv))
        m.tri(b, (cyl_pt(R, 0, a1), (0, -1, 0), top(a1)[2]), (cyl_pt(R, 0, a0), (0, -1, 0), top(a0)[2]))
        # side strip uv: rows 0..32 of 288 (bottom of the image)
        u0, u1 = k/seg, (k+1)/seg
        n0 = (math.cos(a0), 0, -math.sin(a0)); n1 = (math.cos(a1), 0, -math.sin(a1))
        m.quad((cyl_pt(R, 0, a0), n0, (u0, 0.02)), (cyl_pt(R, 0, a1), n1, (u1, 0.02)),
               (cyl_pt(R, H, a1), n1, (u1, 0.09)), (cyl_pt(R, H, a0), n0, (u0, 0.09)))
    m.save("chip.obj")

def model_marker():
    m = Mesh()   # the "dolly" placed on the winning number
    lathe(m, [(0.26, 0.0), (0.26, 0.05), (0.12, 0.08), (0.06, 0.4), (0.0, 0.5)][::-1], seg=32, flip=-1, crease=60)
    sphere(m, (0, 0.55, 0), 0.1, 16, 10)
    m.save("marker.obj")

def model_floor():
    m = Mesh(); n = 14; s = 4.0; y = -4.0
    for i in range(n):
        for j in range(n):
            x0, z0 = (i - n/2) * s + 8, (j - n/2) * s
            up = (0, 1, 0)
            m.quad(((x0, y, z0 + s), up, (0, 0)), ((x0 + s, y, z0 + s), up, (1, 0)),
                   ((x0 + s, y, z0), up, (1, 1)), ((x0, y, z0), up, (0, 1)))
    m.save("floor.obj")

# ================================================================= sounds (synthesised)
SR = 44100
def write_wav(name, data):
    data = np.clip(data, -1, 1)
    with wave.open(os.path.join(SFX, name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((data * 32767).astype("<i2").tobytes())
    print("  sfx", name)

def t(d): return np.linspace(0, d, int(SR * d), endpoint=False)

def sfx_all():
    x = t(0.09)
    write_wav("tick.wav", (np.sin(2*np.pi*3100*x) * 0.6 + np.random.randn(len(x)) * 0.25) * np.exp(-x * 90))
    x = t(0.16)
    clack = np.sin(2*np.pi*1700*x) * np.exp(-x * 70)
    clack += np.sin(2*np.pi*950*np.clip(x - 0.045, 0, None)) * np.exp(-np.clip(x - 0.045, 0, None) * 60) * (x > 0.045)
    write_wav("chip.wav", clack * 0.7 + np.random.randn(len(x)) * 0.05 * np.exp(-x * 120))
    x = t(0.9)
    nz = np.convolve(np.random.randn(len(x)), np.ones(40) / 40, mode="same")
    env = np.sin(np.pi * np.clip(x / 0.9, 0, 1)) ** 1.5
    write_wav("launch.wav", nz * env * 1.8)
    x = t(0.9); out = np.zeros_like(x)
    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        s = i * 0.12; xx = np.clip(x - s, 0, None)
        out += (np.sin(2*np.pi*f*xx) + 0.3*np.sin(2*np.pi*f*2*xx)) * np.exp(-xx * 4) * (x >= s) * 0.3
    write_wav("win.wav", out)
    x = t(0.12)
    write_wav("click.wav", np.sin(2*np.pi*1200*x) * np.exp(-x * 60) * 0.5)
    try:
        os.system(f'ffmpeg -loglevel error -y -i "{os.path.join(ROOT, "res", "wooh.mp3")}" "{os.path.join(SFX, "wooh.wav")}"')
        print("  sfx wooh.wav (converted from the original wooh.mp3)")
    except Exception:
        pass

if __name__ == "__main__":
    print("textures"); tex_wood(); tex_gold(); tex_trim(); tex_ball(); tex_carpet(); tex_track(); tex_felt(); tex_pockets(); tex_chips()
    print("models"); model_track(); model_body(); model_felt(); model_trim(); model_pockets(); model_metal(); model_ball(); model_chip(); model_marker(); model_floor()
    print("sfx"); sfx_all()
    print("done.")
