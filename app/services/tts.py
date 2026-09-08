from pathlib import Path


AUDIO_DIR = Path("generated/audio")


def generate_audio_placeholder(
    text: str,
    lesson_id: str,
) -> str:
    """
    Temporary interface for the TTS engine.

    The actual Kokoro inference is isolated here so the rest
    of the video pipeline does not depend on the TTS implementation.
    """

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    output_path = AUDIO_DIR / f"{lesson_id}.wav"

    raise NotImplementedError(
        "Kokoro TTS engine is not configured yet."
    )