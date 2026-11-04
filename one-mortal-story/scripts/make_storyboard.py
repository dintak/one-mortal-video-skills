"""Turn a shot list into placeholder cards and a renderable project.json."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int):
    for name in ("C:/Windows/Fonts/msjh.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def wrap(text: str, length: int) -> list[str]:
    return [text[pos:pos + length] for pos in range(0, len(text), length)] or [""]


def make(source: Path, output: Path) -> Path:
    data = json.loads(source.resolve().read_text(encoding="utf-8"))
    output = output.resolve()
    canvas = data["canvas"]
    width, height, fps = int(canvas["width"]), int(canvas["height"]), int(canvas["fps"])
    if width < 320 or height < 320 or width % 2 or height % 2 or not 1 <= fps <= 60:
        raise ValueError("invalid canvas")
    shots = data.get("shots", [])
    if not shots:
        raise ValueError("shot list is empty")
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    timeline = {"title": data.get("title", "Storyboard"), "canvas": canvas, "shots": [], "audio": [], "subtitles": []}
    elapsed = 0.0
    for index, shot in enumerate(shots, 1):
        sid, duration = str(shot["id"]), float(shot["duration"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(f"invalid duration: {sid}")
        scene, action, dialogue = (str(shot.get(key, "")) for key in ("scene", "action", "dialogue"))
        image = Image.new("RGB", (width, height), "#1e3040")
        draw = ImageDraw.Draw(image)
        draw.rectangle((width * 0.06, height * 0.08, width * 0.94, height * 0.91), outline="#e9bc73", width=4)
        size = max(18, int(width / 18))
        large, small = font(size), font(max(16, int(size * 0.65)))
        y = int(height * 0.17)
        for text, face, color in ((sid, large, "#e9bc73"), (scene, large, "white"), (action, small, "#e3e8eb"), (dialogue, small, "#e9bc73")):
            for line in wrap(text, max(8, int(width / size * 1.5))):
                draw.text((int(width * 0.1), y), line, font=face, fill=color)
                y += int(size * 1.5)
            y += int(size * 0.7)
        filename = f"{index:03}_{sid}.png"
        image.save(assets / filename)
        timeline["shots"].append({"id": sid, "duration": duration, "image": f"assets/{filename}", "motion": "still"})
        if dialogue:
            timeline["subtitles"].append({"start": elapsed, "end": elapsed + duration, "text": dialogue})
        elapsed += duration
    destination = output / "project.json"
    destination.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("storyboard", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(make(args.storyboard, args.out))
