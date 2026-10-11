#!/usr/bin/env python3
"""Generates every model, texture and sound of DrumRoom3D and patches the kit/collision data into main.lua.
    pip install pillow numpy
    python tools/generate_all.py
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshlib, kit, room, sounds

NAMES = {"kick": "Bass drum", "snare": "Snare", "tom1": "High tom", "tom2": "Mid tom", "floortom": "Floor tom", "hihat": "Hi-hat",
         "crash": "Crash", "ride": "Ride", "kickpedal": "Kick pedal", "hatpedal": "Hi-hat pedal"}
def f(v): return "{%.3f, %.3f, %.3f}" % tuple(v)

def main():
    for d in (meshlib.MODELS, meshlib.TEXTURES, meshlib.SOUNDS): os.makedirs(d, exist_ok=True)
    print("room"); room.textures(); col = room.models()
    print("kit"); meta = kit.build_all(meshlib.TEXTURES); col += kit.kit_colliders()
    print("sounds"); sounds.build_all()
    rows = []
    for k, p in meta.items():
        if p["shape"] == "cyl": rows.append('    %s = { name = "%s", shape = "cyl", c = %s, a = %s, r = %.3f, h = %.3f },' % (k, NAMES[k], f(p["c"]), f(p["a"]), p["r"], p["h"]))
        else: rows.append('    %s = { name = "%s", shape = "sphere", c = %s, r = %.3f },' % (k, NAMES[k], f(p["c"]), p["r"]))
    data = "-- BEGIN KIT_DATA\nlocal SUN = %s\nlocal PARTS = {\n%s\n}\nlocal colliders = {\n%s\n}\n-- END KIT_DATA" % (
        f(room.SUN), "\n".join(rows), "\n".join("    { %.2f, %.2f, %.2f, %.2f }," % c for c in col))
    p = os.path.join(meshlib.ROOT, "main.lua"); s = open(p).read()
    s = re.sub(r"-- BEGIN KIT_DATA.*?-- END KIT_DATA", lambda _: data, s, flags=re.S); open(p, "w").write(s)
    print("patched main.lua with", len(meta), "parts and", len(col), "colliders\ndone.")
main()
