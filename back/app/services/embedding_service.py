from sqlalchemy import or_, select

from app.ai.embeddings import (
    embed_texts,
    get_embedding_metadata,
)
from app.db.session import SessionLocal
from app.models.content_chunk import ContentChunk


def generate_missing_embeddings() -> int:
    db = SessionLocal()

    try:
        embedding_model, embedding_dimension = get_embedding_metadata()

        chunks = db.scalars(
            select(ContentChunk).where(
                or_(
                    ContentChunk.embedding.is_(None),
                    ContentChunk.embedding_model != embedding_model,
                    ContentChunk.embedding_dimension != embedding_dimension,
                )
            )
        ).all()

        if not chunks:
            return 0

        texts = [chunk.chunk_text for chunk in chunks]

        embeddings = embed_texts(texts)

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            chunk.embedding = embedding
            chunk.embedding_model = embedding_model
            chunk.embedding_dimension = embedding_dimension

        db.commit()

        return len(chunks)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
