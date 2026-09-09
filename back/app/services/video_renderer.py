import subprocess
from pathlib import Path

import soundfile as sf

VIDEO_DIR = Path("generated/videos")


def render_video(
    slide_paths: list[str],
    audio_path: str,
    lesson_id: str,
) -> str:
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    output_path = VIDEO_DIR / f"{lesson_id}.mp4"
    concat_file = VIDEO_DIR / f"{lesson_id}_slides.txt"

    audio_info = sf.info(audio_path)
    audio_duration = audio_info.duration

    slide_duration = audio_duration / len(slide_paths)

    with open(concat_file, "w", encoding="utf-8") as file:
        for slide in slide_paths:
            file.write(f"file '{Path(slide).resolve()}'\n")
            file.write(f"duration {slide_duration}\n")

        if slide_paths:
            file.write(
                f"file '{Path(slide_paths[-1]).resolve()}'\n"
            )

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-i",
        str(audio_path),
        "-vf",
        "format=yuv420p",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]

    subprocess.run(command, check=True)

    return str(output_path)