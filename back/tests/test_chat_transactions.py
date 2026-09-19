import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.ai.ai_gateway.ai_gateway import AIGatewayUnavailable
from app.api.routes import chat as chat_routes
from app.main import app
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatRequest


class FakeSession:
    def __init__(self):
        self.scalar_results = [object(), None]
        self.pending = []
        self.committed = []
        self.events = []

    def scalar(self, statement):  # noqa: ARG002
        return self.scalar_results.pop(0)

    def add(self, value):
        self.pending.append(value)

    def _assign_ids(self):
        for value in self.pending:
            if hasattr(value, "id") and value.id is None:
                value.id = uuid.uuid4()

    def flush(self):
        self._assign_ids()
        self.events.append("flush")

    def commit(self):
        self._assign_ids()
        self.committed.extend(self.pending)
        self.pending.clear()
        self.events.append("commit")

    def rollback(self):
        self.pending.clear()
        self.events.append("rollback")

    def refresh(self, value):  # noqa: ARG002
        self.events.append("refresh")


def test_chat_openapi_documents_failure_session_id():
    response = app.openapi()["paths"]["/api/v1/courses/{course_id}/chat"][
        "post"
    ]["responses"]["503"]

    assert response["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ChatFailureResponse"
    )


def test_fallback_reuses_committed_session(monkeypatch):
    db = FakeSession()
    user = SimpleNamespace(id=uuid.uuid4())
    course_id = uuid.uuid4()

    def fail_after_user_turn(**kwargs):  # noqa: ANN003
        assert any(isinstance(item, ChatSession) for item in db.committed)
        assert any(
            isinstance(item, ChatMessage) and item.role == "user"
            for item in db.committed
        )
        raise RuntimeError("primary AI failed")

    monkeypatch.setattr(chat_routes, "run_agent", fail_after_user_turn)
    monkeypatch.setattr(
        chat_routes,
        "ai_gateway_execute",
        lambda **kwargs: "fallback answer",
    )
    monkeypatch.setattr(
        chat_routes,
        "get_configured_llm_model",
        lambda: "test-model",
    )

    response = chat_routes.chat.__wrapped__(
        request=SimpleNamespace(),
        course_id=course_id,
        data=ChatRequest(message="hello"),
        db=db,
        current_user=user,
    )

    sessions = [item for item in db.committed if isinstance(item, ChatSession)]
    messages = [item for item in db.committed if isinstance(item, ChatMessage)]

    assert response.session_id == sessions[0].id
    assert [(message.role, message.session_id) for message in messages] == [
        ("user", sessions[0].id),
        ("assistant", sessions[0].id),
    ]
    assert db.events.index("commit") < db.events.index("rollback")


def test_failed_ai_keeps_user_turn_and_returns_session_id(monkeypatch):
    db = FakeSession()
    user = SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(
        chat_routes,
        "run_agent",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("primary failed")),
    )
    monkeypatch.setattr(
        chat_routes,
        "ai_gateway_execute",
        lambda **kwargs: (_ for _ in ()).throw(
            AIGatewayUnavailable("fallback failed")
        ),
    )

    with pytest.raises(HTTPException) as error:
        chat_routes.chat.__wrapped__(
            request=SimpleNamespace(),
            course_id=uuid.uuid4(),
            data=ChatRequest(message="keep this message"),
            db=db,
            current_user=user,
        )

    sessions = [item for item in db.committed if isinstance(item, ChatSession)]
    messages = [item for item in db.committed if isinstance(item, ChatMessage)]

    assert error.value.status_code == 503
    assert error.value.detail["session_id"] == str(sessions[0].id)
    assert [(message.role, message.content) for message in messages] == [
        ("user", "keep this message")
    ]
