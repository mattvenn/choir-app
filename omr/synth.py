"""Render a music21 part to a simple organ-ish WAV (no soundfont needed)."""
import wave
from pathlib import Path

import numpy as np

RATE = 44100
HARMONICS = [1.0, 0.5, 0.3, 0.15, 0.08]


def tone(freq: float, seconds: float) -> np.ndarray:
    t = np.arange(int(seconds * RATE)) / RATE
    wav = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(HARMONICS))
    env = np.ones_like(t)
    attack, release = int(0.02 * RATE), min(int(0.08 * RATE), len(t) // 2)
    env[:attack] = np.linspace(0, 1, attack)[:len(env)]
    if release:
        env[-release:] *= np.linspace(1, 0, release)
    return wav * env


def render(part, tempo: float, out: Path) -> Path:
    sec_per_beat = 60.0 / tempo
    notes = part.stripTies().flatten().notes
    end = max((n.offset + n.quarterLength for n in notes), default=0)
    buf = np.zeros(int((end * sec_per_beat + 1) * RATE))
    for n in notes:
        start = int(n.offset * sec_per_beat * RATE)
        for p in n.pitches:
            w = tone(p.frequency, n.quarterLength * sec_per_beat)
            buf[start:start + len(w)] += w
    buf /= max(np.abs(buf).max(), 1e-9) / 0.8
    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes((buf * 32767).astype(np.int16).tobytes())
    return out
