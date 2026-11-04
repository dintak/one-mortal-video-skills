"""Draw a simple, editable SVG floor plan from a scene layout JSON file."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path


def number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.layout.read_text(encoding="utf-8"))
    room = data["room"]
    width = number(room["width"], "room.width")
    height = number(room["height"], "room.height")
    if width <= 0 or height <= 0:
        raise ValueError("room dimensions must be positive")

    margin = 65
    scale = min(900 / width, 600 / height)
    svg_width = math.ceil(width * scale + 2 * margin)
    svg_height = math.ceil(height * scale + 2 * margin)

    def xy(x: object, y: object) -> tuple[float, float]:
        px = number(x, "x")
        py = number(y, "y")
        if not 0 <= px <= width or not 0 <= py <= height:
            raise ValueError(f"position ({px}, {py}) is outside the room")
        return margin + px * scale, margin + py * scale

    title = html.escape(str(data.get("title", "Scene layout")))
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#bc7335"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#f5f1e8"/>',
        f'<text x="{margin}" y="35" font-family="sans-serif" font-size="22" fill="#263238">{title}</text>',
        f'<rect x="{margin}" y="{margin}" width="{width * scale:.2f}" height="{height * scale:.2f}" fill="#fff" stroke="#263238" stroke-width="3"/>',
    ]

    for item in data.get("objects", []):
        cx, cy = xy(item["x"], item["y"])
        w = number(item["width"], "object.width") * scale
        h = number(item["height"], "object.height") * scale
        if w <= 0 or h <= 0:
            raise ValueError("object dimensions must be positive")
        label = html.escape(str(item.get("label", "Object")))
        elements.append(f'<rect x="{cx-w/2:.2f}" y="{cy-h/2:.2f}" width="{w:.2f}" height="{h:.2f}" rx="4" fill="#b9c7cf" stroke="#47606c" stroke-width="2"/>')
        elements.append(f'<text x="{cx:.2f}" y="{cy+5:.2f}" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#102a35">{label}</text>')

    for index, actor in enumerate(data.get("actors", [])):
        cx, cy = xy(actor["x"], actor["y"])
        color = ["#3d7a86", "#9b5c7a", "#678b46", "#655fa3"][index % 4]
        label = html.escape(str(actor.get("label", f"Actor {index+1}")))
        elements.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="17" fill="{color}" stroke="#fff" stroke-width="2"/>')
        elements.append(f'<text x="{cx:.2f}" y="{cy+36:.2f}" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#263238">{label}</text>')

    for index, camera in enumerate(data.get("cameras", [])):
        cx, cy = xy(camera["x"], camera["y"])
        tx, ty = xy(camera["target_x"], camera["target_y"])
        label = html.escape(str(camera.get("label", f"C{index+1}")))
        elements.append(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{tx:.2f}" y2="{ty:.2f}" stroke="#bc7335" stroke-width="3" marker-end="url(#arrow)"/>')
        elements.append(f'<rect x="{cx-18:.2f}" y="{cy-13:.2f}" width="36" height="26" rx="5" fill="#bc7335"/>')
        elements.append(f'<text x="{cx:.2f}" y="{cy+5:.2f}" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#fff">{label}</text>')

    unit = html.escape(str(room.get("unit", "unit")))
    elements.append(f'<text x="{margin}" y="{svg_height-18}" font-family="sans-serif" font-size="14" fill="#52636b">{width:g} × {height:g} {unit}</text>')
    elements.append("</svg>")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(elements) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
