from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.jobs.cleanup_expired_tokens import cleanup_expired_tokens
from app.jobs.reconcile_fawry_payments import (
    reconcile_pending_fawry_payments,
)


settings = get_settings()


class WorkerSettings:
    functions = [
        reconcile_pending_fawry_payments,
        cleanup_expired_tokens,
    ]
    cron_jobs = [
        cron(
            reconcile_pending_fawry_payments,
            minute=set(range(0, 60, 15)),
        ),
        cron(
            cleanup_expired_tokens,
            hour={3},
            minute={0},
        ),
    ]
    redis_settings = RedisSettings.from_dsn(
        settings.arq_redis_url
    )
    max_jobs = 10
    job_timeout = 300
