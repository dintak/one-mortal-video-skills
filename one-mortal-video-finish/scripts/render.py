"""Render a portable image/video timeline with mixed audio and subtitles."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path


def positive(value: object, label: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (result < 0 if allow_zero else result <= 0):
        raise ValueError(f"{label} must be {'nonnegative' if allow_zero else 'positive'}")
    return result


def asset(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("asset path must be a nonempty string")
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError(f"use a project-relative asset path: {value}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"asset is missing or outside project: {value}")
    return resolved


def command(args: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args[0]}\n{result.stderr[-2000:]}")


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate", "-of", "json", str(path)],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def media_duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def load_project(path: Path) -> dict:
    path = path.resolve()
    root = path.parent
    data = json.loads(path.read_text(encoding="utf-8"))
    canvas = data["canvas"]
    width = int(positive(canvas["width"], "canvas.width"))
    height = int(positive(canvas["height"], "canvas.height"))
    fps = int(positive(canvas["fps"], "canvas.fps"))
    if width % 2 or height % 2 or not 1 <= fps <= 60:
        raise ValueError("canvas width/height must be even; fps must be 1–60")
    if width > 4096 or height > 4096:
        raise ValueError("canvas is larger than 4096 pixels")

    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ValueError("shots must be a nonempty list")
    ids = set()
    total_frames = 0
    normalized_shots = []
    for index, shot in enumerate(shots, 1):
        sid = str(shot.get("id", ""))
        if not sid or sid in ids:
            raise ValueError(f"shot {index} needs a unique id")
        ids.add(sid)
        source_kind = "image" if "image" in shot else "video" if "video" in shot else None
        if source_kind is None or ("image" in shot and "video" in shot):
            raise ValueError(f"{sid} needs exactly one image or video")
        source = asset(root, shot[source_kind])
        frames = round(positive(shot["duration"], f"{sid}.duration") * fps)
        if frames < 1:
            raise ValueError(f"{sid} is shorter than one frame")
        source_start = positive(shot.get("source_start", 0), f"{sid}.source_start", allow_zero=True)
        if source_kind == "video" and source_start + frames / fps > media_duration(source) + 0.08:
            raise ValueError(f"{sid} video is shorter than its requested shot")
        motion = shot.get("motion", "still")
        if motion not in {"still", "push"}:
            raise ValueError(f"{sid}.motion must be still or push")
        normalized_shots.append({"id": sid, "kind": source_kind, "path": source, "frames": frames, "source_start": source_start, "motion": motion})
        total_frames += frames
    total = total_frames / fps

    audio = []
    for index, track in enumerate(data.get("audio", []), 1):
        source = asset(root, track["file"])
        if not any(s.get("codec_type") == "audio" for s in probe(source).get("streams", [])):
            raise ValueError(f"audio {index} has no audio stream")
        start = positive(track["start"], f"audio {index}.start", allow_zero=True)
        source_start = positive(track.get("source_start", 0), f"audio {index}.source_start", allow_zero=True)
        gain = positive(track.get("gain", 1), f"audio {index}.gain", allow_zero=True)
        if start >= total or gain > 4:
            raise ValueError(f"audio {index} start or gain is invalid")
        available = media_duration(source) - source_start
        if available <= 0:
            raise ValueError(f"audio {index} starts beyond its file")
        requested = positive(track.get("duration", available), f"audio {index}.duration")
        duration = min(requested, available, total - start)
        audio.append({"path": source, "start": start, "source_start": source_start, "duration": duration, "gain": gain})

    subtitles = []
    for index, cue in enumerate(data.get("subtitles", []), 1):
        start = positive(cue["start"], f"subtitle {index}.start", allow_zero=True)
        end = positive(cue["end"], f"subtitle {index}.end")
        text = str(cue.get("text", "")).strip()
        if not text or not start < end <= total + 0.001:
            raise ValueError(f"subtitle {index} text or time is invalid")
        subtitles.append({"start": start, "end": end, "text": text})
    subtitles.sort(key=lambda c: c["start"])
    if any(a["end"] > b["start"] + 0.001 for a, b in zip(subtitles, subtitles[1:])):
        raise ValueError("subtitles overlap")

    return {"title": str(data.get("title", path.stem)), "root": root, "width": width, "height": height, "fps": fps, "shots": normalized_shots, "audio": audio, "subtitles": subtitles, "total": total}


def stamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    whole, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole:02},{milliseconds:03}"


def write_srt(cues: list[dict], path: Path) -> None:
    blocks = []
    for index, cue in enumerate(cues, 1):
        text = cue["text"].replace("\r", "")
        blocks.append(f"{index}\n{stamp(cue['start'])} --> {stamp(cue['end'])}\n{text}")
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def render_shots(project: dict, work: Path) -> Path:
    width, height, fps = project["width"], project["height"], project["fps"]
    entries = []
    for index, shot in enumerate(project["shots"], 1):
        part = work / f"shot_{index:04}.mp4"
        if shot["kind"] == "image":
            prefix = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-i", str(shot["path"])]
            if shot["motion"] == "push":
                visual = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},zoompan=z='min(zoom+0.00035,1.045)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={width}x{height}:fps={fps},format=yuv420p"
            else:
                visual = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p"
        else:
            prefix = ["ffmpeg", "-y", "-v", "error", "-ss", str(shot["source_start"]), "-i", str(shot["path"])]
            visual = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p"
        command(prefix + ["-vf", visual, "-frames:v", str(shot["frames"]), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(part)])
        if abs(media_duration(part) - shot["frames"] / fps) > 1 / fps + 0.02:
            raise RuntimeError(f"{shot['id']} rendered at the wrong duration")
        entries.append(f"file '{part.name}'")
    (work / "concat.txt").write_text("\n".join(entries) + "\n", encoding="utf-8")
    silent = work / "silent.mp4"
    command(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", str(silent)], cwd=work)
    if abs(media_duration(silent) - project["total"]) > 1 / fps + 0.03:
        raise RuntimeError("joined video has the wrong duration")
    return silent


def render_audio(project: dict, work: Path) -> Path:
    total = project["total"]
    args = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-t", str(total), "-i", "anullsrc=r=48000:cl=stereo"]
    filters = [f"[0:a]atrim=duration={total},asetpts=PTS-STARTPTS[base]"]
    labels = ["[base]"]
    for index, track in enumerate(project["audio"], 1):
        args += ["-ss", str(track["source_start"]), "-t", str(track["duration"]), "-i", str(track["path"])]
        delay = round(track["start"] * 1000)
        filters.append(f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={track['gain']},adelay={delay}:all=1,atrim=duration={total}[a{index}]")
        labels.append(f"[a{index}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,atrim=duration={total},alimiter=limit=0.95[mix]")
    output = work / "mix.m4a"
    command(args + ["-filter_complex", ";".join(filters), "-map", "[mix]", "-c:a", "aac", "-b:a", "160k", str(output)])
    return output


def render(project_path: Path, output: Path, force: bool = False) -> Path:
    project = load_project(project_path)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    final = output / "film.mp4"
    if final.exists() and not force:
        raise FileExistsError(f"{final} exists; use --force to replace it")
    with tempfile.TemporaryDirectory(prefix="render_", dir=output) as folder:
        work = Path(folder)
        write_srt(project["subtitles"], work / "captions.srt")
        silent = render_shots(project, work)
        audio = render_audio(project, work)
        staged = work / "film.mp4"
        args = ["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(audio)]
        if project["subtitles"]:
            args += ["-vf", "subtitles=captions.srt:force_style='FontName=DejaVu Sans,FontSize=24,Outline=2,Shadow=1'"]
        args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-t", str(project["total"]), "-movflags", "+faststart", str(staged)]
        command(args, cwd=work)
        if abs(media_duration(staged) - project["total"]) > 1 / project["fps"] + 0.03:
            raise RuntimeError("final video has the wrong duration")
        staged.replace(final)
        (work / "captions.srt").replace(output / "captions.srt")
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    path = render(args.project, args.out, args.force)
    print(json.dumps({"video": str(path), "srt": str(path.parent / "captions.srt")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
