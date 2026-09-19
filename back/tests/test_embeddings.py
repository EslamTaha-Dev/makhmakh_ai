from types import SimpleNamespace

import pytest

from app.ai import embeddings


def settings(**overrides):
    values = {
        "embedding_provider": "openai-compatible",
        "embedding_base_url": "https://embeddings.example/v1",
        "embedding_api_key": "embedding-token",
        "embedding_model": "provider/embedding-model",
        "local_embedding_model": "intfloat/multilingual-e5-small",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def embedding_item(index, dimension=embeddings.EMBEDDING_DIMENSION):
    return SimpleNamespace(index=index, embedding=[float(index)] * dimension)


def test_remote_embeddings_use_independent_endpoint(monkeypatch):
    monkeypatch.setattr(embeddings, "get_settings", settings)
    captured = {}

    def create(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return SimpleNamespace(
            data=[embedding_item(1), embedding_item(0)],
        )

    client = SimpleNamespace(
        embeddings=SimpleNamespace(create=create),
    )
    client_args = []
    monkeypatch.setattr(
        embeddings,
        "create_openai_client",
        lambda base_url, api_key: client_args.append((base_url, api_key)) or client,
    )

    result = embeddings.embed_texts(["first", "second"])

    assert client_args == [
        ("https://embeddings.example/v1", "embedding-token")
    ]
    assert captured == {
        "model": "provider/embedding-model",
        "input": ["first", "second"],
        "dimensions": embeddings.EMBEDDING_DIMENSION,
    }
    assert result[0][0] == 0.0
    assert result[1][0] == 1.0


@pytest.mark.parametrize(
    ("setting_name", "env_var"),
    [
        ("embedding_base_url", "EMBEDDING_BASE_URL"),
        ("embedding_api_key", "EMBEDDING_API_KEY"),
        ("embedding_model", "EMBEDDING_MODEL"),
    ],
)
def test_missing_remote_embedding_configuration(
    monkeypatch,
    setting_name,
    env_var,
):
    monkeypatch.setattr(
        embeddings,
        "get_settings",
        lambda: settings(**{setting_name: ""}),
    )

    with pytest.raises(embeddings.AIGatewayUnavailable, match=env_var):
        embeddings.embed_text("hello")


def test_embedding_dimension_must_match_pgvector(monkeypatch):
    monkeypatch.setattr(embeddings, "get_settings", settings)
    client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(  # noqa: ARG005
                data=[embedding_item(0, dimension=3)]
            )
        )
    )
    monkeypatch.setattr(
        embeddings,
        "create_openai_client",
        lambda base_url, api_key: client,
    )

    with pytest.raises(RuntimeError, match="required 384 dimensions"):
        embeddings.embed_text("hello")


def test_empty_embedding_batch_does_not_call_provider(monkeypatch):
    monkeypatch.setattr(
        embeddings,
        "create_openai_client",
        lambda base_url, api_key: pytest.fail("provider should not be called"),
    )

    assert embeddings.embed_texts([]) == []
