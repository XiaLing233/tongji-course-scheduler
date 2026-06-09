"""
Shared Redis client for SSE streaming.
Initialized once from app.py, imported by routes that need it.
"""

import redis

r = None
STREAM_KEY = None
STATUS_KEY = None


def init_redis(redis_cfg):
    """Initialize Redis connection from config. Must be called before first request."""
    global r, STREAM_KEY, STATUS_KEY
    r = redis.Redis(
        host=redis_cfg['host'],
        port=redis_cfg.getint('port'),
        db=redis_cfg.getint('db'),
        decode_responses=True,
    )
    STREAM_KEY = redis_cfg['stream_key']
    STATUS_KEY = redis_cfg['status_key']


def format_sse_event(event_type, msg_id, data):
    """Format a single SSE frame."""
    return f'id: {msg_id}\nevent: {event_type}\ndata: {data}\n\n'
