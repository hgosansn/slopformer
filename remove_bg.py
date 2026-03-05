#!/usr/bin/env python3
"""
Remove background from all frames in work/<character>/frames_*/
Rewrites in-place: jpg -> png with transparency.

Usage: python3 remove_bg.py --character trex
"""
import sys
from pathlib import Path
from rembg import remove
from PIL import Image

BASE = Path(__file__).parent

def pop_arg(args, flag):
    if flag in args:
        i = args.index(flag)
        val = args[i + 1]
        args.pop(i); args.pop(i)
        return val
    return None

args = sys.argv[1:]
character = pop_arg(args, "--character") or "unknown"
work_dir  = BASE / "work" / character

if not work_dir.exists():
    print(f"Work dir not found: {work_dir}")
    sys.exit(1)

frame_dirs = sorted(work_dir.glob("frames_*"))
if not frame_dirs:
    print(f"No frames_* directories found in {work_dir}")
    sys.exit(1)

for folder in frame_dirs:
    frames = sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.png"))
    print(f"\n{folder.name}: {len(frames)} frames")
    for f in frames:
        print(f"  {f.name}", end=" ... ", flush=True)
        img = Image.open(f)
        out = remove(img)
        out_path = f.with_suffix(".png")
        out.save(out_path)
        if f.suffix == ".jpg":
            f.unlink()
        print("done")

print("\nAll done.")
