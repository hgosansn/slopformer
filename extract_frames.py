#!/usr/bin/env python3
"""
Extract frames from video files at a given FPS into work/<character>/.

Usage:
    python3 extract_frames.py <video> [<video2> ...] --character trex [--fps 2]

Output frames go to work/<character>/frames_<videoname>/
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent

def extract(video_path: Path, character: str, fps: int):
    anim_name = video_path.stem
    out_dir = BASE / "work" / character / f"frames_{anim_name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pattern = str(out_dir / "frame_%04d.jpg")
    cmd = ["ffmpeg", "-i", str(video_path), "-vf", f"fps={fps}", out_pattern, "-y"]
    print(f"\n{video_path.name} -> work/{character}/frames_{anim_name}/")
    result = subprocess.run(cmd, capture_output=True, text=True)
    frames = list(out_dir.glob("frame_*.jpg"))
    print(f"  {len(frames)} frames extracted")
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-300:]}")

if __name__ == "__main__":
    args = sys.argv[1:]

    def pop_arg(flag):
        if flag in args:
            i = args.index(flag)
            val = args[i + 1]
            args.pop(i); args.pop(i)
            return val
        return None

    character = pop_arg("--character") or "unknown"
    fps       = int(pop_arg("--fps") or 2)

    if not args:
        print("Usage: python3 extract_frames.py <video> [<video2>...] --character NAME [--fps 2]")
        sys.exit(1)

    for a in args:
        p = Path(a)
        if not p.exists():
            print(f"File not found: {p}")
            continue
        extract(p, character, fps)

    print("\nAll done.")
