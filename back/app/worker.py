from rq import SimpleWorker

from app.services.payment_reconciliation import start_payment_reconciliation
from app.services.queue import (
    payment_queue,
    email_queue,
    redis_connection,
)
from app.services.token_cleanup import start_token_cleanup


if __name__ == "__main__":
    start_payment_reconciliation()
    start_token_cleanup()

    worker = SimpleWorker(
        [
            payment_queue,
            email_queue,
        ],
        connection=redis_connection,
        default_worker_ttl=600,
        with_scheduler=True,
    )

    worker.work(burst=False)
