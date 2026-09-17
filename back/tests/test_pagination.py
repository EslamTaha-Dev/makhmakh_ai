import uuid
from datetime import datetime, timezone

from app.core.pagination import decode_cursor, encode_cursor


def test_cursor_round_trip():
    created_at = datetime.now(timezone.utc).replace(microsecond=0)
    item_id = uuid.uuid4()

    decoded = decode_cursor(encode_cursor(created_at, item_id))

    assert decoded == (created_at, item_id)


def test_invalid_cursor_is_rejected():
    assert decode_cursor("invalid") is None
