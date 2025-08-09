import os
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    concatenate_audioclips,
)

# Pillow >=10 removed Image.ANTIALIAS; alias to LANCZOS for moviepy compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS  # type: ignore

from .utils import (
    ease_in_out,
    lerp,
    choose_ken_burns_params,
    split_text_for_caption,
)


@dataclass
class SceneSpec:
    image_path: str
    text: str
    duration: float


def _write_bg_tone_wav(tmp_path: str, duration: float, sample_rate: int = 44100, freq: float = 220.0, amplitude: float = 0.08) -> None:
    import wave
    import struct
    num_frames = int(sample_rate * duration)
    with wave.open(tmp_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for n in range(num_frames):
            t = n / sample_rate
            sample = int(amplitude * np.sin(2 * np.pi * freq * t) * 32767)
            wf.writeframes(struct.pack('<h', sample))


def _make_bg_tone(duration: float, volume_db: float = -22.0) -> Optional[AudioFileClip]:
    if duration <= 0:
        return None
    tmp_path = os.path.join(os.getcwd(), f"_tone_{abs(hash((duration, volume_db)))}.wav")
    try:
        _write_bg_tone_wav(tmp_path, duration)
        clip = AudioFileClip(tmp_path).volumex(10 ** (volume_db / 20.0))
        return clip
    except Exception:
        return None


def _ken_burns_clip(image_path: str, w: int, h: int, duration: float, rng: random.Random) -> ImageClip:
    img = Image.open(image_path).convert("RGB")
    base = ImageClip(np.array(img))

    (s_s, sx, sy), (s_e, ex, ey) = choose_ken_burns_params(rng)

    def fl(get_frame, t):
        progress = ease_in_out(min(max(t / duration, 0.0), 1.0))
        scale = lerp(s_s, s_e, progress)
        dx = lerp(sx, ex, progress)
        dy = lerp(sy, ey, progress)
        frame = get_frame(t)
        clip = ImageClip(frame).resize(scale)
        fw, fh = clip.size
        cx = int((fw - w) * (dx * 0.5 + 0.5))
        cy = int((fh - h) * (dy * 0.5 + 0.5))
        x1 = max(0, min(fw - w, cx))
        y1 = max(0, min(fh - h, cy))
        return clip.crop(x1=x1, y1=y1, x2=x1 + w, y2=y1 + h).get_frame(0)

    return base.fl(fl, apply_to=["mask"]).set_duration(duration)


def _render_text_image(text: str, w: int, font_size: int, color: Tuple[int, int, int]) -> Image.Image:
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    lines = split_text_for_caption(text, max_chars=20)
    height = len(lines) * int(font_size * 1.2) + 20
    img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = 10
    for ln in lines:
        ln_w = int(draw.textlength(ln, font=font))
        x = (w - ln_w) // 2
        draw.text((x+3, y+3), ln, font=font, fill=(0,0,0,180))
        draw.text((x-3, y+3), ln, font=font, fill=(0,0,0,180))
        draw.text((x+3, y-3), ln, font=font, fill=(0,0,0,180))
        draw.text((x-3, y-3), ln, font=font, fill=(0,0,0,180))
        draw.text((x, y), ln, font=font, fill=color + (255,))
        y += int(font_size * 1.2)
    return img


def _render_caption_image(text: str, w: int, margin: int, text_color: Tuple[int, int, int]) -> Image.Image:
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
    except Exception:
        font = ImageFont.load_default()
    lines = split_text_for_caption(text, max_chars=58)
    height = len(lines) * 64 + 32
    img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = 16
    for ln in lines:
        ln_width = int(draw.textlength(ln, font=font))
        x = (w - ln_width) // 2
        draw.text((x+2, y+2), ln, font=font, fill=(0,0,0,200))
        draw.text((x-2, y+2), ln, font=font, fill=(0,0,0,200))
        draw.text((x+2, y-2), ln, font=font, fill=(0,0,0,200))
        draw.text((x-2, y-2), ln, font=font, fill=(0,0,0,200))
        draw.text((x, y), ln, font=font, fill=text_color + (255,))
        y += 64
    return img


def _caption_clip(text: str, w: int, h: int, margin: int, text_color_hex: str, caption_bg_hex: str) -> CompositeVideoClip:
    def hex_to_rgba(hexstr: str) -> Tuple[int, int, int, int]:
        hexstr = hexstr.lstrip('#')
        if len(hexstr) == 8:
            r = int(hexstr[0:2], 16)
            g = int(hexstr[2:4], 16)
            b = int(hexstr[4:6], 16)
            a = int(hexstr[6:8], 16)
        else:
            r = int(hexstr[0:2], 16)
            g = int(hexstr[2:4], 16)
            b = int(hexstr[4:6], 16)
            a = 200
        return (r, g, b, a)

    text_rgb = tuple(int(text_color_hex.strip('#')[i:i+2], 16) for i in (0, 2, 4))
    cap_img = _render_caption_image(text, w - 2 * margin, margin, text_rgb)

    bar_h = cap_img.height + 32
    bg = Image.new("RGBA", (w, bar_h), hex_to_rgba(caption_bg_hex))
    composed = Image.new("RGBA", (w, bar_h), (0, 0, 0, 0))
    composed.alpha_composite(bg, (0, 0))
    x = (w - cap_img.width) // 2
    y = (bar_h - cap_img.height) // 2
    composed.alpha_composite(cap_img, (x, y))

    cap_clip = ImageClip(np.array(composed)).set_position((0, h - bar_h))
    return CompositeVideoClip([cap_clip])


def build_video(
    scenes: List[SceneSpec],
    out_path: str,
    width: int,
    height: int,
    fps: int,
    hook_text: Optional[str],
    voice_paths: Optional[List[Optional[str]]],
    music_db: float,
    voice_db: float,
    text_color: str,
    caption_bg: str,
    margin: int,
    seed: int = 42,
    crossfade_s: float = 0.35,
    hook_seconds: float = 2.0,
) -> str:
    rng = random.Random(seed)

    vclips = []
    for idx_s, s in enumerate(scenes):
        kb = _ken_burns_clip(s.image_path, width, height, s.duration, rng)
        overlays = [kb]
        # hook overlay only on first scene
        if idx_s == 0 and hook_text:
            text_rgb = tuple(int(text_color.strip('#')[i:i+2], 16) for i in (0, 2, 4))
            hook_img = _render_text_image(hook_text, w=width - 2 * margin, font_size=96, color=text_rgb)
            hook_clip = ImageClip(np.array(hook_img)).set_position(("center", "center"))
            hook_clip = hook_clip.set_duration(min(hook_seconds, s.duration)).crossfadeout(0.4)
            overlays.append(hook_clip)
        cap = _caption_clip(s.text, width, height, margin, text_color, caption_bg).set_duration(s.duration)
        overlays.append(cap)
        vclips.append(CompositeVideoClip(overlays).set_duration(s.duration))

    # apply crossfades
    vclips_cf = []
    for idx, clip in enumerate(vclips):
        if idx == 0:
            vclips_cf.append(clip)
        else:
            vclips_cf.append(clip.crossfadein(crossfade_s))

    video = concatenate_videoclips(vclips_cf, method="compose", padding=-crossfade_s).set_fps(fps)

    # Voice track concatenation
    voice_track = None
    if voice_paths:
        voice_clips = []
        for p in voice_paths:
            if p and os.path.exists(p):
                try:
                    voice_clips.append(AudioFileClip(p).volumex(10 ** (voice_db / 20.0)))
                except Exception:
                    pass
        if voice_clips:
            voice_track = concatenate_audioclips(voice_clips)

    bg = _make_bg_tone(duration=video.duration, volume_db=music_db)

    audio_layers = []
    if voice_track is not None:
        audio_layers.append(voice_track)
    if bg is not None:
        audio_layers.append(bg)

    if audio_layers:
        video = video.set_audio(CompositeAudioClip(audio_layers))

    video.write_videofile(out_path, fps=fps, codec="libx264", audio_codec="aac", threads=4, preset="medium")
    return out_path