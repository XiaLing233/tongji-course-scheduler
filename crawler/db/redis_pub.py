"""Redis 日志发布器。同步过程中写 Stream（SSE 推送），同时累积到 LIST 供 fullLog 聚合。
所有 Redis 操作静默容错——Redis 不可用时不影响爬虫主流程。"""

import os

import redis

_stream_key = os.getenv('REDIS_STREAM_KEY')
_maxlen = int(os.getenv('REDIS_MAXLEN'))


def _get_redis():
    return redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        db=int(os.getenv('REDIS_DB')),
        decode_responses=True,
    )


def publish(fetchlog_id, calendar_id, calendar_name, level, message, seq=0):
    """写一条日志到 Redis Stream + 累积 LIST。"""
    try:
        r = _get_redis()
        fields = {
            'fetchlogId': str(fetchlog_id),
            'calendarId': str(calendar_id),
            'calendarName': calendar_name,
            'level': level,
            'seq': str(seq),
            'message': message,
        }
        r.xadd(_stream_key, fields, maxlen=_maxlen)
        r.rpush(f'crawler:log:{fetchlog_id}', f'[{level}] {message}')
        r.expire(f'crawler:log:{fetchlog_id}', 86400)
    except redis.RedisError:
        pass


def aggregate(fetchlog_id):
    """读取并删除累积 LIST，返回聚合日志文本。"""
    try:
        r = _get_redis()
        key = f'crawler:log:{fetchlog_id}'
        logs = r.lrange(key, 0, -1)
        r.delete(key)
        return '\n'.join(logs) if logs else None
    except redis.RedisError:
        return None
