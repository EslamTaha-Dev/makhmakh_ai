import base64
import uuid
from datetime import datetime


def encode_cursor(created_at: datetime, item_id: uuid.UUID) -> str:
    value = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(value.encode()).decode()


def decode_cursor(cursor: str | None) -> tuple[datetime, uuid.UUID] | None:
    if not cursor:
        return None

    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        created_at, item_id = raw.rsplit("|", 1)
        return datetime.fromisoformat(created_at), uuid.UUID(item_id)
    except (ValueError, TypeError, UnicodeError):
        return None
