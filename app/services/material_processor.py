from app.ai.embeddings import embed_text
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.concept import Concept, ConceptPrerequisite
from app.models.content_chunk import ContentChunk
from app.models.material import Material
from app.models.processing_job import ProcessingJob
from app.services.chunker import chunk_text
from app.services.concept_pipeline import extract_course_concepts
from app.services.extractor import extract_document
from app.services.graph import topological_sort
from app.services.transcription import transcribe_audio


AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
}


def process_material(
    material_id: str,
):
    db = SessionLocal()

    material = None
    job = None

    try:
        # -----------------------------------------
        # 1. Get material
        # -----------------------------------------
        material = db.scalar(
            select(Material).where(
                Material.id == material_id
            )
        )

        if material is None:
            raise ValueError(
                "Material not found"
            )

        # -----------------------------------------
        # 2. Get or create processing job
        # -----------------------------------------
        job = db.scalar(
            select(ProcessingJob)
            .where(
                ProcessingJob.material_id
                == material.id
            )
            .order_by(
                ProcessingJob.created_at.desc()
            )
        )

        if job is None:
            job = ProcessingJob(
                material_id=material.id,
                job_type="material_processing",
                status="pending",
            )

            db.add(job)
            db.flush()

        elif job.status != "pending":
            job.status = "pending"
            job.error_message = None

        # -----------------------------------------
        # 3. Mark processing
        # -----------------------------------------
        material.processing_status = "processing"
        material.error_message = None

        job.status = "processing"
        job.started_at = datetime.now(
            timezone.utc
        )
        job.completed_at = None
        job.error_message = None

        db.commit()

        # -----------------------------------------
        # 4. Check file
        # -----------------------------------------
        path = Path(
            material.storage_url
        )

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        extension = path.suffix.lower()

        # -----------------------------------------
        # 5. Extract text
        # -----------------------------------------
        if extension in AUDIO_EXTENSIONS:
            text = transcribe_audio(
                str(path)
            )
        else:
            text = extract_document(
                str(path)
            )

        if not isinstance(text, str):
            text = ""

        text = text.strip()

        if not text:
            raise ValueError(
                "No text could be extracted from material"
            )

        # -----------------------------------------
        # 6. Chunk text
        # -----------------------------------------
        chunks = chunk_text(text)

        if not chunks:
            raise ValueError(
                "No chunks were generated"
            )

        # -----------------------------------------
        # 7. Save content chunks
        # -----------------------------------------
        existing_chunks = db.scalars(
            select(ContentChunk).where(
                ContentChunk.material_id
                == material.id
            )
        ).all()

        existing_chunk_texts = {
            chunk.chunk_text
            for chunk in existing_chunks
            if chunk.chunk_text
        }

        saved_chunks = 0

        for chunk in chunks:
            if not isinstance(chunk, str):
                continue

            chunk = chunk.strip()

            if not chunk:
                continue

            if chunk in existing_chunk_texts:
                continue

            db.add(
                ContentChunk(
                    material_id=material.id,
                    chunk_text=chunk,
                )
            )

            existing_chunk_texts.add(chunk)
            saved_chunks += 1

        db.flush()

        # IMPORTANT:
        # Commit chunks separately so they are not
        # removed if Ollama fails later.
        db.commit()

        print(
            f"Content chunks saved: {saved_chunks}"
        )

        # -----------------------------------------
        # 8. Extract concepts
        # -----------------------------------------
        result = extract_course_concepts(
            chunks
        )

        if not isinstance(result, dict):
            result = {
                "concepts": [],
                "prerequisites": [],
            }

        concepts_data = result.get(
            "concepts",
            [],
        )

        prerequisites_data = result.get(
            "prerequisites",
            [],
        )

        if not isinstance(
            concepts_data,
            list,
        ):
            concepts_data = []

        if not isinstance(
            prerequisites_data,
            list,
        ):
            prerequisites_data = []

        # -----------------------------------------
        # 9. Build concept graph
        # -----------------------------------------
        ordered_names, safe_edges = (
            topological_sort(
                concepts_data,
                prerequisites_data,
            )
        )

        # -----------------------------------------
        # 10. Get existing concepts
        # -----------------------------------------
        existing_concepts = db.scalars(
            select(Concept).where(
                Concept.course_id
                == material.course_id
            )
        ).all()

        concept_by_name = {
            concept.name.lower(): concept
            for concept in existing_concepts
        }

        # -----------------------------------------
        # 11. Create / update concepts
        # -----------------------------------------
        for index, name in enumerate(
            ordered_names
        ):
            data = next(
                (
                    item
                    for item in concepts_data
                    if isinstance(item, dict)
                    and item.get("name") == name
                ),
                None,
            )

            if data is None:
                continue

            key = name.lower()

            concept = concept_by_name.get(
                key
            )

            if concept is None:
                concept = Concept(
                    course_id=material.course_id,
                    name=data["name"],
                    description=data.get(
                        "description"
                    ),
                    order_index=index,
                )

                db.add(concept)
                db.flush()

                concept_by_name[key] = concept

            else:
                concept.order_index = index

                description = data.get(
                    "description"
                )

                if isinstance(
                    description,
                    str,
                ) and description.strip():
                    concept.description = (
                        description.strip()
                    )

        db.flush()

        # -----------------------------------------
        # 12. Create prerequisites
        # -----------------------------------------
        for edge in safe_edges:
            concept_name = edge.get(
                "concept",
                "",
            )

            prerequisite_name = edge.get(
                "prerequisite",
                "",
            )

            if not isinstance(
                concept_name,
                str,
            ):
                continue

            if not isinstance(
                prerequisite_name,
                str,
            ):
                continue

            concept = concept_by_name.get(
                concept_name.lower()
            )

            prerequisite = concept_by_name.get(
                prerequisite_name.lower()
            )

            if (
                not concept
                or not prerequisite
            ):
                continue

            if concept.id == prerequisite.id:
                continue

            existing_relation = db.scalar(
                select(ConceptPrerequisite)
                .where(
                    ConceptPrerequisite.concept_id
                    == concept.id
                )
                .where(
                    ConceptPrerequisite.prerequisite_concept_id
                    == prerequisite.id
                )
            )

            if existing_relation is None:
                db.add(
                    ConceptPrerequisite(
                        concept_id=concept.id,
                        prerequisite_concept_id=(
                            prerequisite.id
                        ),
                    )
                )

        # -----------------------------------------
        # 13. Mark completed
        # -----------------------------------------
        material.processing_status = (
            "completed"
        )

        material.error_message = None

        job.status = "completed"
        job.completed_at = datetime.now(
            timezone.utc
        )
        job.error_message = None

        db.commit()

    except Exception as exc:
        # -----------------------------------------
        # 14. Handle failure
        # -----------------------------------------
        db.rollback()

        if material is not None:
            material.processing_status = (
                "failed"
            )
            material.error_message = str(
                exc
            )

        if job is not None:
            job.status = "failed"
            job.error_message = str(
                exc
            )
            job.completed_at = datetime.now(
                timezone.utc
            )

        db.commit()

        raise

    finally:
        # -----------------------------------------
        # 15. Close DB
        # -----------------------------------------
        db.close()