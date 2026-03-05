#!/usr/bin/env python3
"""
Generate animation videos from a base sprite using CogVideoX1.5-5B-I2V (image-to-video).
Downloads the model on first run (~6GB, cached to ~/.cache/huggingface).
Outputs videos to work/<character>/

Usage:
    python3 generate_video.py --character trex --image base_sprite.png --animation walk_right
    python3 generate_video.py --character trex --image base_sprite.png --all

Options:
    --character NAME    Character name (determines output folder)
    --image PATH        Input sprite image (PNG, white background)
    --animation NAME    One of: walk_right, walk_left, turn, idle, attack, jump, roar
    --prompt TEXT       Override the auto-generated prompt
    --all               Generate all animations defined in character.json
    --frames N          Number of frames to generate (default: 16)
    --fps N             FPS for output video (default: 8)
    --steps N           Inference steps (default: 20)
    --guidance-scale V  Prompt guidance strength (default: 4.5)
    --dynamic-cfg       Enable dynamic classifier-free guidance
    --seed N            Random seed for reproducibility
    --offload MODE      Offload mode: sequential, model, none (default: sequential)
    --decode-chunk-size VAE decode chunk size (default: 1, lower memory)
"""
import sys
import json
import argparse
import gc
import inspect
import torch
import imageio
import numpy as np
from pathlib import Path
from PIL import Image
from diffusers import CogVideoXImageToVideoPipeline

BASE = Path(__file__).parent

PROMPTS = {
    "walk_right": (
        "pixel art character walking to the right, smooth looping walk cycle, "
        "side view, white background, consistent style, no camera movement"
    ),
    "walk_left": (
        "pixel art character walking to the left, smooth looping walk cycle, "
        "side view, white background, consistent style, no camera movement"
    ),
    "turn": (
        "pixel art character turning around 180 degrees, side view, "
        "white background, smooth transition, consistent style, no camera movement"
    ),
    "idle": (
        "pixel art character idle breathing animation, subtle movement, "
        "side view, white background, looping, no camera movement"
    ),
    "attack": (
        "pixel art character performing an attack animation, "
        "side view, white background, snappy motion, no camera movement"
    ),
    "jump": (
        "pixel art character performs a clear jump cycle: crouch, takeoff, apex, "
        "landing, side view, fixed camera, white background, strong body motion, "
        "consistent character identity and silhouette"
    ),
    "roar": (
        "pixel art character roaring, head forward, mouth open, "
        "side view, white background, dramatic motion, no camera movement"
    ),
}

NEGATIVE_PROMPT = (
    "blurry, morphing, background change, camera pan, zoom, low quality, "
    "watermark, text, multiple characters, fade to white, blank frame, "
    "overexposed, washed out, ghosting, static pose"
)

def prepare_input_image(image_path):
    image = Image.open(image_path)
    if "A" in image.getbands():
        # Flatten transparency to white so the model does not hallucinate alpha-to-white fades.
        base = Image.new("RGB", image.size, (255, 255, 255))
        base.paste(image, mask=image.split()[-1])
        return base
    return image.convert("RGB")

def save_video_hq(frames, out_path, fps, crf, preset):
    writer = imageio.get_writer(
        str(out_path),
        fps=fps,
        codec="libx264",
        ffmpeg_params=["-crf", str(crf), "-preset", preset, "-pix_fmt", "yuv420p"],
    )
    try:
        for frame in frames:
            if isinstance(frame, Image.Image):
                arr = np.array(frame.convert("RGB"), dtype=np.uint8)
            else:
                arr = np.asarray(frame, dtype=np.uint8)
            writer.append_data(arr)
    finally:
        writer.close()

def load_pipeline(offload_mode):
    print("Loading CogVideoX1.5-5B-I2V model (downloads on first run, several GB)...")
    pipe = CogVideoXImageToVideoPipeline.from_pretrained(
        "zai-org/CogVideoX1.5-5B-I2V",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    if offload_mode == "sequential":
        pipe.enable_sequential_cpu_offload()
    elif offload_mode == "model":
        pipe.enable_model_cpu_offload()
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()
    pipe.enable_attention_slicing()
    print("Model loaded.\n")
    return pipe

def generate(
    pipe, image_path, character, anim_name, prompt,
    num_frames, fps, steps, guidance_scale, use_dynamic_cfg, seed, decode_chunk_size, crf, preset
):
    print(f"[{anim_name}] Generating {num_frames} frames...")
    print(f"  Prompt: {prompt[:80]}...")

    image = prepare_input_image(image_path)
    generator = torch.Generator().manual_seed(seed) if seed is not None else None

    call_kwargs = {
        "image": image,
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "num_frames": num_frames,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "use_dynamic_cfg": use_dynamic_cfg,
        "generator": generator,
    }
    # Keep compatibility across pipelines that may or may not expose this option.
    if "decode_chunk_size" in inspect.signature(pipe.__call__).parameters:
        call_kwargs["decode_chunk_size"] = decode_chunk_size

    with torch.inference_mode():
        output = pipe(**call_kwargs)

    out_dir = BASE / "work" / character
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{anim_name}.mp4"
    save_video_hq(output.frames[0], out_path, fps=fps, crf=crf, preset=preset)

    # Release memory between animations to avoid cumulative pressure.
    del output
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(f"  Saved -> {out_path.relative_to(BASE)}\n")
    return out_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--character", required=True)
    parser.add_argument("--image",     required=True)
    parser.add_argument("--animation", default=None)
    parser.add_argument("--prompt",    default=None)
    parser.add_argument("--all",       action="store_true")
    parser.add_argument("--frames",    type=int, default=16)
    parser.add_argument("--fps",       type=int, default=8)
    parser.add_argument("--steps",     type=int, default=20)
    parser.add_argument("--guidance-scale", type=float, default=4.5)
    parser.add_argument("--dynamic-cfg", action="store_true")
    parser.add_argument("--seed",      type=int, default=None)
    parser.add_argument("--offload",   choices=["sequential", "model", "none"], default="sequential")
    parser.add_argument("--decode-chunk-size", type=int, default=1)
    parser.add_argument("--crf",       type=int, default=16)
    parser.add_argument("--preset",    choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], default="slow")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        sys.exit(1)

    if args.all:
        meta_path = BASE / "characters" / args.character / "character.json"
        if not meta_path.exists():
            print("character.json not found. Run init_metadata.py first or use --animation.")
            sys.exit(1)
        with open(meta_path) as f:
            meta = json.load(f)
        animations = list(meta["animations"].keys())
    elif args.animation:
        animations = [args.animation]
    else:
        print("Specify --animation NAME or --all")
        sys.exit(1)

    pipe = load_pipeline(args.offload)

    for anim in animations:
        prompt = args.prompt or PROMPTS.get(anim, PROMPTS["walk_right"])
        generate(pipe, image_path, args.character, anim, prompt,
                 args.frames, args.fps, args.steps, args.guidance_scale, args.dynamic_cfg,
                 args.seed, args.decode_chunk_size, args.crf, args.preset)

    print("Next steps:")
    print(f"  python3 extract_frames.py work/{args.character}/*.mp4 --character {args.character} --fps {args.fps}")
    print(f"  python3 remove_bg.py --character {args.character}")
    print(f"  python3 init_metadata.py --character {args.character}")
    print(f"  python3 build_spritesheet.py --character {args.character} --size 128")
