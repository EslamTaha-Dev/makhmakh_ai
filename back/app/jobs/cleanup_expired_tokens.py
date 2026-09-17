from datetime import datetime, timezone

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.refresh_token import RefreshToken


async def cleanup_expired_tokens(ctx: dict) -> int:
    del ctx
    db = SessionLocal()

    try:
        result = db.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        db.commit()
        return result.rowcount or 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
