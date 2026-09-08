from rq import SimpleWorker

from app.services.queue import processing_queue, redis_connection
from rq import Queue


video_queue = Queue(
    "video_generation",
    connection=redis_connection,
)


if __name__ == "__main__":
    worker = SimpleWorker(
        [
            processing_queue,
            video_queue,
        ],
        connection=redis_connection,
        default_worker_ttl=600,
    )

    worker.work(
        burst=False,
    )