# Character Sprite Sheet Generator Pipeline

## Overview

Single-prompt pipeline: describe a character → get a full sprite sheet set ready for use in a game.

---

## Folder Structure

```
project/
├── generate_video.py
├── extract_frames.py
├── remove_bg.py
├── init_metadata.py
├── build_spritesheet.py
├── index.html
├── PIPELINE.md
├── .gitignore
│
├── work/                        ← gitignored (intermediate files)
│   └── <character>/
│       ├── base_sprite.png
│       ├── walk_right.mp4
│       ├── walk_left.mp4
│       ├── turn.mp4
│       ├── <action>.mp4
│       ├── frames_walk_right/   ← transparent PNGs
│       ├── frames_walk_left/
│       ├── frames_turn/
│       └── frames_<action>/
│
└── characters/                  ← committed (final output)
    └── <character>/
        ├── character.json       ← animation metadata
        └── sprites/
            ├── walk_right.png
            ├── walk_left.png
            ├── turn.png
            └── <action>.png
```

---

## Pipeline Steps

### 1. Character Description
- User provides a text description of a character
- LLM expands the description into a detailed prompt optimized for pixel art generation
- Extracts personality traits to determine relevant action animations later

### 2. Generate Base Pixel Art
- Use the optimized prompt to generate a pixel art sprite of the character
- Style: pixel art, white background, side-view, game-ready
- Output: `work/<character>/base_sprite.png`

### 3. Generate Videos
- Script: `generate_video.py` — uses **Wan2.1-1.3B** locally (~12GB VRAM, model downloads ~6GB on first run)
- Built-in prompt templates for: `walk_right`, `walk_left`, `turn`, `idle`, `attack`, `jump`, `roar`
  ```bash
  # Single animation
  python3 generate_video.py --character trex --image work/trex/base_sprite.png --animation walk_right

  # All animations defined in character.json
  python3 generate_video.py --character trex --image work/trex/base_sprite.png --all

  # Custom prompt or fixed seed
  python3 generate_video.py --character trex --image work/trex/base_sprite.png --animation jump --seed 42
  python3 generate_video.py --character trex --image work/trex/base_sprite.png --animation walk_right --frames 33 --fps 8
  ```
- Output: `work/<character>/<animation>.mp4`

### 4. Split Videos into Frames
- Script: `extract_frames.py`
  ```bash
  python3 extract_frames.py work/trex/walk_right.mp4 work/trex/walk_left.mp4 work/trex/turn.mp4 --character trex --fps 2
  ```
- Output: `work/<character>/frames_<name>/frame_XXXX.jpg`

### 5. Remove Background from All Frames
- Strip white/noisy background, output transparent PNGs in-place (jpg → png)
- Uses `rembg` — handles watermarks and compression artifacts, not just solid white
- Script: `remove_bg.py`
  ```bash
  python3 remove_bg.py --character trex
  ```
- Output: `work/<character>/frames_<name>/frame_XXXX.png`

### 6. Initialize / Update Metadata
- Scans `work/<character>/frames_*`, generates `characters/<character>/character.json`
- Re-run after adding any new animation to auto-update frame counts
- Edit `character.json` manually to correct types, loop flags, names
- Script: `init_metadata.py`
  ```bash
  python3 init_metadata.py --character trex --fps 2
  ```
- Output: `characters/<character>/character.json`

### 7. Build Sprite Sheets
- Reads `characters/<character>/character.json` for animation config
- Finds tightest bounding box across all frames (consistent crop, no clipping)
- Pads to square, resizes to target size, stitches into horizontal strip
- Script: `build_spritesheet.py`
  ```bash
  python3 build_spritesheet.py --character trex --size 128 --padding 2
  python3 build_spritesheet.py --character trex --size 128 --cols 8        # grid mode
  python3 build_spritesheet.py --character trex --animation walk_right     # single
  ```
- Updates `character.json` with final `frame_size`
- Output: `characters/<character>/sprites/<name>.png`

### 8. Preview
- Open `index.html` in browser to see the character animated live
- Reads sprites from `characters/<character>/sprites/`

---

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `generate_video.py` | Generate animation videos from base sprite (Wan2.1-1.3B) | `python3 generate_video.py --character trex --image work/trex/base_sprite.png --all` |
| `extract_frames.py` | Extract frames from video at given FPS | `python3 extract_frames.py work/trex/walk.mp4 --character trex --fps 2` |
| `remove_bg.py` | Remove background from all frames in work dir (rembg) | `python3 remove_bg.py --character trex` |
| `init_metadata.py` | Scan work frame dirs, generate/update character.json | `python3 init_metadata.py --character trex` |
| `build_spritesheet.py` | Build sprite sheets, output to characters/ | `python3 build_spritesheet.py --character trex --size 128` |

---

## Tech Stack

- **Video generation**: Wan2.1-1.3B (local, HuggingFace) via `diffusers`
- **Frame extraction**: `ffmpeg` via `extract_frames.py`
- **Background removal**: `rembg` via `remove_bg.py`
- **Metadata**: `character.json` — generated/updated by `init_metadata.py`
- **Sprite sheet stitching**: `Pillow` via `build_spritesheet.py`
- **Preview**: `index.html` (Canvas + JS)
- **Image generation**: TBD (Replicate / fal.ai / OpenAI / local)
- **LLM for prompt expansion**: TBD (Claude / OpenAI)
- **App interface**: TBD (Desktop / Web / CLI)
