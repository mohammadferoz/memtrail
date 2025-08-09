import os
import json
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

load_dotenv(override=True)


@dataclass
class Story:
    hook: str
    scenes: List[str]
    caption: str


SYSTEM_PROMPT = (
    "You are a social video story writer who crafts short, high-retention Instagram Reels stories. "
    "You always deliver: (1) a punchy 1-sentence hook under 90 chars, (2) 6-10 micro-scenes (1-2 sentences each), "
    "(3) a one-paragraph caption with a question CTA. Keep language simple, emotional, and visual."
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _openai_generate(topic: str, niche: str, style: str, target_scenes: int) -> Story:
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK not installed")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    user_prompt = (
        f"Niche: {niche}\n"
        f"Topic: {topic}\n"
        f"Visual Style: {style}\n"
        f"Target Scenes: {target_scenes}\n\n"
        "Return JSON with keys: hook (string), scenes (array of strings), caption (string)."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    data = json.loads(content)
    return Story(
        hook=data.get("hook", "Wait for it..."),
        scenes=[s for s in data.get("scenes", []) if isinstance(s, str)],
        caption=data.get("caption", "What would you do?"),
    )


def _fallback_generate(topic: str, niche: str, style: str, target_scenes: int) -> Story:
    hook = "This will blow your mind in 5 seconds!"
    base = (
        f"In the world of {niche}, a story unfolds: {topic}. "
        f"Told in a {style} vibe."
    )
    scenes: List[str] = []
    for i in range(target_scenes):
        scenes.append(
            f"Scene {i+1}: {topic} takes an unexpected turn—there's a tiny problem that grows, "
            f"and someone makes a brave choice."
        )
    caption = (
        f"{base}\n\nIf you were there, what would you do? Comment one emoji that fits!"
    )
    return Story(hook=hook, scenes=scenes, caption=caption)


def generate_story(topic: str, niche: str, style: str, target_scenes: int) -> Story:
    try:
        return _openai_generate(topic, niche, style, target_scenes)
    except Exception:
        return _fallback_generate(topic, niche, style, target_scenes)