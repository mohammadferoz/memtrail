import os
import yaml
import argparse
from dotenv import load_dotenv
from tqdm import tqdm

from .utils import ensure_dir, slugify
from .story_gen import generate_story
from .scene_builder import build_scenes
from .image_gen import generate_image
from .tts import synthesize
from .video import build_video, SceneSpec


def parse_args():
    p = argparse.ArgumentParser(description="Generate Instagram-ready cartoon story videos")
    p.add_argument("--topic", type=str, required=True)
    p.add_argument("--niche", type=str, required=True)
    p.add_argument("--duration", type=int, default=35)
    p.add_argument("--style", type=str, default="cute 2D cartoon")
    p.add_argument("--outdir", type=str, required=True)
    p.add_argument("--config", type=str, default=os.path.join(os.path.dirname(__file__), "config.yaml"))
    p.add_argument("--image-provider", type=str, default=os.getenv("IMAGE_PROVIDER", "placeholder"))
    p.add_argument("--tts-provider", type=str, default=os.getenv("TTS_PROVIDER", "gtts"))
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    load_dotenv(override=True)
    args = parse_args()

    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)

    ensure_dir(args.outdir)
    project_slug = slugify(f"{args.topic}-{args.niche}-{args.style}")[:60]

    # 1) Story
    story = generate_story(
        topic=args.topic,
        niche=args.niche,
        style=args.style,
        target_scenes=cfg["story"]["target_scenes"],
    )

    # 2) Scenes (initial durations)
    target_total = max(cfg["video"]["min_duration"], min(cfg["video"]["max_duration"], args.duration))
    scenes = build_scenes(
        story_scenes=story.scenes,
        topic=args.topic,
        niche=args.niche,
        style_hint=cfg["images"]["style_hint"],
        total_duration=target_total,
    )

    # 3) Images
    size = cfg["images"]["size"]
    frame_paths = []
    for sc in tqdm(scenes, desc="Generating images"):
        out_path = os.path.join(args.outdir, f"scene_{sc.idx:02d}.png")
        if args.dry_run or args.image_provider == "placeholder":
            frame_paths.append(generate_image("placeholder", sc.prompt, out_path, size=size))
        else:
            frame_paths.append(generate_image(args.image_provider, sc.prompt, out_path, size=size))

    # 4) Per-scene TTS (optional) and duration alignment
    voice_paths = []
    voice_durations = []
    for sc in scenes:
        vo = synthesize(sc.text, provider=args.tts_provider)
        if vo:
            voice_paths.append(vo.path)
            voice_durations.append(max(1.8, vo.duration))
        else:
            voice_paths.append(None)
            voice_durations.append(sc.duration)

    # scale durations to match target_total
    total_voice = sum(voice_durations) if voice_durations else target_total
    scale = target_total / total_voice if total_voice > 0 else 1.0
    for sc, d in zip(scenes, voice_durations):
        sc.duration = max(1.8, d * scale)

    # 5) Video assembly
    scene_specs = [SceneSpec(image_path=fp, text=sc.text, duration=sc.duration) for fp, sc in zip(frame_paths, scenes)]
    out_video = os.path.join(args.outdir, f"{project_slug}.mp4")

    build_video(
        scenes=scene_specs,
        out_path=out_video,
        width=cfg["video"]["width"],
        height=cfg["video"]["height"],
        fps=cfg["video"]["fps"],
        hook_text=story.hook,
        voice_paths=voice_paths,
        music_db=cfg["video"]["music_db"],
        voice_db=cfg["video"]["voice_db"],
        text_color=cfg["video"]["text_color"],
        caption_bg=cfg["video"]["caption_bg"],
        margin=cfg["video"]["margin"],
    )

    # 6) Caption + hashtags
    base_tags = cfg.get("hashtags", {}).get("base", [])
    extra_tags = [f"#{slugify(args.niche)}", f"#{slugify(args.style)}", "#fyp", "#reelsinstagram"]
    hashtags = sorted(set(base_tags + extra_tags))

    with open(os.path.join(args.outdir, "captions.txt"), "w") as f:
        f.write(story.caption.strip() + "\n")
    with open(os.path.join(args.outdir, "hashtags.txt"), "w") as f:
        f.write(" ".join(hashtags) + "\n")

    print("\nDone! Video:", out_video)
    print("Caption:", os.path.join(args.outdir, "captions.txt"))
    print("Hashtags:", os.path.join(args.outdir, "hashtags.txt"))


if __name__ == "__main__":
    main()