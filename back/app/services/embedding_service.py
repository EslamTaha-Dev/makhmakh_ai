from sqlalchemy import select

from app.ai.embeddings import embed_texts
from app.db.session import SessionLocal
from app.models.content_chunk import ContentChunk


def generate_missing_embeddings() -> int:
    db = SessionLocal()

    try:
        chunks = db.scalars(
            select(ContentChunk)
            .where(ContentChunk.embedding.is_(None))
        ).all()

        if not chunks:
            return 0

        texts = [chunk.chunk_text for chunk in chunks]

        embeddings = embed_texts(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        db.commit()

        return len(chunks)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()