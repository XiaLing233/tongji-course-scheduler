"""
Shared Redis client for SSE streaming.
Initialized once from app.py, imported by routes that need it.

Uses a mutable dict as container so that ``from redis_client import state``
always sees the live values set by init_redis() across all Gunicorn workers.
"""

import redis

state = {
    'r': None,
    'stream_key': None,
    'status_key': None,
    'progress_key': None,
}


def init_redis(redis_cfg):
    """Initialize Redis connection from config. Must be called before first request."""
    state['r'] = redis.Redis(
        host=redis_cfg['host'],
        port=redis_cfg.getint('port'),
        db=redis_cfg.getint('db'),
        decode_responses=True,
    )
    state['stream_key'] = redis_cfg['stream_key']
    state['status_key'] = redis_cfg['status_key']
    state['progress_key'] = redis_cfg['progress_key']


def format_sse_event(event_type, msg_id, data):
    """Format a single SSE frame."""
    return f'id: {msg_id}\nevent: {event_type}\ndata: {data}\n\n'
