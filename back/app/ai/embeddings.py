import hashlib
from functools import lru_cache

from app.ai.ai_gateway.ai_gateway import (
    AIGatewayUnavailable,
    create_openai_client,
)
from app.core.config import get_settings

E5_PROVIDER = "sentence-transformers"
OPENAI_COMPATIBLE_PROVIDER = "openai-compatible"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Local embeddings require requirements-local-embeddings.txt"
        ) from exc

    return SentenceTransformer(get_settings().local_embedding_model)


def get_embedding_metadata() -> tuple[str, int]:
    settings = get_settings()

    if settings.mock_ai and not settings.embedding_model.strip():
        return "mock", EMBEDDING_DIMENSION

    if settings.embedding_provider == OPENAI_COMPATIBLE_PROVIDER:
        model = _required(settings.embedding_model, "EMBEDDING_MODEL")
        return model, EMBEDDING_DIMENSION

    if settings.embedding_provider == E5_PROVIDER:
        return settings.local_embedding_model, EMBEDDING_DIMENSION

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )


def _mock_embedding(text: str) -> list[float]:
    values = []
    seed = text.encode("utf-8")

    for index in range(EMBEDDING_DIMENSION):
        digest = hashlib.sha256(seed + index.to_bytes(4, "big")).digest()
        values.append((int.from_bytes(digest[:4], "big") / 2**31) - 1)

    magnitude = sum(value * value for value in values) ** 0.5
    return [value / magnitude for value in values]


def _required(value: str, env_var: str) -> str:
    value = value.strip()

    if not value:
        raise AIGatewayUnavailable(f"{env_var} is not configured.")

    return value


def _remote_embeddings(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = create_openai_client(
        _required(settings.embedding_base_url, "EMBEDDING_BASE_URL"),
        _required(settings.embedding_api_key, "EMBEDDING_API_KEY"),
    )
    response = client.embeddings.create(
        model=_required(settings.embedding_model, "EMBEDDING_MODEL"),
        input=texts,
        dimensions=EMBEDDING_DIMENSION,
    )

    embeddings = [
        item.embedding
        for item in sorted(response.data, key=lambda item: item.index)
    ]

    if len(embeddings) != len(texts):
        raise RuntimeError(
            "The embedding endpoint returned an unexpected number of vectors"
        )

    if any(len(embedding) != EMBEDDING_DIMENSION for embedding in embeddings):
        raise RuntimeError(
            "The embedding endpoint returned vectors that do not match "
            f"the required {EMBEDDING_DIMENSION} dimensions"
        )

    return embeddings


def _embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    settings = get_settings()

    if settings.mock_ai:
        return [_mock_embedding(text) for text in texts]

    if settings.embedding_provider == OPENAI_COMPATIBLE_PROVIDER:
        return _remote_embeddings(texts)

    if settings.embedding_provider == E5_PROVIDER:
        model = get_embedding_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=16,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    raise ValueError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )


def embed_text(text: str) -> list[float]:
    return _embed([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _embed(texts)
