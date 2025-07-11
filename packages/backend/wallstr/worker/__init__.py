import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import (
    AgeLimit,
    Callbacks,
    CurrentMessage,
    ShutdownNotifications,
    TimeLimit,
)
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

import wallstr.sentry  #  type: ignore[import]
from wallstr.conf import settings

from .middlewares import AsyncSessionMiddleware

rabbitmq_broker = RabbitmqBroker(
    url=settings.RABBITMQ_URL.get_secret_value(),
    middleware=[
        AgeLimit(),  # type: ignore[no-untyped-call]
        # hard limit of 20 minutes
        # use `async with time_limit()` inside the task for graceful shutdown
        TimeLimit(time_limit=20 * 60 * 1000),  # type: ignore[no-untyped-call]
        ShutdownNotifications(),  # type: ignore[no-untyped-call]
        Callbacks(),
        AsyncSessionMiddleware(),
        CurrentMessage(),
    ],
)  # type: ignore[no-untyped-call]
redis_backend = RedisBackend(url=settings.REDIS_URL.get_secret_value())

# middlewares
rabbitmq_broker.add_middleware(Results(backend=redis_backend, store_results=True))  # type: ignore[no-untyped-call]

# create queues
rabbitmq_broker.declare_queue("parse", ensure=True)  # type: ignore[no-untyped-call]

dramatiq.set_broker(rabbitmq_broker)

__all__ = ["dramatiq"]
