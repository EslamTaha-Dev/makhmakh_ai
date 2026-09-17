import json

import soundfile as sf
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.concept import Concept
from app.models.lesson import Lesson
from app.models.processing_job import ProcessingJob
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

        from app.services.lesson_pipeline import compute_content_hash

        content_hash = compute_content_hash(
            concept.name,
            concept.description or "",
        )
        job = db.scalar(
            select(ProcessingJob).where(
                ProcessingJob.lesson_id == lesson.id,
                ProcessingJob.content_hash == content_hash,
            )
        )
        if job is not None and job.status == "completed":
            lesson.status = "completed"
            lesson.video_url = job.output_video_url
            db.commit()
            return
        if job is None:
            job = ProcessingJob(
                lesson_id=lesson.id,
                job_type="video_generation",
                status="pending",
                content_hash=content_hash,
            )
            db.add(job)
        job.attempt_count += 1
        job.status = "processing"
        job.progress_percent = 5
        db.flush()

        lesson.status = "processing"
        db.commit()

        result = generate_lesson(
            lesson_id=str(lesson.id),
            concept_name=concept.name,
            concept_description=concept.description or "",
        )

        job.status = "processing"
        job.progress_percent = 80
        db.flush()

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
        job.status = "completed"
        job.progress_percent = 100
        job.output_video_url = result["video"]
        job.output_thumbnail_url = result["thumbnail"]

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

        if "job" in locals() and job is not None:
            job.status = "failed"
            job.error_message = "Video generation failed"
            db.commit()

        raise

    finally:
        db.close()