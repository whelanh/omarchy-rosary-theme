#!/usr/bin/python3
"""Build the Rosary login chime from the CC0 mission-bell recording.

The source is craigsmith's "G20-12-Mission Bells" (Freesound 438227), a 1930s
optical-effects recording of individual mission bells. It opens with a spoken
slate; we skip that, keep the first four actual tolls, and fade out before the
next toll at 8.82 s. The gain matches the old chime's -20.4 LUFS.

    ./make-chime.py

Needs Python with numpy and ffmpeg to decode the source MP3.
"""
from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "art" / "originals" / "mission-bells.mp3"
OUT = ROOT / "extras" / "login.wav"
SR = 44100
START = 2.30       # after the spoken slate and its room tone
END = 8.70         # the next toll starts at about 8.82 s
FADE_IN = 0.02
FADE_OUT = 0.50
GAIN_DB = 5.0      # ~ -20.4 LUFS, the same integrated loudness as before


def main():
    if not SOURCE.exists():
        raise SystemExit(
            f"missing {SOURCE}\n"
            "Download the CC0 source from "
            "https://freesound.org/people/craigsmith/sounds/438227/")
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is needed to decode the source MP3")

    decoded = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(SOURCE),
         "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True,
    )
    x = np.frombuffer(decoded.stdout, dtype="<f4").copy()
    x = x[int(START * SR):int(END * SR)]

    fade_in = int(FADE_IN * SR)
    fade_out = int(FADE_OUT * SR)
    x[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
    x[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)
    x *= 10 ** (GAIN_DB / 20)

    peak = np.max(np.abs(x))
    if peak > 0.95:
        x *= 0.95 / peak

    pcm = np.clip(x * 32767, -32768, 32767).astype("<i2")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())
    print(f"wrote {OUT} ({x.size / SR:.2f} s, {OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
