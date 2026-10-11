"""
kit.py - the yellow 5-piece drum kit (modelled after the reference photo)

Layout (kit coordinates, metres): +Z points to the audience, the drummer sits at -Z,
+X is the audience's right.  Everything is shifted by KIT_ORIGIN into the room.

  * bass drum 22x16 with black logo head       * 12" + 10" rack toms on the bass drum
  * 14" snare on a basket stand                * 16" floor tom on 3 legs (audience left)
  * hi-hat on a pedal stand (audience right)   * crash (audience left) and ride (audience right) on boom stands
  * round throne, kick pedal, sticks

One texture atlas (assets/textures/kit.png) is shared by every kit model:
    top strip  = palette of flat colours       (head_black / head_white / brass / shell) = textured regions
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from meshlib import *

KIT_ORIGIN = (3.2, 0.0, 2.3)           # world position of the bass-drum centre column (y = floor)
def W(p): return (KIT_ORIGIN[0]+p[0], KIT_ORIGIN[1]+p[1], KIT_ORIGIN[2]+p[2])

# ----------------------------------------------------------------------------- atlas
ATLAS = 512
KIT_NAMES = ["chrome", "steel", "black", "rubber", "felt", "yellow", "yellow2", "seat", "seat2", "stick", "wing", "spring", "badge"]
KIT_HEX   = ["#d3d8e0", "#8b9199", "#18181b", "#0f0f11", "#efe9d8", "#f4d41c", "#d6b100", "#202026", "#35353d", "#c99d64", "#b9bec7", "#6e747c", "#ece8da"]
KIT_PAL = Palette(KIT_NAMES, KIT_HEX, ATLAS, cell=16, y0=0)
REGIONS = {"head_black": (0, 64, 224, 224), "head_white": (224, 64, 224, 224), "brass": (0, 288, 224, 224), "shell": (224, 288, 224, 224)}

def region_uv(name, u, v, inset=2):
    x, y, w, h = REGIONS[name]
    px = x + inset + u*(w - 2*inset); py = y + inset + (1 - v)*(h - 2*inset)
    return (px/ATLAS, 1 - py/ATLAS)
def shell_map(uv, p): return region_uv("shell", uv[0], uv[1])
def planar_map(region, R):
    return lambda uv, p: region_uv(region, 0.5 + p[0]/(2*R), 0.5 - p[2]/(2*R))

def _font(sz):
    for f in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf"):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()

def make_atlas(path):
    rng = np.random.RandomState(11)
    im = Image.new("RGB", (ATLAS, ATLAS), (0, 0, 0)); d = ImageDraw.Draw(im); KIT_PAL.paint(d)
    S = 224; yy, xx = np.mgrid[0:S, 0:S]; rr = np.hypot(xx - S/2, yy - S/2) / (S/2)

    # --- black bass-drum head with logo
    a = np.zeros((S, S, 3)); a[:] = (26, 26, 31); a += (1 - np.clip(rr, 0, 1))[:, :, None] * 9 + rng.randn(S, S)[:, :, None] * 1.6
    a[(rr > 0.91) & (rr < 0.935)] *= 0.55                                   # tuck line near the collar
    head = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"); hd = ImageDraw.Draw(head)
    f = _font(33); word = "TAMA"; sp = 5
    ws = [hd.textlength(c, font=f) for c in word]; tw = sum(ws) + sp*(len(word) - 1); x = (S - tw)/2
    for c, w_ in zip(word, ws):
        hd.text((x, 26), c, font=f, fill=(244, 244, 240)); x += w_ + sp
    hd.rectangle([S/2 - 36, 69, S/2 + 36, 71], fill=(214, 40, 38))          # small red bar under the wordmark
    im.paste(head, REGIONS["head_black"][:2])

    # --- coated white head
    a = np.zeros((S, S, 3)); a[:] = (238, 236, 228)
    a += rng.randn(S, S)[:, :, None] * 3.0
    a *= (1 - 0.10*np.clip(rr - 0.55, 0, 1))[:, :, None]
    a[(rr > 0.62) & (rr < 0.64)] *= 0.93; a[(rr > 0.90) & (rr < 0.93)] *= 0.86
    im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"), REGIONS["head_white"][:2])

    # --- brass cymbal: lathing grooves + polished bell + hammer noise
    a = np.zeros((S, S, 3)); base = np.array((206, 164, 76), float)
    g = 0.94 + 0.05*np.sin(rr*190) + 0.03*np.sin(rr*47 + 1.3) + rng.randn(S, S)*0.012
    ang = np.arctan2(yy - S/2, xx - S/2); g += 0.02*np.sin(ang*3 + rr*4)
    bell = np.clip((0.26 - rr)/0.05, 0, 1); g = g*(1 - bell) + (1.12 + 0.05*np.sin(rr*60))*bell
    edge = np.clip((rr - 0.94)/0.06, 0, 1); g *= 1 - 0.18*edge
    a[:] = base; a *= g[:, :, None]
    im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.4)), REGIONS["brass"][:2])

    # --- yellow shell wrap (u around the shell, v along it)
    a = np.zeros((S, S, 3)); a[:] = (244, 210, 24)
    v = yy / S; u = xx / S
    a *= (0.96 + 0.04*np.sin(u*2*math.pi*3))[:, :, None] * (0.93 + 0.12*np.exp(-((v - 0.5)/0.18)**2))[:, :, None]
    a += rng.randn(S, S)[:, :, None] * 2.2
    sparkle = rng.rand(S, S) > 0.992; a[sparkle] += 40
    im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"), REGIONS["shell"][:2])
    im.save(path); print("  texture", path.split("/")[-1], im.size)

# ----------------------------------------------------------------------------- parts
def rot_axis(axis, ang):
    a = vnorm(axis); c, s = math.cos(ang), math.sin(ang); x, y, z = a; C = 1 - c
    return ((c + x*x*C, x*y*C - z*s, x*z*C + y*s), (y*x*C + z*s, c + y*y*C, y*z*C - x*s), (z*x*C - y*s, z*y*C + x*s, c + z*z*C))

def build_drum(m, r, hs, top="head_white", bottom="head_white", hoop="chrome", lugs=8, bass=False):
    """Drum centred at the origin, axis = local +Y.  Shell yellow, heads textured, hoops/lugs chrome."""
    with uvmapped(m, shell_map): lathe(m, [(r, -hs), (r, hs)], 44, 1, 45)
    for sgn, region in ((1, top), (-1, bottom)):
        if bass:
            y_hoop = (hs - 0.012, hs + 0.04); y_head = hs + 0.022
            with uvmapped(m, shell_map): ring(m, r - 0.012, r + 0.004, *((y_hoop if sgn > 0 else (-y_hoop[1], -y_hoop[0]))), seg=44)
        else:
            y_hoop = (hs - 0.010, hs + 0.016); y_head = hs + 0.004
            with colored(m, hoop): ring(m, r - 0.012, r + 0.012, *((y_hoop if sgn > 0 else (-y_hoop[1], -y_hoop[0]))), seg=44)
        with uvmapped(m, planar_map(region, r)): disc(m, sgn*y_head, r + 0.001, up=(sgn > 0), seg=44)
    # lugs + tension rods
    for k in range(lugs):
        a = 2*math.pi*(k + 0.5)/lugs
        with placed(m, rotY(a)):
            for sgn in (1, -1):
                y = sgn*(hs - 0.04)
                pbox(m, "chrome", (r + 0.010, y, 0), (0.008, 0.022, 0.011))
                top_y = sgn*(hs + (0.034 if bass else 0.012))
                tube(m, "steel", (r + 0.012, top_y, 0), (r + 0.010, y, 0), 0.0035, 5, False)
                if bass: pbox(m, "chrome", (r + 0.012, top_y, 0), (0.008, 0.012, 0.018))   # bass-drum claw
    if not bass:     # badge
        with placed(m, rotY(0.0)): pbox(m, "badge", (r + 0.004, 0, 0), (0.003, 0.016, 0.03))

def cymbal(m, R, tilt=None):
    """Brass cymbal, centre/bell at the origin, bell facing +Y. tilt = (axis_angle, amount) wobble in the cymbal's own frame."""
    t = [0.0, 0.012, 0.028, 0.045, 0.058, 0.074, 0.40*R, 0.70*R, R]
    ys = [0.032, 0.0318, 0.028, 0.018, 0.010, 0.004, 0.0, -0.004, -0.012]
    top = list(zip(t, ys)); bot = [(rr, yy - 0.0035) for rr, yy in top]
    prof = bot + top[::-1]
    R_t = I3 if tilt is None else rot_axis((math.cos(tilt[0]), 0, math.sin(tilt[0])), tilt[1])
    with placed(m, R_t):
        with uvmapped(m, planar_map("brass", R)): lathe(m, prof, 26, 1, 50)

def cyl_at(m, name, p, r, y0, y1, seg=12):
    with placed(m, I3, p): cyl(m, name, r, y0, y1, seg)

def tripod_at(m, x, z, **kw):
    # draw hub at the right place
    leg = kw.get("leg", 0.42); h = kw.get("h", 0.10); rot = kw.get("rot", 0.0); r = kw.get("r", 0.0105); legs = kw.get("legs", 3)
    cyl_at(m, "steel", (x, 0, z), 0.026, 0.0, h + 0.03)
    for k in range(legs):
        a = rot + 2*math.pi*k/legs; ex, ez = x + leg*math.cos(a), z + leg*math.sin(a)
        tube(m, "chrome", (x, h, z), (ex, 0.02, ez), r, 6)
        cyl_at(m, "rubber", (ex, 0, ez), 0.017, 0.0, 0.024, 8)

def boom_stand(m, base, top_y, pivot, n, spindle=True, rot=0.0):
    bx, bz = base                                   # world x,z
    tripod_at(m, bx, bz, leg=0.46, h=0.12, rot=rot)
    tube(m, "chrome", (bx, 0.12, bz), (bx, top_y*0.55, bz), 0.0145, 10)
    tube(m, "steel", (bx, top_y*0.55, bz), (bx, top_y, bz), 0.0105, 10)
    cyl_at(m, "black", (bx, 0, bz), 0.02, top_y*0.55 - 0.02, top_y*0.55 + 0.03)                  # height clamp
    boom_from = (bx, top_y, bz); arm_end = vsub(pivot, vmul(n, 0.045))
    tube(m, "steel", boom_from, arm_end, 0.009, 8)
    d = vnorm((arm_end[0]-boom_from[0], 0, arm_end[2]-boom_from[2]))
    tube(m, "steel", boom_from, vsub(boom_from, vmul(d, 0.16)), 0.009, 6)                     # counter-weight stub
    sphere(m, "black", vsub(boom_from, vmul(d, 0.17)), 0.026, 10, 6)
    sphere(m, "chrome", boom_from, 0.02, 10, 6)
    if spindle:
        tube(m, "steel", vsub(pivot, vmul(n, 0.055)), vadd(pivot, vmul(n, 0.07)), 0.0055, 6)
        tube(m, "felt", vsub(pivot, vmul(n, 0.012)), vsub(pivot, vmul(n, 0.004)), 0.026, 10)
        tube(m, "felt", vadd(pivot, vmul(n, 0.036)), vadd(pivot, vmul(n, 0.044)), 0.024, 10)
        sphere(m, "wing", vadd(pivot, vmul(n, 0.062)), 0.014, 8, 6)

# ----------------------------------------------------------------------------- kit definition (kit coordinates)
def unit(x, y, z): return vnorm((x, y, z))
def xz(p): return (p[0], p[2])
TOM_T = math.radians(26)
N_TOM = (0.0, math.cos(TOM_T), -math.sin(TOM_T))                 # tilt toward the drummer
N_TOM2 = unit(-0.07, math.cos(TOM_T), -math.sin(TOM_T)); N_TOM1 = unit(0.07, math.cos(TOM_T), -math.sin(TOM_T))
N_SNARE = unit(0.0, math.cos(math.radians(7)), -math.sin(math.radians(7)))

DRUMS = {   # id: dict(centre, axis, radius, half-shell, ...)
    "kick":     dict(c=(0.0, 0.300, 0.0),     n=(0, 0, 1),  r=0.279, hs=0.185, pr=0.288, ph=0.232),
    "tom2":     dict(c=(-0.168, 0.800, 0.03), n=N_TOM2,     r=0.152, hs=0.095, pr=0.160, ph=0.112),
    "tom1":     dict(c=(0.148, 0.790, 0.03),  n=N_TOM1,     r=0.127, hs=0.082, pr=0.136, ph=0.100),
    "snare":    dict(c=(0.120, 0.625, -0.62), n=N_SNARE,    r=0.178, hs=0.065, pr=0.188, ph=0.082),
    "floortom": dict(c=(-0.640, 0.455, -0.14), n=(0, 1, 0), r=0.203, hs=0.200, pr=0.212, ph=0.214),
}
HAT   = dict(c=(0.62, 0.950, -0.30), n=unit(0.0, 1.0, 0.03), r=0.178)
CRASH = dict(c=(-0.80, 1.300, -0.18), n=unit(0.10, 0.96, -0.24), r=0.225)
RIDE  = dict(c=(0.95, 1.250, -0.12),  n=unit(-0.10, 0.96, -0.24), r=0.254)
THRONE = (0.02, -1.15)

WOBBLE_TILT = math.radians(4.0)
N_WOBBLE = 8

def build_drum_models():
    meta = {}
    for name, dd in DRUMS.items():
        m = Mesh(KIT_PAL)
        with placed(m, rot_from_y(dd["n"])):
            if name == "kick":
                build_drum(m, dd["r"], dd["hs"], top="head_black", bottom="head_white", bass=True, lugs=8)
            elif name == "snare":
                build_drum(m, dd["r"], dd["hs"], lugs=10)
                with placed(m, rotY(0.0)): pbox(m, "chrome", (dd["r"] + 0.03, -dd["hs"] + 0.02, 0), (0.03, 0.025, 0.03))   # strainer
            else:
                build_drum(m, dd["r"], dd["hs"], lugs=8 if name == "floortom" else 6)
        m.save(name + ".obj")
        meta[name] = dict(shape="cyl", c=W(dd["c"]), a=vnorm(dd["n"]), r=dd["pr"], h=dd["ph"])
    # hi-hat (top cymbal moves; bottom cymbal lives in hardware)
    m = Mesh(KIT_PAL)
    with placed(m, rot_from_y(HAT["n"])):
        cymbal(m, HAT["r"])
    cyl(m, "steel", 0.012, 0.03, 0.05, 8)
    m.save("hat_top.obj")
    meta["hihat"] = dict(shape="cyl", c=W(HAT["c"]), a=vnorm(HAT["n"]), r=HAT["r"] + 0.01, h=0.035)
    # crash / ride with wobble variants (variant 0 = still)
    for name, cd in (("crash", CRASH), ("ride", RIDE)):
        for v in range(N_WOBBLE + 1):
            m = Mesh(KIT_PAL)
            with placed(m, rot_from_y(cd["n"])):
                cymbal(m, cd["r"], None if v == 0 else (2*math.pi*(v - 1)/N_WOBBLE, WOBBLE_TILT))
            m.save(f"{name}_{v}.obj", quiet=True)
        print("  model", f"{name}_0..{N_WOBBLE}.obj", "(wobble variants)")
        meta[name] = dict(shape="cyl", c=W(cd["c"]), a=vnorm(cd["n"]), r=cd["r"] + 0.01, h=0.035)
    meta["kickpedal"] = dict(shape="sphere", c=W((0.0, 0.07, -0.44)), r=0.13)
    meta["hatpedal"] = dict(shape="sphere", c=W((0.62, 0.05, -0.52)), r=0.12)
    return meta

def build_hardware():
    m = Mesh(KIT_PAL)
    # ---- bass drum: spurs, tom-mount base, rubber feet
    for sgn in (-1, 1):
        tube(m, "chrome", W((sgn*0.19, 0.22, 0.16)), W((sgn*0.40, 0.012, 0.36)), 0.011, 8)
        with placed(m, I3, W((sgn*0.40, 0, 0.36))): cyl(m, "rubber", 0.022, 0.0, 0.03, 10)
        pbox(m, "chrome", W((sgn*0.19, 0.22, 0.16)), (0.02, 0.025, 0.02))
    pbox(m, "chrome", W((0.0, 0.585, 0.03)), (0.05, 0.012, 0.05))
    # ---- tom mount: post, block, arms
    tube(m, "chrome", W((0.0, 0.58, 0.03)), W((0.0, 0.705, 0.03)), 0.013, 10)
    pbox(m, "chrome", W((0.0, 0.715, 0.03)), (0.045, 0.022, 0.03))
    for nm, sgn in (("tom2", -1), ("tom1", 1)):
        dd = DRUMS[nm]; c = dd["c"]; side = (c[0] - sgn*(dd["r"] + 0.014), c[1] - 0.012, c[2])
        tube(m, "chrome", W((sgn*0.03, 0.72, 0.03)), W(side), 0.0095, 8)
        pbox(m, "chrome", W(side), (0.012, 0.03, 0.02))
    # ---- snare stand
    sc = DRUMS["snare"]["c"]; sx, sz = sc[0], sc[2]; hub = (sx, 0.495, sz)
    sphere(m, "chrome", W(hub), 0.03, 10, 6)
    for k in range(3):
        a = math.radians(90 + 120*k); tip = (sx + 0.168*math.cos(a), 0.552, sz + 0.168*math.sin(a))
        tube(m, "chrome", W(hub), W(tip), 0.0085, 6); pbox(m, "rubber", W(tip), (0.014, 0.008, 0.014))
    tube(m, "chrome", W(hub), W((sx, 0.14, sz)), 0.0125, 10); tube(m, "steel", W((sx, 0.14, sz)), W((sx, 0.08, sz)), 0.0095, 8)
    tripod_at_k(m, sx, sz, leg=0.30, h=0.10, rot=math.radians(-30))
    # ---- floor tom legs (3)
    fc = DRUMS["floortom"]["c"]; fr = DRUMS["floortom"]["r"]
    for k in range(3):
        a = math.radians(30 + 120*k); bx, bz = fc[0] + (fr + 0.016)*math.cos(a), fc[2] - (fr + 0.016)*math.sin(a)
        fx, fz = fc[0] + (fr + 0.085)*math.cos(a), fc[2] - (fr + 0.085)*math.sin(a)
        pbox(m, "chrome", W((bx, fc[1] + 0.07, bz)), (0.02, 0.03, 0.02), -a)
        tube(m, "chrome", W((bx, fc[1] + 0.09, bz)), W((fx, 0.03, fz)), 0.0125, 8)
        with placed(m, I3, W((fx, 0, fz))): cyl(m, "rubber", 0.022, 0.0, 0.035, 10)
    # ---- cymbal stands
    boom_stand(m, xz(W((-0.98, 0, -0.55))), 1.20, W(CRASH["c"]), vnorm(CRASH["n"]), rot=math.radians(20))
    boom_stand(m, xz(W((1.05, 0, -0.55))), 1.15, W(RIDE["c"]), vnorm(RIDE["n"]), rot=math.radians(160))
    # ---- hi-hat: stand, clutch, bottom cymbal, pedal
    hx, hy, hz = HAT["c"]
    tripod_at_k(m, hx, hz, leg=0.38, h=0.09, rot=math.radians(90))
    tube(m, "chrome", W((hx, 0.09, hz)), W((hx, 0.55, hz)), 0.0145, 10); tube(m, "steel", W((hx, 0.55, hz)), W((hx, 0.925, hz)), 0.0105, 10)
    cyl_at(m, "black", W((hx, 0, hz)), 0.018, 0.545, 0.58)
    tube(m, "steel", W((hx, 0.925, hz)), W((hx, hy - 0.026, hz)), 0.0045, 6)
    with placed(m, I3, W((hx, hy - 0.035, hz))):
        with placed(m, rotX(math.pi)): cymbal(m, 0.178)
    tube(m, "chrome", W((hx, hy - 0.045, hz)), W((hx, hy - 0.052, hz)), 0.014, 10)
    cyl_at(m, "chrome", W((hx, 0, hz)), 0.012, hy + 0.034 - 0.0, hy + 0.058, 10)
    pbox(m, "steel", W((hx, 0.01, hz - 0.18)), (0.05, 0.008, 0.19))                                  # base plate
    with placed(m, rotX(0.20), W((hx, 0.06, hz - 0.20))): pbox(m, "chrome", (0, 0, 0), (0.042, 0.008, 0.15))   # foot board
    pbox(m, "black", W((hx, 0.10, hz - 0.31)), (0.032, 0.006, 0.04))
    tube(m, "steel", W((hx, 0.04, hz - 0.02)), W((hx, 0.09, hz - 0.05)), 0.009, 6)
    # ---- kick pedal
    pz = -0.41
    pbox(m, "steel", W((0.0, 0.010, pz - 0.06)), (0.075, 0.008, 0.20))
    with placed(m, rotX(-0.28), W((0.0, 0.055, pz - 0.09))): pbox(m, "chrome", (0, 0, 0), (0.055, 0.007, 0.13))
    for sgn in (-1, 1):
        tube(m, "chrome", W((sgn*0.07, 0.015, pz + 0.02)), W((sgn*0.07, 0.17, pz + 0.01)), 0.012, 8)
        tube(m, "spring", W((sgn*0.05, 0.03, pz + 0.01)), W((sgn*0.05, 0.14, pz + 0.01)), 0.006, 6)
    tube(m, "steel", W((-0.07, 0.17, pz + 0.01)), W((0.07, 0.17, pz + 0.01)), 0.0085, 8)
    tube(m, "chrome", W((0.0, 0.17, pz + 0.01)), W((0.0, 0.325, -0.245)), 0.0075, 8)
    sphere(m, "felt", W((0.0, 0.335, -0.25)), 0.026, 10, 8)
    tube(m, "black", W((0.0, 0.07, pz - 0.10)), W((0.0, 0.15, pz + 0.01)), 0.005, 5)                # strap
    # ---- throne
    tx, tz = THRONE; th = 0.50
    with placed(m, I3, W((tx, th, tz))):
        with colored(m, "seat"): lathe(m, [(0, -0.03), (0.17, -0.03), (0.178, 0.0), (0.172, 0.04), (0.14, 0.062), (0.0, 0.066)], 28, 1, 60)
        with colored(m, "seat2"): lathe(m, [(0.172, 0.0), (0.178, 0.004), (0.1745, 0.02), (0.172, 0.0)], 28, 1, 60)
    tube(m, "chrome", W((tx, 0.12, tz)), W((tx, th - 0.03, tz)), 0.0145, 10); tube(m, "steel", W((tx, 0.06, tz)), W((tx, 0.30, tz)), 0.011, 8)
    tripod_at_k(m, tx, tz, leg=0.31, h=0.10, rot=math.radians(35), r=0.012)
    # ---- sticks on the rug
    for (a, b) in (((0.38, -1.02), (0.62, -1.28)), ((0.45, -0.98), (0.70, -1.20))):
        tube(m, "stick", W((a[0], 0.02, a[1])), W((b[0], 0.02, b[1])), 0.007, 6)
        sphere(m, "stick", W((b[0], 0.02, b[1])), 0.009, 6, 4)
    m.save("kit_hw.obj")

def tripod_at_k(m, x, z, **kw):
    """tripod in kit coordinates"""
    leg = kw.get("leg", 0.42); h = kw.get("h", 0.10); rot = kw.get("rot", 0.0); r = kw.get("r", 0.0105)
    cyl_at(m, "steel", W((x, 0, z)), 0.026, 0.0, h + 0.03)
    for k in range(3):
        a = rot + 2*math.pi*k/3; ex, ez = x + leg*math.cos(a), z + leg*math.sin(a)
        tube(m, "chrome", W((x, h, z)), W((ex, 0.02, ez)), r, 6)
        cyl_at(m, "rubber", W((ex, 0, ez)), 0.017, 0.0, 0.024, 8)

def kit_colliders():
    """2D footprints (world x0,z0,x1,z1) of the kit, for the player's collision test."""
    def box_(x0, z0, x1, z1):
        a, b = W((x0, 0, z0)), W((x1, 0, z1)); return (min(a[0], b[0]), min(a[2], b[2]), max(a[0], b[0]), max(a[2], b[2]))
    return [box_(-0.50, -0.30, 0.50, 0.45),        # bass drum + spurs + toms
            box_(-0.92, -0.40, -0.36, 0.12),       # floor tom
            box_(0.02, -0.80, 0.30, -0.45),        # snare
            box_(0.44, -0.52, 0.80, -0.14),        # hi-hat
            box_(-1.22, -0.82, -0.52, 0.06),       # crash stand + cymbal
            box_(0.68, -0.80, 1.32, 0.12),         # ride stand + cymbal
            box_(-0.24, -1.38, 0.28, -0.92)]       # throne

def build_all(textures_dir):
    make_atlas(textures_dir + "/kit.png")
    meta = build_drum_models()
    build_hardware()
    return meta
