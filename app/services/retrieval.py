from sqlalchemy import select

from app.ai.embeddings import embed_text
from app.db.session import SessionLocal
from app.models.content_chunk import ContentChunk
from app.models.material import Material


def search_similar_chunks(
    course_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    db = SessionLocal()

    try:
        query_embedding = embed_text(query)

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
            )
            .order_by(distance)
            .limit(top_k)
        ).all()

        return [
            {
                "chunk_id": str(chunk.id),
                "material_id": str(material.id),
                "file_name": material.file_name,
                "distance": float(chunk_distance),
                "text": chunk.chunk_text,
            }
            for chunk, material, chunk_distance in results
        ]

    finally:
        db.close()