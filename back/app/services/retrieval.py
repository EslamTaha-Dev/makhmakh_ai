from sqlalchemy import select

from app.ai.embeddings import embed_text
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.content_chunk import ContentChunk
from app.models.material import Material
from app.models.concept import Concept


def search_similar_chunks(
    course_id: str,
    query: str,
    node_id: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    db = SessionLocal()

    try:
        query = query.strip()

        if not query:
            return []

        query_embedding = embed_text(query)
        settings = get_settings()

        distance = ContentChunk.embedding.cosine_distance(
            query_embedding
        ).label("distance")

        results = db.execute(
            select(
                ContentChunk,
                Material,
                distance,
            )
            .join(
                Material,
                ContentChunk.material_id == Material.id,
            )
            .where(
                Material.course_id == course_id,
                ContentChunk.embedding.is_not(None),
                ContentChunk.embedding_model == settings.active_embedding_model,
                ContentChunk.embedding_dimension == settings.active_embedding_dimension,
            )
            .where(
                ContentChunk.node_id == node_id
                if node_id is not None
                else True
            )
            .order_by(distance)
            .limit(top_k)
        ).all()

        concepts = db.scalars(
            select(Concept)
            .where(
                Concept.course_id == course_id
            )
            .order_by(Concept.order_index)
        ).all()

        query_lower = query.lower()

        matched_concepts = []

        for concept in concepts:
            name = (concept.name or "").strip()

            if not name:
                continue

            if name.lower() in query_lower:
                matched_concepts.append(concept)

        output = []

        for chunk, material, chunk_distance in results:
            chunk_text = chunk.chunk_text or ""
            chunk_lower = chunk_text.lower()

            related_concepts = []

            for concept in concepts:
                name = (concept.name or "").strip()

                if not name:
                    continue

                if name.lower() in chunk_lower:
                    related_concepts.append(
                        {
                            "id": str(concept.id),
                            "name": concept.name,
                            "description": concept.description or "",
                        }
                    )

            output.append(
                {
                    "chunk_id": str(chunk.id),
                    "material_id": str(material.id),
                    "file_name": material.file_name,
                    "distance": float(chunk_distance),
                    "text": chunk_text,
                    "related_concepts": related_concepts,
                }
            )

        if matched_concepts:
            matched_ids = {
                str(concept.id)
                for concept in matched_concepts
            }

            for item in output:
                for concept in item["related_concepts"]:
                    if concept["id"] in matched_ids:
                        item["graph_relevant"] = True
                        break

        return output

    finally:
        db.close()