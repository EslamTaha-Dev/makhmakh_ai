import json
import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.security_event import SecurityEvent


def record_security_event(
    db: Session,
    event_type: str,
    user_id: uuid.UUID | None = None,
    request: Request | None = None,
    details: dict | None = None,
) -> None:
    ip_address = None
    user_agent = None

    if request is not None:
        if request.client:
            ip_address = request.client.host

        user_agent = request.headers.get("user-agent")

    event = SecurityEvent(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=json.dumps(details) if details else None,
    )

    db.add(event)