"""Decode a finished film, check its timeline, and make a shot contact sheet."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from render import load_project, media_duration, probe, stamp


def review(project_path: Path, film: Path, output: Path) -> Path:
    project = load_project(project_path)
    film = film.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    metadata = probe(film)
    video = next((stream for stream in metadata["streams"] if stream["codec_type"] == "video"), None)
    audio = next((stream for stream in metadata["streams"] if stream["codec_type"] == "audio"), None)
    actual = media_duration(film)
    errors = []
    if not video or (video["width"], video["height"]) != (project["width"], project["height"]):
        errors.append("video stream or canvas mismatch")
    if not audio:
        errors.append("audio stream missing")
    if abs(actual - project["total"]) > 1 / project["fps"] + 0.05:
        errors.append("duration mismatch")
    captions = film.parent / "captions.srt"
    if not captions.is_file():
        errors.append("captions.srt missing")
    else:
        content = captions.read_text(encoding="utf-8-sig")
        for index, cue in enumerate(project["subtitles"], 1):
            expected = f"{index}\n{stamp(cue['start'])} --> {stamp(cue['end'])}\n{cue['text']}"
            if expected not in content:
                errors.append(f"subtitle {index} differs from project")
    decoded = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(film), "-f", "null", "-"], capture_output=True, text=True)
    if decoded.returncode:
        errors.append("decode failed: " + decoded.stderr[-500:])
    sheet = Image.new("RGB", (640, 300 * len(project["shots"])), "#202020")
    pen = ImageDraw.Draw(sheet)
    elapsed = 0.0
    for index, shot in enumerate(project["shots"]):
        offset = elapsed + shot["frames"] / project["fps"] / 2
        frame = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(offset), "-i", str(film), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if frame.returncode or not frame.stdout:
            errors.append(f"could not sample {shot['id']}")
        else:
            from io import BytesIO
            with Image.open(BytesIO(frame.stdout)) as source:
                thumb = source.convert("RGB")
                thumb.thumbnail((400, 265))
                sheet.paste(thumb, ((640 - thumb.width) // 2, index * 300))
        pen.text((20, index * 300 + 270), f"{shot['id']}   {offset:.2f}s", fill="white")
        elapsed += shot["frames"] / project["fps"]
    contact = output / "contact.png"
    sheet.save(contact)
    report = {"passed": not errors, "errors": errors, "expected_seconds": project["total"], "actual_seconds": actual, "shot_count": len(project["shots"]), "contact": str(contact), "film": str(film)}
    path = output / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("film", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = review(args.project, args.film, args.out)
    print(report.read_text(encoding="utf-8"))
    if not json.loads(report.read_text(encoding="utf-8"))["passed"]:
        raise SystemExit(1)
