from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


router = APIRouter(tags=["health"])


def check_database(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_redis() -> bool:
    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=False,
        )
        return bool(redis_client.ping())
    except Exception:
        return False


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    database_ok = check_database(db)
    redis_ok = check_redis()

    all_ok = database_ok and redis_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "database": "ok" if database_ok else "error",
        "queue": "ok" if redis_ok else "error",
    }


@router.get("/health/live")
def liveness_check():
    return {
        "status": "ok",
    }


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    database_ok = check_database(db)
    redis_ok = check_redis()

    if not database_ok or not redis_ok:
        return {
            "status": "not_ready",
            "database": "ok" if database_ok else "error",
            "queue": "ok" if redis_ok else "error",
        }

    return {
        "status": "ready",
        "database": "ok",
        "queue": "ok",
    }