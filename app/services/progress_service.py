from sqlalchemy import select

from app.models.concept import Concept, ConceptPrerequisite
from app.models.progress import StudentProgress


def refresh_user_progress(db, user_id, course_id):
    concepts = db.scalars(
        select(Concept)
        .where(Concept.course_id == course_id)
    ).all()

    for concept in concepts:
        progress = db.scalar(
            select(StudentProgress).where(
                StudentProgress.user_id == user_id,
                StudentProgress.concept_id == concept.id,
            )
        )

        if progress is None:
            progress = StudentProgress(
                user_id=user_id,
                concept_id=concept.id,
                status="locked",
            )
            db.add(progress)

        prerequisites = db.scalars(
            select(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id == concept.id
            )
        ).all()

        if not prerequisites:
            if progress.status == "locked":
                progress.status = "available"

            continue

        prerequisite_ids = [
            item.prerequisite_concept_id
            for item in prerequisites
        ]

        completed_count = db.scalar(
            select(StudentProgress)
            .where(
                StudentProgress.user_id == user_id,
                StudentProgress.concept_id.in_(prerequisite_ids),
                StudentProgress.status == "completed",
            )
        )

        if completed_count:
            if progress.status == "locked":
                progress.status = "available"

    db.commit()