import hashlib
import logging
import threading
from functools import lru_cache

from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

from app.ai.ai_gateway.ai_gateway import GEMINI_PROVIDER, key_pool
from app.core.config import get_settings

logger = logging.getLogger("makhmakh.embeddings")

E5_PROVIDER = "sentence-transformers"
GEMINI_PROVIDER_NAME = "gemini"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 384

_provider_lock = threading.Lock()
_active_provider: str | None = None
_fallback_activated = False


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(get_settings().active_embedding_model)


def get_embedding_metadata() -> tuple[str, int]:
    if _active_provider == GEMINI_PROVIDER_NAME:
        return GEMINI_EMBEDDING_MODEL, EMBEDDING_DIMENSION

    return get_settings().active_embedding_model, EMBEDDING_DIMENSION


def fallback_was_activated() -> bool:
    return _fallback_activated


def _set_gemini_fallback() -> None:
    global _active_provider, _fallback_activated

    with _provider_lock:
        if _active_provider != GEMINI_PROVIDER_NAME:
            logger.warning(
                "SentenceTransformer embedding failed; switching to Gemini embeddings."
            )
        _active_provider = GEMINI_PROVIDER_NAME
        _fallback_activated = True


def _mock_embedding(text: str) -> list[float]:
    values = []
    seed = text.encode("utf-8")

    for index in range(EMBEDDING_DIMENSION):
        digest = hashlib.sha256(seed + index.to_bytes(4, "big")).digest()
        values.append((int.from_bytes(digest[:4], "big") / 2**31) - 1)

    magnitude = sum(value * value for value in values) ** 0.5
    return [value / magnitude for value in values]


def _gemini_embeddings(texts: list[str], task_type: str) -> list[list[float]]:
    settings = get_settings()
    last_error: Exception | None = None

    for _ in range(settings.ai_gateway_max_retries):
        api_key = key_pool.reserve_key(target_provider=GEMINI_PROVIDER)

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIMENSION,
                ),
            )

            embeddings = [item.values for item in response.embeddings or []]

            if len(embeddings) != len(texts):
                raise RuntimeError("Gemini returned an unexpected number of embeddings")

            if any(len(embedding) != EMBEDDING_DIMENSION for embedding in embeddings):
                raise RuntimeError("Gemini embedding dimension does not match pgvector")

            return embeddings
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()

            if "401" in message or "403" in message or "api key" in message:
                key_pool.disable_key(api_key)
            elif "429" in message or "quota" in message or "rate limit" in message:
                key_pool.set_cooldown(api_key)
            else:
                raise

    raise RuntimeError("Every configured Gemini embedding key failed") from last_error


def _embed_with_fallback(texts: list[str], task_type: str) -> list[list[float]]:
    global _active_provider

    if get_settings().mock_ai:
        return [_mock_embedding(text) for text in texts]

    if _active_provider == GEMINI_PROVIDER_NAME:
        return _gemini_embeddings(texts, task_type)

    try:
        model = get_embedding_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=16,
            show_progress_bar=False,
        )
        _active_provider = E5_PROVIDER
        return embeddings.tolist()
    except Exception:
        _set_gemini_fallback()
        return _gemini_embeddings(texts, task_type)


def embed_text(text: str) -> list[float]:
    return _embed_with_fallback([text], "RETRIEVAL_QUERY")[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _embed_with_fallback(texts, "RETRIEVAL_DOCUMENT")
