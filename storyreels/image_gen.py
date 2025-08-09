import os
from io import BytesIO
from typing import Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

load_dotenv(override=True)


@dataclass
class GeneratedImage:
    path: str


def _placeholder_image(text: str, out_path: str, size=(1024, 1024)) -> str:
    img = Image.new("RGB", size, (30, 30, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
    wrapped = []
    words = text.split()
    line = []
    for w in words:
        test = " ".join(line + [w])
        if draw.textlength(test, font=font) > size[0] - 80:
            if line:
                wrapped.append(" ".join(line))
                line = []
        line.append(w)
    if line:
        wrapped.append(" ".join(line))
    y = size[1] // 2 - 12 * len(wrapped)
    for i, ln in enumerate(wrapped[:8]):
        draw.text((40, y + i * 32), ln, fill=(230, 230, 230), font=font)
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