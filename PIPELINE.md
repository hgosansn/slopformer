# SlopFormer Pipeline

## Overview

End-to-end workflow to turn a character concept into game-ready sprite sheets, then preview it in the web demo.

## Project Layout

```
project/
├── generate_video.py
├── extract_frames.py
├── remove_bg.py
├── init_metadata.py
├── build_spritesheet.py
├── index.html
├── PIPELINE.md
├── README.md
├── .github/workflows/pages.yml
│
├── work/                        # gitignored intermediates
│   └── <character>/
│       ├── <animation>.mp4
│       └── frames_<animation>/
│
└── characters/                  # committed outputs
    └── <character>/
        ├── character.json
        └── sprites/
            └── <animation>.png
```

## Pipeline Steps

### 1. Generate video clips

Local (CogVideoX, lower-cost, variable quality):

```bash
python3 generate_video.py --character trex --image work/trex/frames_right/frame_0001.png --animation jump
```

Optional cloud route (higher quality):
- Generate clip with Sora API.
- Save to `work/<character>/<animation>.mp4`.

### 2. Extract frames at target fps

Use lower fps when you want fewer frames to curate manually.

```bash
python3 extract_frames.py work/trex/jump.mp4 --character trex --fps 4
```

Output:
- `work/trex/frames_jump/frame_0001.jpg ...`

### 3. Curate frames manually

Delete bad/duplicate frames from `work/<character>/frames_<animation>/`.

### 4. Remove backgrounds

```bash
python3 remove_bg.py --character trex
```

Output:
- JPG frames are converted to transparent PNGs in-place.

### 5. Refresh metadata

```bash
python3 init_metadata.py --character trex --fps 4
```

This updates frame counts and keeps animation entries synced.

### 6. Build spritesheet

```bash
python3 build_spritesheet.py --character trex --animation jump --size 128
```

Output:
- `characters/trex/sprites/jump.png`

### 7. Preview in browser

Open `index.html` (or the GitHub Pages URL).

Current demo features:
- Character dropdown (extensible list)
- Random jumps
- Direction-aware jump flip when moving left
- Animated title + footer links

## Script Reference

| Script | Purpose |
|---|---|
| `generate_video.py` | Generate animation mp4 clips (CogVideoX local pipeline) |
| `extract_frames.py` | Split mp4 into frame images at target fps |
| `remove_bg.py` | Remove white/noisy backgrounds with `rembg` |
| `init_metadata.py` | Update `character.json` from frame folders |
| `build_spritesheet.py` | Build spritesheets from frame folders |

## Deployment

GitHub Pages deploys from `main` through:
- `.github/workflows/pages.yml`

Live site:
- `https://hgosansn.github.io/slopformer/`
