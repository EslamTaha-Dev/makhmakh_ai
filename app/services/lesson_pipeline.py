from app.ai.script_generator import generate_lesson_script
from app.services.slide_generator import create_slides
from app.services.tts import generate_audio_placeholder
from app.services.video_renderer import render_video


def generate_lesson(
    lesson_id: str,
    concept_name: str,
    concept_description: str,
):
    script = generate_lesson_script(
        concept_name=concept_name,
        concept_description=concept_description,
    )

    slides = create_slides(
        script=script,
        lesson_id=lesson_id,
    )

    text_for_audio = " ".join(
        [
            script["introduction"],
            *[
                section["explanation"]
                for section in script["sections"]
            ],
            script["summary"],
        ]
    )

    audio = generate_audio_placeholder(
        text=text_for_audio,
        lesson_id=lesson_id,
    )

    # 4. Render video
    video = render_video(
        slide_paths=slides,
        audio_path=audio,
        lesson_id=lesson_id,
    )

    return {
        "script": script,
        "slides": slides,
        "audio": audio,
        "video": video,
    }