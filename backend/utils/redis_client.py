"""
Shared Redis client for SSE streaming.
Initialized once from app.py, imported by routes that need it.

Uses a mutable dict as container so that ``from redis_client import state``
always sees the live values set by init_redis() across all Gunicorn workers.
"""

import os

import redis

state = {
    'r': None,
    'stream_key': None,
    'status_key': None
}


def init_redis():
    """Initialize Redis connection from env vars. Must be called before first request."""
    state['r'] = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0')),
        decode_responses=True,
    )
    state['stream_key'] = os.getenv('REDIS_STREAM_KEY', 'crawler:log')
    state['status_key'] = os.getenv('REDIS_STATUS_KEY', 'crawler:status')


def format_sse_event(event_type, msg_id, data):
    """Format a single SSE frame."""
    return f'id: {msg_id}\nevent: {event_type}\ndata: {data}\n\n'
