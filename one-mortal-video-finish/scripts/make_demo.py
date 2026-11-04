"""Create a small self-contained film project for testing the renderer."""

from __future__ import annotations

import argparse
import json
import math
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def card(path: Path, color: tuple[int, int, int], heading: str) -> None:
    picture = Image.new("RGB", (720, 1280), color)
    pen = ImageDraw.Draw(picture)
    pen.rectangle((90, 360, 630, 900), outline="#ffffff", width=8)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 80) if Path("C:/Windows/Fonts/arial.ttf").is_file() else ImageFont.load_default()
    pen.text((360, 620), heading, fill="white", font=font, anchor="mm")
    picture.save(path)


def tone(path: Path) -> None:
    rate = 48000
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        for second in range(4):
            frequency = 330 if second < 2 else 440
            for index in range(rate):
                time = index / rate
                envelope = min(1, index / 2400, (rate - index) / 2400)
                sample = int(3500 * envelope * math.sin(2 * math.pi * frequency * time))
                output.writeframesraw(struct.pack("<h", sample))


def make_demo(root: Path) -> Path:
    root = root.resolve()
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    card(assets / "first.png", (26, 58, 91), "01")
    card(assets / "second.png", (98, 44, 61), "02")
    tone(assets / "tone.wav")
    data = {
        "title": "Portable video demo",
        "canvas": {"width": 720, "height": 1280, "fps": 24},
        "shots": [
            {"id": "S01", "duration": 2, "image": "assets/first.png", "motion": "push"},
            {"id": "S02", "duration": 2, "image": "assets/second.png", "motion": "still"},
        ],
        "audio": [{"file": "assets/tone.wav", "start": 0, "gain": 0.5}],
        "subtitles": [
            {"start": 0.2, "end": 1.8, "text": "First shot"},
            {"start": 2.2, "end": 3.8, "text": "Second shot"},
        ],
    }
    project = root / "project.json"
    project.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return project


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(make_demo(args.out))
