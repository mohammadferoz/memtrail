from dataclasses import dataclass
from typing import List


@dataclass
class Scene:
    idx: int
    text: str
    prompt: str
    duration: float


def build_scenes(story_scenes: List[str], topic: str, niche: str, style_hint: str, total_duration: float) -> List[Scene]:
    if not story_scenes:
        return []
    base_duration = max(2.5, total_duration / len(story_scenes))
    scenes: List[Scene] = []
    for i, text in enumerate(story_scenes):
        prompt = (
            f"{style_hint}. Instagram reel frame, vertical, character-centric, "
            f"scene {i+1}. Niche: {niche}. Topic: {topic}."
        )
        scenes.append(Scene(idx=i, text=text, prompt=prompt, duration=base_duration))
    return scenes