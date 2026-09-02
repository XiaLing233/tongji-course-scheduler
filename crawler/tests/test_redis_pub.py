"""cache_invalidate 应发布 pool-refresh 通知，让 backend 重建连接池。

需要 Redis（docker-compose.test.yml 提供 test-redis）。
"""

import os

import redis

from db.redis_pub import cache_invalidate


def _get_redis():
    return redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        db=int(os.getenv('REDIS_DB')),
        decode_responses=True,
    )


def test_cache_invalidate_publishes_pool_refresh():
    pubsub = _get_redis().pubsub()
    pubsub.subscribe('backend:pool-refresh')
    assert pubsub.get_message(timeout=2)['type'] == 'subscribe'

    cache_invalidate(999)

    msg = pubsub.get_message(timeout=2)
    assert msg is not None and msg['type'] == 'message'
    assert msg['data'] == '999'
