from datetime import datetime, timezone

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.refresh_token import RefreshToken
from app.services.queue import payment_queue


TOKEN_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
TOKEN_CLEANUP_LOCK_KEY = "makhmakh:token-cleanup:scheduler-lock"


def cleanup_expired_tokens_job() -> int:
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
        schedule_next_token_cleanup()


def schedule_next_token_cleanup() -> None:
    payment_queue.enqueue_in(
        TOKEN_CLEANUP_INTERVAL_SECONDS,
        "app.services.token_cleanup.cleanup_expired_tokens_job",
        job_timeout=300,
    )


def start_token_cleanup() -> None:
    try:
        acquired = payment_queue.connection.set(
            TOKEN_CLEANUP_LOCK_KEY,
            "1",
            nx=True,
            ex=TOKEN_CLEANUP_INTERVAL_SECONDS + 60,
        )

        if not acquired:
            return

        payment_queue.enqueue(
            "app.services.token_cleanup.cleanup_expired_tokens_job",
            job_timeout=300,
        )
    except Exception:
        return
