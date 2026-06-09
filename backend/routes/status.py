import json

import redis
from flask import Blueprint, request, jsonify, Response

from utils import bckndSql
from utils.redis_client import r, STREAM_KEY, STATUS_KEY, format_sse_event

status_bp = Blueprint('status', __name__)


@status_bp.route('/api/health', methods=['GET'])
def health():
    try:
        with bckndSql.bckndSql() as sql:
            sql.getHealth()
    except Exception as e:
        print(e)
        return jsonify({
            "code": 500,
            "msg": "数据库连接失败！"
        }), 500

    return jsonify({
        "code": 200,
        "msg": "服务健康！"
    }), 200


@status_bp.route('/api/getFetchLog', methods=['GET'])
def get_fetch_log():
    '''
    Server-Sent Events endpoint for real-time crawler log streaming.
    Reads from Redis Stream (XREAD BLOCK) and pushes log lines to the browser.

    EventSource auto-reconnects with Last-Event-ID header,
    which maps to the Redis Stream entry ID for resuming.

    SSE Events:
        log:       A new log line (data = plain text)
        meta:      Status info update (data = JSON)
        completed: Crawler finished successfully
        failed:    Crawler exited with error
    '''
    # Read headers outside the generator — gevent may lose request context on switch
    last_id = request.headers.get('Last-Event-ID', '0')

    def event_generator(last_id):

        # Phase 1: catch up missed messages
        try:
            if last_id == '0':
                history = r.xrange(STREAM_KEY, min='-', max='+')
            else:
                history = r.xrange(STREAM_KEY, min=f'({last_id}', max='+')

            for msg_id, fields in history:
                yield format_sse_event('log', msg_id, fields.get('msg', ''))
                last_id = msg_id

            # Push current status
            status_data = r.get(STATUS_KEY)
            if status_data:
                yield format_sse_event('meta', last_id, status_data)
        except redis.ConnectionError:
            yield format_sse_event('log', '0', '[系统] Redis 连接失败，重试中...')

        # Phase 2: block on new messages
        while True:
            try:
                result = r.xread({STREAM_KEY: last_id}, block=1000, count=50)
            except redis.ConnectionError:
                yield format_sse_event('log', '0', '[系统] Redis 连接失败，重试中...')
                continue

            if result:
                for _stream_name, messages in result:
                    for msg_id, fields in messages:
                        yield format_sse_event('log', msg_id, fields.get('msg', ''))
                        last_id = msg_id

            # Check completion
            status_str = r.get(STATUS_KEY)
            if status_str:
                try:
                    status = json.loads(status_str)
                    if status.get('status') in ('completed', 'failed'):
                        event_type = 'completed' if status['status'] == 'completed' else 'failed'
                        yield format_sse_event(event_type, last_id, status_str)
                        break
                except json.JSONDecodeError:
                    pass

    return Response(
        event_generator(last_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )
