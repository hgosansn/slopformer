#!/usr/bin/env python3
"""
Build sprite sheets from frames, guided by characters/<character>/character.json.
Reads frames from work/<character>/frames_*/
Outputs sprites to characters/<character>/sprites/

Usage:
    python3 build_spritesheet.py --character trex [--size 128] [--padding 2] [--cols N] [--animation NAME]
"""
import json
import sys
from pathlib import Path
from PIL import Image

BASE = Path(__file__).parent

def resolve_frames_dir(frames_dir_value, character):
    p = Path(frames_dir_value)
    candidates = [
        BASE / p,
        BASE / "work" / character / p,
    ]
    for c in candidates:
        if c.exists():
            return c
    return BASE / p

def resolve_spritesheet_path(spritesheet_value, character):
    p = Path(spritesheet_value)
    if p.is_absolute():
        return p
    # Support both "characters/<name>/sprites/x.png" and "sprites/x.png".
    if str(p).startswith("sprites/"):
        return BASE / "characters" / character / p
    return BASE / p

def get_bbox_union(images):
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = 0, 0
    for img in images:
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])
    return None if min_x == float("inf") else (int(min_x), int(min_y), int(max_x), int(max_y))

def crop_to_square(img, bbox):
    cropped = img.crop(bbox)
    w, h = cropped.size
    size = max(w, h)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(cropped, ((size - w) // 2, (size - h) // 2))
    return square

def build_sheet(frames, target_size, padding, cols):
    n = len(frames)
    cols = min(cols, n)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA",
        (cols * target_size + (cols - 1) * padding,
         rows * target_size + (rows - 1) * padding),
        (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        resized = frame.resize((target_size, target_size), Image.LANCZOS)
        col, row = i % cols, i // cols
        sheet.paste(resized, (col * (target_size + padding), row * (target_size + padding)))
    return sheet

def process_animation(character, name, anim, target_size, padding, cols):
    frames_dir = resolve_frames_dir(anim["frames_dir"], character)
    if not frames_dir.exists():
        print(f"  [skip] {frames_dir} not found")
        return None

    frame_paths = sorted(frames_dir.glob("*.png"))
    if not frame_paths:
        print(f"  [skip] no PNG frames in {frames_dir}")
        return None

    print(f"  Loading {len(frame_paths)} frames...", end=" ", flush=True)
    images = [Image.open(p).convert("RGBA") for p in frame_paths]

    bbox = get_bbox_union(images)
    if not bbox:
        print("no content, skipping")
        return None

    cropped = [crop_to_square(img, bbox) for img in images]
    size = target_size or cropped[0].size[0]
    effective_cols = cols or len(cropped)

    sheet = build_sheet(cropped, size, padding, effective_cols)

    out_path = resolve_spritesheet_path(anim["spritesheet"], character)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    print(f"done -> {out_path.relative_to(BASE)}  ({sheet.width}x{sheet.height})")
    return {"width": size, "height": size}

def pop_arg(args, flag, default=None):
    if flag in args:
        i = args.index(flag)
        val = args[i + 1]
        args.pop(i); args.pop(i)
        return val
    return default

args = sys.argv[1:]
character   = pop_arg(args, "--character") or "unknown"
target_size = int(pop_arg(args, "--size") or 0) or None
padding     = int(pop_arg(args, "--padding") or 1)
cols        = int(pop_arg(args, "--cols") or 0)
only        = pop_arg(args, "--animation")

meta_path = BASE / "characters" / character / "character.json"
if not meta_path.exists():
    print(f"character.json not found at {meta_path}. Run init_metadata.py first.")
    sys.exit(1)

with open(meta_path) as f:
    meta = json.load(f)

print(f"\nBuilding sprite sheets for: {character}\n")

for name, anim in meta["animations"].items():
    if only and name != only:
        continue
    print(f"[{name}]")
    result = process_animation(character, name, anim, target_size, padding, cols)
    if result:
        anim["frame_size"] = result

with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)

print(f"\nUpdated {meta_path.relative_to(BASE)}")
