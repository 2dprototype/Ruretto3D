"""sounds.py - synthesises every drum sample (numpy only) into assets/sounds/*.wav (44.1 kHz, 16-bit mono)."""
import os, wave
import numpy as np
from meshlib import SOUNDS

SR = 44100
rng = np.random.RandomState(5)

def T(sec): return np.arange(int(SR*sec))/SR
def noise(n): return rng.uniform(-1, 1, n)
def filt(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR); g = np.ones_like(f)
    if lo: g *= np.clip((f - lo*0.7)/(lo*0.3), 0, 1)
    if hi: g *= np.clip((hi*1.3 - f)/(hi*0.3), 0, 1)
    return np.fft.irfft(X*g, len(x))
def sweep(t, f0, f1, tau): return np.sin(2*np.pi*np.cumsum(f1 + (f0 - f1)*np.exp(-t/tau))/SR)
def fin(x, peak=0.9):
    x = x/ (np.max(np.abs(x)) + 1e-9)*peak; n = len(x); k = int(0.004*SR); x[:k] *= np.linspace(0, 1, k)
    k = int(min(0.05, n/SR/4)*SR); x[-k:] *= np.linspace(1, 0, k); return x

def kick():
    t = T(0.6); body = sweep(t, 150, 48, 0.03)*np.exp(-t/0.17); click = filt(noise(len(t)), 1500, 6000)*np.exp(-t/0.004)*0.5
    return np.tanh(1.8*(body + click))
def snare():
    t = T(0.5); tone = (np.sin(2*np.pi*185*t)*0.6 + np.sin(2*np.pi*330*t)*0.3)*np.exp(-t/0.06)
    return tone + filt(noise(len(t)), 1800, 9500)*np.exp(-t/0.12)*0.9
def rim():
    t = T(0.25); return (np.sin(2*np.pi*1750*t)*0.4 + np.sin(2*np.pi*480*t)*0.6)*np.exp(-t/0.02) + filt(noise(len(t)), 900, 7000)*np.exp(-t/0.012)*0.7
def tom(f, tau=0.3):
    t = T(0.9); b = sweep(t, f*1.5, f, 0.035)*np.exp(-t/tau); return b + 0.25*np.sin(2*np.pi*f*1.6*t)*np.exp(-t/0.1) + filt(noise(len(t)), 2000, 8000)*np.exp(-t/0.006)*0.35
def metal(t, base=1.0):
    return sum(np.sign(np.sin(2*np.pi*f*base*t)) for f in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0))/6
def hat(decay, sec):
    t = T(sec); return filt(metal(t, 1.0)*0.7 + noise(len(t))*0.5, 6500, None)*np.exp(-t/decay)
def crash():
    t = T(2.6); x = filt(noise(len(t)), 2500, 14000)*np.exp(-t/0.9)*0.6
    for _ in range(40): x += np.sin(2*np.pi*rng.uniform(350, 9000)*t + rng.uniform(0, 6))*np.exp(-t/rng.uniform(0.4, 1.6))*0.05
    return x*(1 - np.exp(-t/0.004))
def ride():
    t = T(2.2); x = filt(noise(len(t)), 4500, 14000)*np.exp(-t/0.25)*0.35
    for f in (420, 790, 1330, 2150, 3180, 4400, 5900): x += np.sin(2*np.pi*f*t*rng.uniform(.99, 1.01))*np.exp(-t/rng.uniform(.7, 1.4))*0.18
    return x + np.sin(2*np.pi*3300*t)*np.exp(-t/0.35)*0.25
def ride_bell():
    t = T(1.6); x = sum(np.sin(2*np.pi*f*t)*np.exp(-t/tau)*a for f, tau, a in ((1900, .9, 1), (2840, .6, .6), (4100, .4, .5), (5250, .25, .3)))
    return x + filt(noise(len(t)), 5000, 12000)*np.exp(-t/0.02)*0.4

SAMPLES = {"kick": kick, "snare": snare, "snare_rim": rim, "tom1": lambda: tom(210, .26), "tom2": lambda: tom(155, .3), "floortom": lambda: tom(95, .42),
           "hat_closed": lambda: hat(0.03, 0.25), "hat_open": lambda: hat(0.35, 1.3), "hat_pedal": lambda: hat(0.012, 0.12),
           "crash": crash, "ride": ride, "ride_bell": ride_bell}

def build_all():
    os.makedirs(SOUNDS, exist_ok=True)
    for name, fn in SAMPLES.items():
        x = fin(fn()); pcm = (x*32767).astype("<i2")
        with wave.open(os.path.join(SOUNDS, name + ".wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        print("  sound", name + ".wav", round(len(x)/SR, 2), "s")
