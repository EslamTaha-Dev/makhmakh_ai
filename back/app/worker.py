from rq import SimpleWorker

from app.services.payment_reconciliation import start_payment_reconciliation
from app.services.queue import (
    payment_queue,
    processing_queue,
    redis_connection,
    video_queue,
)


if __name__ == "__main__":
    start_payment_reconciliation()

    worker = SimpleWorker(
        [
            processing_queue,
            video_queue,
            payment_queue,
        ],
        connection=redis_connection,
        default_worker_ttl=600,
        with_scheduler=True,
    )

    worker.work(burst=False)