import os
import re
import math
import random
from dataclasses import dataclass
from typing import List, Tuple


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def seconds_from_words(words: int, words_per_minute: int = 170) -> float:
    minutes = words / max(100, words_per_minute)
    return max(1.5, minutes * 60.0)


def ease_in_out(t: float) -> float:
    return 3 * t * t - 2 * t * t * t


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def choose_ken_burns_params(rng: random.Random) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    start_scale = rng.uniform(1.05, 1.18)
    end_scale = rng.uniform(1.0, 1.12)
    start_dx = rng.uniform(-0.06, 0.06)
    start_dy = rng.uniform(-0.06, 0.06)
    end_dx = rng.uniform(-0.06, 0.06)
    end_dy = rng.uniform(-0.06, 0.06)
    return (start_scale, start_dx, start_dy), (end_scale, end_dx, end_dy)


def split_text_for_caption(text: str, max_chars: int = 60) -> List[str]:
    words = text.split()
    lines: List[str] = []
    line: List[str] = []
    for w in words:
        if sum(len(x) for x in line) + len(line) + len(w) > max_chars:
            if line:
                lines.append(" ".join(line))
                line = []
        line.append(w)
    if line:
        lines.append(" ".join(line))
    return lines