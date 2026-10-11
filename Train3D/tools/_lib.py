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

