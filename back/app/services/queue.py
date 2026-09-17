"""Job queues.

Production runs the RQ workers defined in ``docker-compose.yml``. When Redis is not
reachable the helper below runs the job in a background thread instead, so an
uploaded material is still processed and the API does not fail the request just
because the worker fleet is absent (local development, single-container deploys).
"""

import importlib
import logging
import threading
from typing import Any, Callable

from redis import Redis
from rq import Queue

from app.core.config import get_settings

logger = logging.getLogger("makhmakh.queue")


settings = get_settings()


redis_connection = Redis.from_url(
    settings.redis_url,
    decode_responses=False,
)


processing_queue = Queue(
    "material_processing",
    connection=redis_connection,
)


video_queue = Queue(
    "video_generation",
    connection=redis_connection,
)


payment_queue = Queue(
    "payment_processing",
    connection=redis_connection,
)


email_queue = Queue(
    "email_delivery",
    connection=redis_connection,
)


def resolve_callable(target: Callable[..., Any] | str) -> Callable[..., Any]:
    """Accept either a callable or the dotted path RQ uses for jobs."""

    if callable(target):
        return target

    module_path, _, attribute = target.rpartition(".")

    if not module_path:
        raise ValueError(f"Invalid job path: {target}")

    module = importlib.import_module(module_path)

    return getattr(module, attribute)


def enqueue_job(
    queue: Queue,
    target: Callable[..., Any] | str,
    *args: Any,
    **kwargs: Any,
) -> Any | None:
    """Enqueue a job, falling back to an in-process background thread.

    Returns the RQ job when the queue accepted it, or ``None`` when the job was
    executed inline because the queue was unavailable.
    """

    if settings.run_jobs_inline:
        return _run_inline(target, *args, **kwargs)

    try:
        return queue.enqueue(target, *args, **kwargs)
    except Exception as exc:  # redis/rq connection failures
        logger.warning(
            "Job queue '%s' is unavailable (%s). Running %s inline instead.",
            queue.name,
            exc,
            target if isinstance(target, str) else getattr(target, "__name__", target),
        )

        return _run_inline(target, *args, **kwargs)


def _run_inline(
    target: Callable[..., Any] | str,
    *args: Any,
    **kwargs: Any,
) -> None:
    func = resolve_callable(target)

    def run() -> None:
        try:
            func(*args, **kwargs)
        except Exception:
            logger.exception(
                "Inline job failed: %s",
                getattr(func, "__name__", func),
            )

    threading.Thread(
        target=run,
        name=f"inline-job-{getattr(func, '__name__', 'job')}",
        daemon=True,
    ).start()

    return None
