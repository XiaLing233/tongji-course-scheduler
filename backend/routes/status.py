import json

import redis
from flask import Blueprint, request, jsonify, Response

from bckndSql import bckndSql
from utils.redis_client import state, format_sse_event

status_bp = Blueprint('status', __name__)


@status_bp.route('/api/health', methods=['GET'])
def health():
    try:
        with bckndSql() as sql:
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


@status_bp.route('/api/sync/history/<int:log_id>/stream', methods=['GET'])
def sync_history_stream(log_id):
    '''
    SSE 端点：实时推送指定 fetchlog 的日志。
    读到 level='end' 时发送 end 事件并关闭连接。'''
    last_id = request.headers.get('Last-Event-ID', '0')

    def event_generator(log_id, last_id):
        r = state['r']
        stream_key = state['stream_key']

        def _emit(msg_id, fields):
            event_type = 'end' if fields.get('level') == 'end' else 'log'
            return format_sse_event(event_type, msg_id,
                                    json.dumps(dict(fields), ensure_ascii=False)), event_type

        # Phase 1: 追赶历史消息
        try:
            if last_id == '0':
                history = r.xrange(stream_key, min='-', max='+')
            else:
                history = r.xrange(stream_key, min=f'({last_id}', max='+')

            for msg_id, fields in history:
                if fields.get('fetchlogId') != str(log_id):
                    last_id = msg_id
                    continue
                data, event_type = _emit(msg_id, fields)
                yield data
                last_id = msg_id
                if event_type == 'end':
                    return
        except redis.ConnectionError:
            pass

        # Phase 2: 阻塞等待新消息
        while True:
            try:
                result = r.xread({stream_key: last_id}, block=3000, count=50)
            except redis.ConnectionError:
                continue

            if result:
                for _, messages in result:
                    for msg_id, fields in messages:
                        if fields.get('fetchlogId') != str(log_id):
                            last_id = msg_id
                            continue
                        data, event_type = _emit(msg_id, fields)
                        yield data
                        last_id = msg_id
                        if event_type == 'end':
                            return

    return Response(
        event_generator(log_id, last_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@status_bp.route('/api/sync/history', methods=['GET'])
def sync_history():
    '''同步历史列表（不含 fullLog）。支持 ?calendarId= 筛选和分页。'''
    calendar_id = request.args.get('calendarId', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)

    with bckndSql() as sql:
        rows = sql.getSyncHistory(calendar_id, page, page_size)

    return jsonify({'code': 200, 'data': [_history_row(r) for r in rows]}), 200


@status_bp.route('/api/sync/history/<int:log_id>', methods=['GET'])
def sync_history_detail(log_id):
    '''单条同步记录详情（含 fullLog）。'''
    with bckndSql() as sql:
        row = sql.getSyncHistoryDetail(log_id)

    if not row:
        return jsonify({'code': 404, 'msg': '记录不存在'}), 404

    return jsonify({'code': 200, 'data': _history_row(row, with_full_log=True)}), 200


def _fmt(ts):
    """MySQL datetime(3) → 'YYYY-MM-DD HH:MM:SS'"""
    if ts is None:
        return None
    return str(ts)[:19]


def _history_row(row, with_full_log=False):
    d = {
        'id': row[0], 'calendarId': row[1], 'calendarName': row[2],
        'startTime': _fmt(row[3]), 'endTime': _fmt(row[4]),
        'status': row[5], 'totalCourses': row[6],
        'totalPages': row[7], 'msg': row[8], 'errorMessage': row[9],
    }
    if with_full_log:
        d['fullLog'] = row[10]
    return d
