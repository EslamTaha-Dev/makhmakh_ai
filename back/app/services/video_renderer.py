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
    thumbnail_path = VIDEO_DIR / f"{lesson_id}.jpg"
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

    if output_path.exists() and output_path.stat().st_size > 0:
        return str(output_path)

    raw_output_path = VIDEO_DIR / f"{lesson_id}_raw.mp4"
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
        str(raw_output_path),
    ]

    subprocess.run(command, check=True)

    postprocess_command = [
        "ffmpeg",
        "-y",
        "-i",
        str(raw_output_path),
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "medium",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    subprocess.run(postprocess_command, check=True)

    thumbnail_command = [
        "ffmpeg",
        "-y",
        "-ss",
        "3",
        "-i",
        str(output_path),
        "-vframes",
        "1",
        "-q:v",
        "2",
        str(thumbnail_path),
    ]
    subprocess.run(thumbnail_command, check=True)
    raw_output_path.unlink(missing_ok=True)

    return str(output_path)