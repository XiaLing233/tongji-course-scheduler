"""Redis Pub/Sub 监听 — 爬虫蓝绿切换后通知 backend 重建学期库连接池。

爬虫在 crawler/db/redis_pub.py 的 cache_invalidate() 中，切库完成后发布
`backend:pool-refresh <calendarId>`。本模块在每个 gunicorn worker 启动时
（app.py import，Dockerfile 未用 --preload）起一个守护线程订阅该频道，
收到消息即调用 router.invalidate_pool() 丢弃旧池，下次请求自动按新
registry 重建。

消息丢失无害：backend 重启时连接池本来就会重建。
"""

import os
import threading
import time

import redis

CHANNEL = 'backend:pool-refresh'
_RECONNECT_INTERVAL = 5  # Redis 断连后的重连间隔（秒）


def start_pool_refresh_listener(router):
    """起守护线程订阅 pool-refresh 频道，通知 router 丢弃过期连接池。"""
    t = threading.Thread(
        target=_listen_loop, args=(router,), name='pool-refresh', daemon=True)
    t.start()


def _listen_loop(router):
    while True:
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST'),
                port=int(os.getenv('REDIS_PORT')),
                db=int(os.getenv('REDIS_DB')),
                decode_responses=True,
            )
            pubsub = client.pubsub()
            pubsub.subscribe(CHANNEL)
            for msg in pubsub.listen():
                if msg.get('type') == 'message':
                    _handle_message(router, msg.get('data'))
        except Exception:
            pass  # Redis 断连等任何异常：静默等待后重连
        time.sleep(_RECONNECT_INTERVAL)


def _handle_message(router, data):
    """解析 calendarId 并丢弃对应连接池。非法消息静默忽略。"""
    try:
        calendar_id = int(data)
    except (TypeError, ValueError):
        return
    router.invalidate_pool(calendar_id)
