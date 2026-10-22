#!/usr/bin/python3
"""Synthesize the Rosary login chime: two soft church bells in a quiet room.

A slow C5 bell, then a lower G4 answer, with inharmonic partials and a little
air around the strike. Written to extras/login.wav.
"""
from __future__ import annotations

from pathlib import Path
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "extras" / "login.wav"
SR = 44100
DURATION = 7.0


def bell(t: np.ndarray, f0: float, gain: float) -> np.ndarray:
    # Church-bell partials: hum, prime, minor tierce, quint, nominal, upper.
    partials = [
        (0.5, 0.55, 1.1),
        (1.0, 0.80, 0.75),
        (1.19, 0.42, 1.5),
        (1.5, 0.30, 1.9),
        (2.0, 0.55, 0.95),
        (2.52, 0.22, 2.6),
        (3.01, 0.12, 3.1),
        (4.07, 0.07, 3.8),
    ]
    out = np.zeros_like(t)
    for ratio, amp, decay in partials:
        out += amp * np.sin(2 * np.pi * f0 * ratio * t) * np.exp(-t / decay)
    # A breath of filtered strike noise, gone in a moment.
    rng = np.random.default_rng(int(f0 * 1000))
    noise = rng.normal(0, 1, t.size)
    kernel = np.hanning(24)
    noise = np.convolve(noise, kernel / kernel.sum(), mode="same")
    out += 0.045 * noise * np.exp(-t / 0.035)
    return gain * out


def main():
    t = np.arange(int(SR * DURATION)) / SR
    mix = bell(t, 523.25, 0.34)
    # The answer enters after 2.35 s, a fifth below.
    delayed = np.zeros_like(mix)
    start = int(2.35 * SR)
    tt = np.arange(mix.size - start) / SR
    delayed[start:] = bell(tt, 392.00, 0.26)
    mix += delayed

    # A very low wooden room tone.
    mix += 0.035 * np.sin(2 * np.pi * 98.0 * t) * np.exp(-t / 2.8)

    # Soft attack, long tail, and a clean fade at the end.
    attack = np.clip(t / 0.004, 0, 1)
    tail = np.clip((DURATION - t) / 0.8, 0, 1)
    mix *= attack * tail
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.72

    pcm = (mix * 32767).astype("<i2")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
