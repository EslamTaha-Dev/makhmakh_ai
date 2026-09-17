import hashlib
import json

from app.ai.ai_gateway.ai_gateway import ai_gateway_execute
from app.ai.script_generator import generate_lesson_script
from app.schemas.slide_plan import normalize_legacy_script
from app.services.slide_generator import create_slides
from app.services.tts import generate_audio_placeholder
from app.services.video_renderer import render_video


def compute_content_hash(
    concept_name: str,
    concept_description: str,
) -> str:
    payload = json.dumps(
        {
            "concept_name": concept_name,
            "concept_description": concept_description,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_lesson(
    lesson_id: str,
    concept_name: str,
    concept_description: str,
):
    try:
        script = generate_lesson_script(
            concept_name=concept_name,
            concept_description=concept_description,
        )
    except Exception:
        prompt = f"""
Write an educational lesson script for:
Concept: {concept_name}
Description: {concept_description}

Provide a structured lesson plan with slide titles and narrations.
        """.strip()

        raw_script = ai_gateway_execute(
            task_type="video_script",
            prompt=prompt,
        )
        script = {"raw_text": raw_script}

    teaching_script = normalize_legacy_script(script, lesson_id)

    slides = create_slides(
        script=script,
        lesson_id=lesson_id,
    )

    text_for_audio = " ".join(
        [
            teaching_script.slides[0].narration,
            *[
                slide.narration
                for slide in teaching_script.slides[1:-1]
            ],
            teaching_script.slides[-1].narration,
        ]
    )

    audio = generate_audio_placeholder(
        text=text_for_audio,
        lesson_id=lesson_id,
    )

    video = render_video(
        slide_paths=slides,
        audio_path=audio,
        lesson_id=lesson_id,
    )

    return {
        "script": teaching_script.model_dump(mode="json"),
        "slides": slides,
        "audio": audio,
        "video": video,
        "thumbnail": video.rsplit(".", 1)[0] + ".jpg",
        "content_hash": compute_content_hash(
            concept_name,
            concept_description,
        ),
    }