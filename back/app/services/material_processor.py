from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.concept import Concept, ConceptPrerequisite
from app.models.content_chunk import ContentChunk
from app.models.material import Material
from app.models.processing_job import ProcessingJob
from app.services.chunker import chunk_text
from app.services.concept_pipeline import extract_course_concepts
from app.services.embedding_service import generate_missing_embeddings
from app.services.extractor import extract_document
from app.services.graph import topological_sort
from app.services.graph_builder import build_course_graph
from app.services.transcription import transcribe_audio


AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
}


def process_material(material_id: str):
    db = SessionLocal()

    material = None
    job = None

    try:
        material = db.scalar(
            select(Material).where(
                Material.id == material_id
            )
        )

        if material is None:
            raise ValueError("Material not found")

        job = db.scalar(
            select(ProcessingJob)
            .where(
                ProcessingJob.material_id == material.id
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

        material.processing_status = "processing"
        material.error_message = None

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        job.completed_at = None
        job.error_message = None

        db.commit()

        path = Path(material.storage_url)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        extension = path.suffix.lower()

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

        chunks = chunk_text(text)

        if not chunks:
            raise ValueError(
                "No chunks were generated"
            )

        existing_chunks = db.scalars(
            select(ContentChunk).where(
                ContentChunk.material_id == material.id
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
        db.commit()

        print(
            f"Content chunks saved: {saved_chunks}"
        )

        generated_embeddings = (
            generate_missing_embeddings()
        )

        print(
            f"Embeddings generated: {generated_embeddings}"
        )

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

        if not isinstance(concepts_data, list):
            concepts_data = []

        if not isinstance(prerequisites_data, list):
            prerequisites_data = []

        if not concepts_data:
            raise ValueError(
                "No concepts could be extracted from the material."
            )

        ordered_names, safe_edges = topological_sort(
            concepts_data,
            prerequisites_data,
        )

        existing_concepts = db.scalars(
            select(Concept).where(
                Concept.course_id == material.course_id
            )
        ).all()

        concept_by_name = {
            concept.name.lower(): concept
            for concept in existing_concepts
        }

        ordered_name_set = {
            name.lower()
            for name in ordered_names
            if isinstance(name, str)
        }

        remaining_names = []

        for item in concepts_data:
            if not isinstance(item, dict):
                continue

            name = item.get("name")

            if not isinstance(name, str):
                continue

            name = name.strip()

            if not name:
                continue

            if name.lower() not in ordered_name_set:
                remaining_names.append(name)

        final_ordered_names = (
            ordered_names + remaining_names
        )

        for index, name in enumerate(
            final_ordered_names
        ):
            if not isinstance(name, str):
                continue

            name = name.strip()

            if not name:
                continue

            data = next(
                (
                    item
                    for item in concepts_data
                    if isinstance(item, dict)
                    and isinstance(
                        item.get("name"),
                        str,
                    )
                    and item.get("name").strip().lower()
                    == name.lower()
                ),
                None,
            )

            if data is None:
                continue

            key = name.lower()

            concept = concept_by_name.get(key)

            description = data.get(
                "description"
            )

            if not isinstance(description, str):
                description = None
            else:
                description = description.strip() or None

            if concept is None:
                concept = Concept(
                    course_id=material.course_id,
                    name=name,
                    description=description,
                    order_index=index,
                )

                db.add(concept)
                db.flush()

                concept_by_name[key] = concept

            else:
                concept.order_index = index

                if description:
                    concept.description = description

        db.flush()

        for edge in safe_edges:
            if not isinstance(edge, dict):
                continue

            concept_name = edge.get(
                "concept",
                "",
            )

            prerequisite_name = edge.get(
                "prerequisite",
                "",
            )

            if not isinstance(concept_name, str):
                continue

            if not isinstance(prerequisite_name, str):
                continue

            concept_name = concept_name.strip()
            prerequisite_name = prerequisite_name.strip()

            if not concept_name or not prerequisite_name:
                continue

            concept = concept_by_name.get(
                concept_name.lower()
            )

            prerequisite = concept_by_name.get(
                prerequisite_name.lower()
            )

            if concept is None or prerequisite is None:
                continue

            if concept.id == prerequisite.id:
                continue

            existing_relation = db.scalar(
                select(ConceptPrerequisite).where(
                    ConceptPrerequisite.concept_id
                    == concept.id,
                    ConceptPrerequisite.prerequisite_concept_id
                    == prerequisite.id,
                )
            )

            if existing_relation is None:
                db.add(
                    ConceptPrerequisite(
                        concept_id=concept.id,
                        prerequisite_concept_id=prerequisite.id,
                    )
                )

        material.processing_status = "completed"
        material.error_message = None

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None

        graph_result = build_course_graph(
            db=db,
            course_id=material.course_id,
        )

        db.commit()

        print(
            f"Material processing completed: {material.id}"
        )
        print(
            "Knowledge graph updated: "
            f"{graph_result['nodes_created']} nodes, "
            f"{graph_result['edges_created']} edges"
        )

    except Exception as exc:
        db.rollback()

        if material is not None:
            material.processing_status = "failed"
            material.error_message = str(exc)

        if job is not None:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)

        db.commit()

        raise

    finally:
        db.close()
