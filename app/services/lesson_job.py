import json

import soundfile as sf
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.concept import Concept
from app.models.lesson import Lesson
from app.services.lesson_pipeline import generate_lesson


def generate_lesson_job(lesson_id: str) -> None:
    db = SessionLocal()

    try:
        lesson = db.scalar(
            select(Lesson).where(
                Lesson.id == lesson_id
            )
        )

        if lesson is None:
            raise ValueError(
                f"Lesson not found: {lesson_id}"
            )

        concept = db.scalar(
            select(Concept).where(
                Concept.id == lesson.concept_id
            )
        )

        if concept is None:
            raise ValueError(
                f"Concept not found: {lesson.concept_id}"
            )

        lesson.status = "processing"
        db.commit()

        result = generate_lesson(
            lesson_id=str(lesson.id),
            concept_name=concept.name,
            concept_description=concept.description or "",
        )

        audio_path = result["audio"]
        audio_info = sf.info(audio_path)

        lesson.script_text = json.dumps(
            result["script"],
            ensure_ascii=False,
        )
        lesson.audio_url = result["audio"]
        lesson.video_url = result["video"]
        lesson.duration_seconds = audio_info.duration
        lesson.status = "completed"

        db.commit()

    except Exception:
        db.rollback()

        lesson = db.scalar(
            select(Lesson).where(
                Lesson.id == lesson_id
            )
        )

        if lesson is not None:
            lesson.status = "failed"
            db.commit()

        raise

    finally:
        db.close()