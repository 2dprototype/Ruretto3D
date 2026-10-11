"""
meshlib.py - tiny OBJ mesh toolkit shared by the DrumRoom3D generators.

Everything is built from triangles with per-vertex normals, written as Wavefront
OBJ ("v/vt/vn" triplets) exactly like the Room3D example, so Crayon's
`graphics.loadModel` reads it directly.
"""
import math, os
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
TEXTURES = os.path.join(ROOT, "assets", "textures")
SOUNDS = os.path.join(ROOT, "assets", "sounds")
FLIP_V = False      # set True if textures appear upside-down in your build (same switch as Room3D)

# ----------------------------------------------------------------------------- vector math
def vsub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def vadd(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vmul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def vcross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def vdot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def vlen(a): return math.sqrt(vdot(a, a))
def vnorm(a):
    l = vlen(a); return (a[0]/l, a[1]/l, a[2]/l) if l > 1e-12 else (0.0, 1.0, 0.0)
I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
def rotY(a): c, s = math.cos(a), math.sin(a); return ((c, 0, s), (0, 1, 0), (-s, 0, c))
def rotZ(a): c, s = math.cos(a), math.sin(a); return ((c, -s, 0), (s, c, 0), (0, 0, 1))
def rotX(a): c, s = math.cos(a), math.sin(a); return ((1, 0, 0), (0, c, -s), (0, s, c))
def mv(R, p): return tuple(R[i][0]*p[0] + R[i][1]*p[1] + R[i][2]*p[2] for i in range(3))
def mm(A, B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))

def rot_from_y(n):
    """Rotation matrix that maps local +Y onto the unit vector n."""
    n = vnorm(n)
    v = vcross((0, 1, 0), n); s = vlen(v); c = n[1]
    if s < 1e-9:
        return I3 if c > 0 else rotX(math.pi)
    K = ((0, -v[2], v[1]), (v[2], 0, -v[0]), (-v[1], v[0], 0))
    K2 = mm(K, K); f = (1 - c) / (s * s)
    return tuple(tuple((1 if i == j else 0) + K[i][j] + K2[i][j]*f for j in range(3)) for i in range(3))

# ----------------------------------------------------------------------------- palettes (solid colours via UV cells)
class Palette:
    """A grid of flat colour cells inside a texture. UV of a colour = centre of its cell."""
    def __init__(self, names, hexes, tex_size, cell=16, y0=0):
        assert len(names) == len(hexes)
        self.names, self.hexes, self.size, self.cell, self.y0 = names, hexes, tex_size, cell, y0
        self.index = {n: i for i, n in enumerate(names)}
        self.cols = tex_size // cell
    def uv(self, name):
        i = self.index[name]; col, row = i % self.cols, i // self.cols
        return ((col*self.cell + self.cell/2) / self.size, 1 - (self.y0 + row*self.cell + self.cell/2) / self.size)
    def paint(self, draw):
        for i, hx in enumerate(self.hexes):
            col, row = i % self.cols, i // self.cols
            x, y = col*self.cell, self.y0 + row*self.cell
            draw.rectangle([x, y, x + self.cell - 1, y + self.cell - 1], fill=hx)

# ----------------------------------------------------------------------------- mesh
class Mesh:
    def __init__(self, palette=None):
        self.v, self.vt, self.vn, self.f = [], [], [], []
        self._v, self._vt, self._vn = {}, {}, {}
        self.stack, self.fixed, self.uvfun = [], None, None
        self.pal = palette
    def _idx(self, tab, lst, val):
        k = tuple(round(x, 5) for x in val)
        if k not in tab: lst.append(val); tab[k] = len(lst)
        return tab[k]
    def tri(self, a, b, c):
        pts = []
        for p, n, uv in (a, b, c):
            p0 = p
            for R, t in reversed(self.stack):
                p = vadd(mv(R, p), t); n = mv(R, n)
            if self.fixed: uv = self.fixed
            elif self.uvfun: uv = self.uvfun(uv, p0)
            pts.append((p, vnorm(n), uv))
        a, b, c = pts
        gn = vcross(vsub(b[0], a[0]), vsub(c[0], a[0]))
        if vlen(gn) < 1e-10: return
        if vdot(gn, vadd(vadd(a[1], b[1]), c[1])) < 0: b, c = c, b      # winding follows the normals
        ids = []
        for p, n, uv in (a, b, c):
            if FLIP_V: uv = (uv[0], 1 - uv[1])
            ids.append((self._idx(self._v, self.v, p), self._idx(self._vt, self.vt, uv), self._idx(self._vn, self.vn, n)))
        self.f.append(ids)
    def quad(self, a, b, c, d): self.tri(a, b, c); self.tri(a, c, d)
    def save(self, name, quiet=False):
        with open(os.path.join(MODELS, name), "w") as fh:
            fh.write(f"# DrumRoom3D {name}\n")
            for p in self.v: fh.write("v %.5f %.5f %.5f\n" % p)
            for t in self.vt: fh.write("vt %.5f %.5f\n" % t)
            for n in self.vn: fh.write("vn %.5f %.5f %.5f\n" % n)
            for f in self.f: fh.write("f " + " ".join(f"{a}/{b}/{c}" for a, b, c in f) + "\n")
        if not quiet: print("  model", name, len(self.f), "tris")

@contextmanager
def placed(m, R=I3, t=(0, 0, 0)):
    m.stack.append((R, t)); yield; m.stack.pop()
@contextmanager
def colored(m, name):
    old = m.fixed; m.fixed = m.pal.uv(name); yield; m.fixed = old
@contextmanager
def uvmapped(m, fn):
    """fn(uv, local_pos) -> uv.  Used to send UVs into a region of a texture atlas."""
    old, oldf = m.uvfun, m.fixed; m.uvfun, m.fixed = fn, None; yield; m.uvfun, m.fixed = old, oldf

# ----------------------------------------------------------------------------- primitives
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
    """Surface of revolution about +Y. profile = [(radius, y), ...]. With flip=1 a profile walked
    bottom-outward / up / top-inward gives outward-facing normals."""
    n = len(profile) - 1; segn = []
    for i in range(n):
        dr, dy = profile[i+1][0]-profile[i][0], profile[i+1][1]-profile[i][1]
        l = math.hypot(dr, dy) or 1e-9; segn.append((flip*dy/l, -flip*dr/l))
    def pn(i, side):
        a = segn[side]; o = side-1 if i == side else side+1
        if 0 <= o < n:
            b = segn[o]
            if a[0]*b[0]+a[1]*b[1] > math.cos(math.radians(crease)):
                s2 = (a[0]+b[0], a[1]+b[1]); l = math.hypot(*s2) or 1; return (s2[0]/l, s2[1]/l)
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

def ring(m, ri, ro, y0, y1, seg=40):
    """Rectangular-section ring (hoops, collars). Colour/uv set by the caller's context."""
    lathe(m, [(ri, y0), (ro, y0), (ro, y1), (ri, y1), (ri, y0)], seg, 1, 30)

def disc(m, y, r, up=True, seg=48):
    """Flat disc at height y (fan). UVs come from the active uvmapped/colored context."""
    n = (0, 1 if up else -1, 0)
    for k in range(seg):
        a0, a1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
        m.tri(((0, y, 0), n, (.5, .5)), ((r*math.cos(a0), y, -r*math.sin(a0)), n, (.5, .5)), ((r*math.cos(a1), y, -r*math.sin(a1)), n, (.5, .5)))

def sphere(m, name, c, r, seg=14, rings=8):
    with colored(m, name): ellipsoid_raw(m, c, (r, r, r), seg, rings)

def ellipsoid(m, name, c, rad, seg=16, rings=10):
    with colored(m, name): ellipsoid_raw(m, c, rad, seg, rings)

def ellipsoid_raw(m, c, rad, seg, rings):
    rx, ry, rz = rad
    for i in range(rings):
        t0, t1 = math.pi*i/rings, math.pi*(i+1)/rings
        for k in range(seg):
            p0, p1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
            def V(t, p):
                n = (math.sin(t)*math.cos(p), math.cos(t), -math.sin(t)*math.sin(p))
                pos = (c[0] + rx*n[0], c[1] + ry*n[1], c[2] + rz*n[2])
                return (pos, (n[0]/rx, n[1]/ry, n[2]/rz), (0, 0))
            m.quad(V(t0, p0), V(t0, p1), V(t1, p1), V(t1, p0))

def torus(m, name, R, tube_r, seg=32, ringn=8):
    prof = [(R + tube_r*math.cos(2*math.pi*i/ringn), tube_r*math.sin(2*math.pi*i/ringn)) for i in range(ringn+1)]
    with colored(m, name): lathe(m, prof, seg, 1, 180)

def tube(m, name, p0, p1, r, seg=8, caps=True):
    a = vsub(p1, p0); ax = vnorm(a)
    h = (0, 1, 0) if abs(ax[1]) < 0.9 else (1, 0, 0)
    u = vnorm(vcross(ax, h)); w = vcross(ax, u)
    with colored(m, name):
        for k in range(seg):
            a0, a1 = 2*math.pi*k/seg, 2*math.pi*(k+1)/seg
            def rg(ang, base):
                n = vadd(vmul(u, math.cos(ang)), vmul(w, math.sin(ang)))
                return (vadd(base, vmul(n, r)), n, (0, 0))
            m.quad(rg(a0, p0), rg(a1, p0), rg(a1, p1), rg(a0, p1))
            if caps:
                for base, nn in ((p0, vmul(ax, -1)), (p1, ax)):
                    m.tri((base, nn, (0, 0)), (rg(a0, base)[0], nn, (0, 0)), (rg(a1, base)[0], nn, (0, 0)))

def planar(m, pts, n, uvf):
    m.quad(*[(p, n, uvf(p)) for p in pts])
