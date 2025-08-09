import os
from io import BytesIO
from typing import Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import random
import hashlib

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

load_dotenv(override=True)


@dataclass
class GeneratedImage:
    path: str


def _placeholder_palette(seed: str):
    h = hashlib.md5(seed.encode()).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    base = (r, g, b)
    comp = (255 - r // 2, 255 - g // 2, 255 - b // 2)
    accent = ((r + 128) % 255, (g + 64) % 255, (b + 192) % 255)
    return base, comp, accent


def _placeholder_image(text: str, out_path: str, size=(1024, 1024)) -> str:
    base, comp, accent = _placeholder_palette(text[:80])
    img = Image.new("RGB", size, base)
    draw = ImageDraw.Draw(img)

    # radial vignette
    cx, cy = size[0] // 2, size[1] // 2
    for r in range(min(size)//2, 0, -40):
        alpha = int(80 * (r / (min(size)//2)))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(0, 0, 0), width=2)

    # simple "character" shape
    face_r = size[0] // 6
    face_x = cx
    face_y = cy - face_r // 2
    draw.ellipse((face_x - face_r, face_y - face_r, face_x + face_r, face_y + face_r), fill=comp)
    eye_r = face_r // 6
    draw.ellipse((face_x - face_r//2 - eye_r, face_y - eye_r, face_x - face_r//2 + eye_r, face_y + eye_r), fill=(0, 0, 0))
    draw.ellipse((face_x + face_r//2 - eye_r, face_y - eye_r, face_x + face_r//2 + eye_r, face_y + eye_r), fill=(0, 0, 0))
    draw.arc((face_x - face_r//2, face_y, face_x + face_r//2, face_y + face_r//2), start=10, end=170, fill=accent, width=4)

    # foreground accents
    for i in range(5):
        w = random.randint(size[0]//10, size[0]//5)
        h = random.randint(size[1]//12, size[1]//6)
        x = random.randint(40, size[0]-w-40)
        y = random.randint(size[1]//2, size[1]-h-40)
        draw.rounded_rectangle((x, y, x+w, y+h), radius=12, outline=accent, width=4)

    # subtle label
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    label = (text[:48] + "…") if len(text) > 48 else text
    tw = int(draw.textlength(label, font=font))
    draw.text(((size[0]-tw)//2, size[1]-60), label, fill=(255, 255, 255), font=font)

    img.save(out_path, format="PNG")
    return out_path


def generate_openai_image(prompt: str, out_path: str, size: str = "1024x1024") -> str:
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK not installed")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    result = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
    b64 = result.data[0].b64_json
    import base64

    raw = base64.b64decode(b64)
    img = Image.open(BytesIO(raw)).convert("RGB")
    img.save(out_path, format="PNG")
    return out_path


def generate_image(provider: str, prompt: str, out_path: str, size: str = "1024x1024") -> str:
    provider = (provider or "placeholder").lower()
    if provider == "openai":
        try:
            return generate_openai_image(prompt, out_path, size=size)
        except Exception:
            return _placeholder_image(prompt, out_path)
    return _placeholder_image(prompt, out_path)