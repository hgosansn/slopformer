#!/usr/bin/env python3
"""
Scan work/<character>/frames_* and generate/update characters/<character>/character.json.

Usage: python3 init_metadata.py --character trex [--fps 2]
"""
import json
import sys
from pathlib import Path
from PIL import Image

BASE = Path(__file__).parent

TYPE_HINTS = {
    "walk":   "locomotion",
    "run":    "locomotion",
    "right":  "locomotion",
    "left":   "locomotion",
    "turn":   "transition",
    "idle":   "idle",
    "attack": "attack",
    "bite":   "attack",
    "roar":   "action",
    "eat":    "action",
    "die":    "reaction",
    "jump":   "action",
    "sleep":  "idle",
}

def guess_type(name):
    for key, t in TYPE_HINTS.items():
        if key in name:
            return t
    return "action"

def guess_loop(anim_type):
    return anim_type in ("locomotion", "idle")

def get_frame_size(frames_dir):
    frames = sorted(frames_dir.glob("*.png")) + sorted(frames_dir.glob("*.jpg"))
    if not frames:
        return None
    with Image.open(frames[0]) as img:
        return {"width": img.width, "height": img.height}

def count_frames(frames_dir):
    return len(list(frames_dir.glob("*.png"))) + len(list(frames_dir.glob("*.jpg")))

def pop_arg(args, flag):
    if flag in args:
        i = args.index(flag)
        val = args[i + 1]
        args.pop(i); args.pop(i)
        return val
    return None

args = sys.argv[1:]
character   = pop_arg(args, "--character") or "unknown"
default_fps = int(pop_arg(args, "--fps") or 2)

work_dir = BASE / "work" / character
out_dir  = BASE / "characters" / character
out_dir.mkdir(parents=True, exist_ok=True)
meta_path = out_dir / "character.json"

if meta_path.exists():
    with open(meta_path) as f:
        meta = json.load(f)
    print(f"Loaded existing {meta_path}")
else:
    meta = {"character": character, "animations": {}}

print(f"\nScanning {work_dir} ...\n")

for fd in sorted(work_dir.glob("frames_*")):
    anim_name   = fd.name.replace("frames_", "")
    frame_count = count_frames(fd)
    if frame_count == 0:
        continue

    if anim_name in meta["animations"]:
        meta["animations"][anim_name]["frames"] = frame_count
        print(f"  Updated: {anim_name} ({frame_count} frames)")
    else:
        anim_type = guess_type(anim_name)
        entry = {
            "type":       anim_type,
            "frames":     frame_count,
            "fps":        default_fps,
            "loop":       guess_loop(anim_type),
            "frames_dir": f"work/{character}/{fd.name}",
            "spritesheet": f"characters/{character}/sprites/{anim_name}.png",
        }
        size = get_frame_size(fd)
        if size:
            entry["frame_size"] = size
        meta["animations"][anim_name] = entry
        print(f"  Added:   {anim_name} ({frame_count} frames, type={anim_type})")

with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nSaved -> {meta_path}")
print(f"Animations: {list(meta['animations'].keys())}")
