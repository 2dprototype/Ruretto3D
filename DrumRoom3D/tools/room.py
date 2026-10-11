"""room.py - rehearsal room around the drum kit: wood floor, rug, foam wall, window + sun patch, posters, amp, PA speakers, lights."""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from meshlib import *
from kit import KIT_ORIGIN

random.seed(3); np.random.seed(3)
W, D, H = 6.4, 6.0, 2.7
WZ0, WZ1, WY0, WY1 = 1.4, 3.2, 0.95, 2.0            # window opening in the left wall (x = 0)
SUN = (0.8, -0.5, 0.28)                              # direction the sunlight travels (also used by main.lua)

NAMES = ["foamA", "foamB", "paper", "wood", "amp", "knob", "chrome", "black", "shade", "door", "rod", "cord", "lw", "lr", "lb", "lg", "grey"]
HEXES = ["#23232a", "#1a1a20", "#efe9dc", "#6b4a32", "#17171a", "#d8d8dc", "#c8ccd2", "#101012", "#2b3b46", "#8a5a34", "#b9b0a0", "#222226", "#fff0c0", "#ff5a4a", "#5aa0ff", "#6af08a", "#5b5b63"]
PAL = Palette(NAMES, HEXES, 128, 16)

def save(img, name): img.save(os.path.join(TEXTURES, name)); print("  texture", name, img.size)
def tfont(sz):
    for f in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()
def blotch(w, h, scale, amp):
    small = np.random.rand(max(2, h//scale), max(2, w//scale))*255
    return (np.array(Image.fromarray(small.astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float)/255 - 0.5)*amp

def textures():
    d = Image.new("RGB", (128, 128), (0, 0, 0)); PAL.paint(ImageDraw.Draw(d)); save(d, "room_palette.png")
    for name, base in (("plaster_a.png", (226, 205, 176)), ("plaster_b.png", (52, 98, 112))):
        w = 512; n = blotch(w, w, 64, 22) + blotch(w, w, 8, 10) + np.random.randn(w, w)*3
        save(Image.fromarray(np.clip(np.array(base, float)[None, None, :] + n[:, :, None], 0, 255).astype(np.uint8), "RGB"), name)
    S = 1024; im = Image.new("RGB", (S, S)); dr = ImageDraw.Draw(im); sh = S//40
    for r in range(40):
        x = -random.randint(0, 300)
        while x < S:
            ln = random.randint(180, 330); f = random.uniform(0.84, 1.1)
            dr.rectangle([x, r*sh, x + ln - 2, r*sh + sh - 2], fill=tuple(int(c*f) for c in (168, 112, 66))); x += ln
    a = np.array(im).astype(float) + (np.sin(np.arange(S)[None, :]*0.05 + np.arange(S)[:, None]*0.3)*6 + np.random.randn(S, S)*5)[:, :, None]
    save(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"), "floor.png")
    # rug
    w, h = 512, 384; im = Image.new("RGB", (w, h), (120, 28, 36)); dr = ImageDraw.Draw(im)
    for i, col in enumerate(((226, 196, 120), (40, 40, 60), (226, 196, 120))): dr.rectangle([14 + i*10, 14 + i*10, w - 15 - i*10, h - 15 - i*10], outline=col, width=5)
    for k in range(7):
        cx = 80 + k*58; dr.polygon([(cx, 192 - 60), (cx + 26, 192), (cx, 192 + 60), (cx - 26, 192)], outline=(226, 196, 120), fill=(150, 40, 48) if k % 2 else (36, 40, 70))
    n = np.random.randn(h, w)*7; save(Image.fromarray(np.clip(np.array(im).astype(float) + n[:, :, None], 0, 255).astype(np.uint8), "RGB"), "rug.png")
    # posters
    for i, (c0, c1, word) in enumerate((((255, 120, 60), (60, 20, 90), "LIVE"), ((40, 160, 200), (20, 20, 60), "DRUMS"))):
        w, h = 256, 384; im = Image.new("RGB", (w, h)); dr = ImageDraw.Draw(im)
        for y in range(h): t = y/h; dr.line([(0, y), (w, y)], fill=tuple(int(c0[j]*(1 - t) + c1[j]*t) for j in range(3)))
        for k in range(14): dr.pieslice([-60, 160, w + 60, 520], 180 + k*180/14, 180 + (k + .5)*180/14, fill=(255, 235, 170))
        dr.ellipse([w/2 - 46, 150, w/2 + 46, 242], fill=(255, 240, 200)); f = tfont(54); tw = dr.textlength(word, font=f)
        dr.text(((w - tw)/2, 40), word, font=f, fill=(255, 255, 255)); dr.rectangle([4, 4, w - 5, h - 5], outline=(20, 20, 20), width=5)
        save(im, f"poster{i + 1}.png")
    # speaker cabinet / amp face / misc
    S = 256; im = Image.new("RGB", (S, S), (24, 24, 28)); dr = ImageDraw.Draw(im)
    for cx, cy, r in ((128, 66, 36), (128, 176, 66)):
        dr.ellipse([cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6], fill=(90, 90, 96)); dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(38, 38, 42))
        dr.ellipse([cx - r*.5, cy - r*.5, cx + r*.5, cy + r*.5], fill=(66, 66, 72)); dr.ellipse([cx - r*.18, cy - r*.18, cx + r*.18, cy + r*.18], fill=(150, 150, 154))
    save(im, "speaker.png")
    im = Image.new("RGB", (256, 160), (30, 30, 34)); dr = ImageDraw.Draw(im)
    for x in range(0, 256, 6): dr.line([(x, 0), (x, 160)], fill=(58, 52, 40)); 
    for y in range(0, 160, 6): dr.line([(0, y), (256, y)], fill=(48, 44, 36))
    dr.rectangle([0, 0, 255, 159], outline=(10, 10, 12), width=6); save(im, "amp_face.png")
    g = np.linspace(0, 1, 128)[:, None]*np.ones((128, 128)); save(Image.fromarray(np.stack([np.full((128, 128), 255.), 246 - 56*g, 214 - 100*g], -1).astype(np.uint8), "RGB"), "glow.png")
    a = np.zeros((512, 512, 4), np.uint8); a[:, :] = (255, 176, 84, 140); im = Image.fromarray(a, "RGBA").filter(ImageFilter.GaussianBlur(5)); arr = np.array(im)
    arr[:6, :, 3] = 0; arr[-6:, :, 3] = 0; arr[:, :6, 3] = 0; arr[:, -6:, 3] = 0; save(Image.fromarray(arr, "RGBA"), "sunpatch.png")
    x = np.linspace(0, 1, 256)[None, :]; g = 0.86 + 0.14*np.sin(x*2*math.pi*7) + np.zeros((256, 1))
    save(Image.fromarray(np.clip(np.array((226, 218, 200), float)[None, None, :]*g[:, :, None], 0, 255).astype(np.uint8), "RGB"), "curtain.png")

def pyramid(m, x, y, s, hgt, name):
    a = [(x, y, 0), (x + s, y, 0), (x + s, y + s, 0), (x, y + s, 0)]; ap = (x + s/2, y + s/2, hgt)
    with colored(m, name):
        for i in range(4):
            p, q = a[i], a[(i + 1) % 4]; n = vnorm(vcross(vsub(q, p), vsub(ap, p)))
            if n[2] < 0: n = vmul(n, -1)
            m.tri((p, n, (0, 0)), (q, n, (0, 0)), (ap, n, (0, 0)))

def models():
    COL = []
    P = Mesh(PAL)
    # walls
    A, B = Mesh(), Mesh()
    for z0, z1, y0, y1 in ((0, WZ0, 0, H), (WZ1, D, 0, H), (WZ0, WZ1, 0, WY0), (WZ0, WZ1, WY1, H)):
        planar(A, [(0, y0, z1), (0, y0, z0), (0, y1, z0), (0, y1, z1)], (1, 0, 0), lambda p: (p[2]/D, p[1]/H))
    planar(A, [(W, 0, D), (0, 0, D), (0, H, D), (W, H, D)], (0, 0, -1), lambda p: (p[0]/W, p[1]/H))
    planar(A, [(0, H, 0), (W, H, 0), (W, H, D), (0, H, D)], (0, -1, 0), lambda p: (p[0]/W, p[2]/D))
    planar(B, [(0, 0, 0), (W, 0, 0), (W, H, 0), (0, H, 0)], (0, 0, 1), lambda p: (p[0]/W, p[1]/H))
    planar(B, [(W, 0, 0), (W, 0, D), (W, H, D), (W, H, 0)], (-1, 0, 0), lambda p: (p[2]/D, p[1]/H))
    A.save("walls_a.obj"); B.save("walls_b.obj")
    F = Mesh(); planar(F, [(0, 0, D), (W, 0, D), (W, 0, 0), (0, 0, 0)], (0, 1, 0), lambda p: (p[0]/W, 1 - p[2]/D)); F.save("floor.obj")
    R = Mesh(); x0, x1, z0, z1 = 1.5, 4.9, 0.5, 3.3
    planar(R, [(x0, .008, z1), (x1, .008, z1), (x1, .008, z0), (x0, .008, z0)], (0, 1, 0), lambda p: ((p[0] - x0)/(x1 - x0), (p[2] - z0)/(z1 - z0))); R.save("rug.obj")
    # acoustic foam behind the kit
    fm = Mesh(PAL); t = 0.4
    for i in range(11):
        for j in range(4):
            for a in range(4):
                for b in range(4):
                    pyramid(fm, 1.0 + i*t + a*0.1, 0.7 + j*t + b*0.1, 0.1, 0.05, "foamA" if (i + j) % 2 else "foamB")
    fm.save("foam.obj")
    # window frame, door, curtain rod, lamp, skirting
    cy, cz = (WY0 + WY1)/2, (WZ0 + WZ1)/2
    pbox(P, "wood", (-0.06, WY0 - 0.02, cz), (0.05, 0.03, (WZ1 - WZ0)/2 + 0.08)); pbox(P, "wood", (-0.04, WY1 + 0.02, cz), (0.04, 0.03, (WZ1 - WZ0)/2 + 0.04))
    for z in (WZ0, WZ1): pbox(P, "wood", (-0.04, cy, z), (0.04, (WY1 - WY0)/2, 0.03))
    pbox(P, "wood", (-0.04, cy, cz), (0.03, (WY1 - WY0)/2, 0.02)); pbox(P, "wood", (-0.04, cy, cz), (0.03, 0.02, (WZ1 - WZ0)/2))
    pbox(P, "door", (W - 0.02, 1.05, 5.1), (0.02, 1.05, 0.5)); pbox(P, "chrome", (W - 0.06, 1.0, 4.7), (0.03, 0.015, 0.03))
    tube(P, "rod", (0.2, 2.2, 1.0), (0.2, 2.2, 3.7), 0.015, 8)
    for pt in ((0.2, 1.0), (0.2, 3.7)): sphere(P, "chrome", (pt[0], 2.2, pt[1]), 0.03)
    for (c, h) in (((W/2, 0.04, 0.01), (W/2, 0.04, 0.01)), ((W/2, 0.04, D - 0.01), (W/2, 0.04, 0.01)), ((0.01, 0.04, D/2), (0.01, 0.04, D/2)), ((W - 0.01, 0.04, D/2), (0.01, 0.04, D/2))): pbox(P, "paper", c, h)
    # pendant lamp
    kx, kz = KIT_ORIGIN[0], KIT_ORIGIN[2] - 0.2
    tube(P, "cord", (kx, H, kz), (kx, 2.18, kz), 0.006, 5)
    with placed(P, I3, (kx, 2.1, kz)):
        with colored(P, "shade"): lathe(P, [(0.04, 0.12), (0.2, 0.0), (0.205, -0.005), (0.045, 0.125)], 24, -1, 90)
    # amp (faces -x) + PA speakers
    ax, az = 6.15, 3.4
    pbox(P, "amp", (ax, 0.26, az), (0.14, 0.26, 0.3)); pbox(P, "chrome", (ax - 0.14, 0.5, az), (0.012, 0.01, 0.3))
    for k in range(5): cyl_t = (ax - 0.15, 0.47, az - 0.2 + k*0.1); sphere(P, "knob", cyl_t, 0.018, 8, 5)
    tube(P, "black", (ax, 0.52, az - 0.12), (ax, 0.52, az + 0.12), 0.012, 6)
    COL.append((ax - 0.16, az - 0.32, W, az + 0.32))
    AF = Mesh(); fx = ax - 0.1401
    planar(AF, [(fx, 0.04, az + 0.27), (fx, 0.04, az - 0.27), (fx, 0.42, az - 0.27), (fx, 0.42, az + 0.27)], (-1, 0, 0), lambda p: ((p[2] - (az - 0.27))/0.54, (p[1] - 0.04)/0.38)); AF.save("amp_face.obj")
    Sp = Mesh()
    for sx in (0.45, W - 0.45):
        box(Sp, (sx, 0.5, 0.24), (0.25, 0.5, 0.2), 0, uv={i: (lambda u, v: (0.01, 0.01)) for i in (0, 1, 2, 3, 5)}); COL.append((sx - 0.26, 0.0, sx + 0.26, 0.46))
    Sp.save("speakers.obj")
    for i, pz in enumerate((1.6, 2.8)):
        Q = Mesh(); planar(Q, [(W - 0.012, 1.05, pz + 0.3), (W - 0.012, 1.05, pz - 0.3), (W - 0.012, 1.95, pz - 0.3), (W - 0.012, 1.95, pz + 0.3)], (-1, 0, 0), lambda p, pz=pz: ((p[2] - (pz - 0.3))/0.6, (p[1] - 1.05)/0.9)); Q.save(f"poster{i + 1}.obj")
    P.save("props.obj")
    # curtain, window glow, sun patch
    C = Mesh()
    with placed(C, I3, (0.24, 0, 3.45)): lathe(C, [(0, 2.18), (0.13, 2.18), (0.15, 1.3), (0.12, 0.2), (0, 0.2)], 24, 1, 80)
    C.save("curtain.obj")
    G = Mesh(); planar(G, [(-0.1, WY0, WZ0), (-0.1, WY0, WZ1), (-0.1, WY1, WZ1), (-0.1, WY1, WZ0)], (1, 0, 0), lambda p: ((p[2] - WZ0)/(WZ1 - WZ0), (p[1] - WY0)/(WY1 - WY0))); G.save("window_glow.obj")
    Sn = Mesh()
    def proj(z, y): t = y/-SUN[1]; return (SUN[0]*t, 0.012, z + SUN[2]*t)
    a, b, c, d = proj(WZ0, WY0), proj(WZ1, WY0), proj(WZ1, WY1), proj(WZ0, WY1)
    Sn.quad((a, (0, 1, 0), (0, 1)), (b, (0, 1, 0), (1, 1)), (c, (0, 1, 0), (1, 0)), (d, (0, 1, 0), (0, 0))); Sn.save("sunpatch.obj")
    # emissive: pendant bulb + fairy lights along the back wall
    L = Mesh(PAL); sphere(L, "lw", (kx, 2.03, kz), 0.05, 10, 6)
    cols = ["lw", "lr", "lb", "lg"]; pts = []
    for k in range(25):
        x = 0.4 + k*0.23; y = 2.52 - 0.12*abs(math.sin((x - 0.4)/1.15*math.pi/1)); pts.append((x, y, 0.06)); sphere(L, cols[k % 4], pts[-1], 0.028, 8, 5)
    for p, q in zip(pts, pts[1:]): tube(L, "cord", p, q, 0.003, 4, False)
    L.save("emissive.obj")
    return COL
