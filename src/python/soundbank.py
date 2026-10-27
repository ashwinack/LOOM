# Plucked-string sound bank: one wav, fixed-length slots, [note][layer]
import numpy as np, wave, os

SR = 44100
SLOT = 3.0          # seconds per slot
LOW, HIGH = 28, 100 # MIDI range in the bank
LAYERS = 2          # 0 = soft, 1 = bright

def bank_path():
    return project.folder + '/audio/string_bank.wav'

def slot_offset(midi, layer):
    midi = int(min(max(midi, LOW), HIGH))
    return ((midi - LOW)*LAYERS + layer) * SLOT

def _pluck(f, bright, rng):
    n = int(SR*SLOT)
    t = np.arange(n)/SR
    y = np.zeros(n)
    H = int(min(28, 15000.0/f))
    B = 0.00012                     # slight stiffness -> inharmonic shimmer
    pos = 0.13 if bright else 0.22  # pluck position shapes the timbre
    tilt = 0.10 if bright else 0.32
    for h in range(1, H+1):
        fh = h*f*np.sqrt(1 + B*h*h)
        amp = abs(np.sin(np.pi*h*pos))/h * np.exp(-tilt*(h-1))
        dec = 0.8 + 0.30*h + f/450.0
        y += amp*np.sin(2*np.pi*fh*t + rng.uniform(0, 6.28))*np.exp(-dec*t)
    nl = int(0.008*SR)                                   # pick noise transient
    y[:nl] += rng.normal(0, 1, nl)*np.exp(-np.arange(nl)/(0.0015*SR))*(0.25 if bright else 0.08)
    y *= np.minimum(1.0, t/0.002)                        # 2 ms attack, no click
    fo = int(0.3*SR); y[-fo:] *= np.linspace(1, 0, fo)   # clean tail inside the slot
    return y/ (np.max(np.abs(y)) + 1e-9) * 0.85

def build(force=False):
    path = bank_path()
    if os.path.exists(path) and not force:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = np.random.default_rng(7)
    parts = []
    for m in range(LOW, HIGH+1):
        f = 440.0*2**((m-69)/12.0)
        for layer in range(LAYERS):
            parts.append(_pluck(f, layer == 1, rng))
    data = (np.concatenate(parts)*32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())
    return path
