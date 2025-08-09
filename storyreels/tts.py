import os
import tempfile
from typing import Literal, Optional
from dataclasses import dataclass

from moviepy.audio.io.AudioFileClip import AudioFileClip


@dataclass
class Voiceover:
    path: str
    duration: float


def synthesize(text: str, provider: Literal["gtts", "pyttsx3"] = "gtts") -> Optional[Voiceover]:
    provider = (provider or "gtts").lower()  # type: ignore

    if provider == "gtts":
        try:
            from gtts import gTTS  # type: ignore
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts = gTTS(text=text, lang="en")
            tts.save(tmp.name)
            clip = AudioFileClip(tmp.name)
            return Voiceover(path=tmp.name, duration=clip.duration)
        except Exception:
            # fallback
            return synthesize(text, provider="pyttsx3")

    # pyttsx3 fallback (offline, platform-dependent)
    try:
        import pyttsx3  # type: ignore
        import wave
        import contextlib

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        engine = pyttsx3.init()
        engine.setProperty('rate', 175)
        engine.save_to_file(text, tmp.name)
        engine.runAndWait()
        with contextlib.closing(wave.open(tmp.name, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        return Voiceover(path=tmp.name, duration=duration)
    except Exception:
        return None