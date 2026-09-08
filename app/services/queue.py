from redis import Redis
from rq import Queue

from app.core.config import get_settings


settings = get_settings()

redis_connection = Redis.from_url(
    settings.redis_url,
    decode_responses=False,
)

processing_queue = Queue(
    "material_processing",
    connection=redis_connection,
)