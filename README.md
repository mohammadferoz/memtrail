## AI Story Reels — Instagram Cartoon Story Video Generator

Generate hooky, Instagram-ready 9:16 animated cartoon story videos with AI. Pipeline includes:

- Story + hook generation
- Scene splitting and prompt creation
- Image generation (OpenAI Images) or placeholder mode
- Voiceover TTS (gTTS or offline pyttsx3 fallback)
- Animated Ken-Burns style scenes, bold captions, background tone
- Outputs MP4 (1080x1920), captions, and hashtags

### Quick start

1) Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure environment

- Copy `.env.example` to `.env` and set `OPENAI_API_KEY` if you want AI images or story via OpenAI.
- Dry-run mode works without any API keys (uses placeholder images and local TTS if available).

```bash
cp .env.example .env
# edit .env to add keys
```

3) Run (dry-run, no external APIs)

```bash
python -m storyreels.main \
  --topic "A mischievous cat who secretly helps neighbors" \
  --niche "heartwarming animals" \
  --duration 35 \
  --style "cute 2D cartoon" \
  --outdir ./outputs/demo \
  --dry-run
```

4) Run (with OpenAI images)

```bash
python -m storyreels.main \
  --topic "A time-traveling chef who saves a village" \
  --niche "food adventures" \
  --duration 35 \
  --style "whimsical cartoon" \
  --outdir ./outputs/chef \
  --image-provider openai \
  --tts-provider gtts
```

### Output

- MP4 video in `outdir`
- `captions.txt` Instagram caption
- `hashtags.txt` suggested hashtags

### Tips for growth and monetization

- Keep total duration 20–45s; the hook must land in first 2 seconds
- Use strong niche signals and recurring characters/styles
- Post consistently; A/B test hooks and first frames
- Engage comments with pinned question, and CTA overlays
- Collaborate with other accounts in your niche; recycle top performers with fresh hooks

### Configuration

Default knobs are in `storyreels/config.yaml`. Override with CLI flags.

### Known limits

- Placeholder mode simulates images; for best results, use OpenAI Images or plug in your provider.
- pyttsx3 availability varies by system. If it fails, use `--tts-provider gtts`.

### License

For your own use; ensure you have the right to post any generated media, voices, music, and likenesses.
