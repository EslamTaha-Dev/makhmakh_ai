from pathlib import Path

import soundfile as sf
from kokoro import KPipeline


AUDIO_DIR = Path("generated/audio")

_pipeline = None


def get_pipeline():
    global _pipeline

    if _pipeline is None:
        _pipeline = KPipeline(lang_code="a")

    return _pipeline


def generate_audio_placeholder(
    text: str,
    lesson_id: str,
) -> str:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    output_path = AUDIO_DIR / f"{lesson_id}.wav"

    if output_path.exists() and output_path.stat().st_size > 0:
        return str(output_path)

    pipeline = get_pipeline()

    generator = pipeline(
        text,
        voice="af_heart",
        speed=1.0,
    )

    audio_parts = []

    for _, _, audio in generator:
        audio_parts.append(audio)

    if not audio_parts:
        raise RuntimeError("Kokoro did not generate any audio.")

    import numpy as np

    final_audio = np.concatenate(audio_parts)

    sf.write(
        output_path,
        final_audio,
        24000,
    )

    return str(output_path)