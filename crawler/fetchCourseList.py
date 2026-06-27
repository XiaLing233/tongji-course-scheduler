import argparse
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

from tjSql import tjSql
from auth import loginout
from db.redis_pub import publish as redis_publish, cache_invalidate as redis_cache_invalidate
from meru.smtp import SMTPEmailClient

load_dotenv()


def _log(message, log_id=None, calendar_id=None, calendar_name=None,
        level='info', seq=0):
    """打印到控制台，同时发布到 Redis Stream。自动加时间戳。"""
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {message}'
    print(line)
    if log_id is not None:
        redis_publish(log_id, calendar_id, calendar_name, level, line, seq=seq)


# 1 系统的 URL
URL = "https://1.tongji.edu.cn/api/arrangementservice/manualArrange/page?profile"

# 重试相关配置
MAX_RETRIES = 10          # 最大重试次数
BASE_DELAY = 3            # 基础等待秒数（退避基数）
MAX_DELAY = 120           # 单次等待上限（秒）


def safeFetch(session, headers, payload):
    """
    带重试的请求-解析一体函数：
    - 发送 POST 请求
    - 尝试解析 JSON
    - 校验响应结构（data.list 必须存在）
    - 失败时指数退避重试
    返回: dict — 解析成功的 JSON 对象
    """
    last_exc = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.post(URL, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )

            data = response.json()

            if 'data' not in data or 'list' not in data['data']:
                raise RuntimeError(
                    f"响应结构异常，缺少 data.list 字段。"
                    f"实际 keys: {list(data.keys())}"
                )

            return data

        except Exception as exc:
            last_exc = exc
            delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)

            _log(f"[重试 {attempt}/{MAX_RETRIES}] 请求失败: {exc}")
            _log(f"  {delay}s 后重试...")

            if attempt < MAX_RETRIES:
                time.sleep(delay)
            else:
                _log(f"已达最大重试次数 {MAX_RETRIES}，放弃。")
                raise last_exc


PAGESIZE = 200


def fetchCourseList(session, calendar, target_db, log_id=None):
    """爬取一个学期的课程，写入 target_db。返回 (totalCourses, totalPages, calendarName)。"""

    payload = {
        "condition": {
            "trainingLevel": "",
            "campus": "",
            "calendar": calendar,
            "college": "",
            "course": "",
            "ids": [],
            "isChineseTeaching": None,
        },
        "pageNum_": 1,
        "pageSize_": 20,  # 小请求先拿 total，减少首包体积
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://1.tongji.edu.cn/taskResultQuery",
    }

    data = safeFetch(session, headers, payload)
    total = data['data']['total_']
    total_pages = total // PAGESIZE + 1
    payload['pageSize_'] = PAGESIZE  # 后续请求用全量

    # 从第一页第一条课程提取学期中文名（如 "2025-2026学年第1学期"）
    calendar_name = data['data']['list'][0]['calendarIdI18n']

    _log(f"学期 {calendar_name}  —  {total} 条课程, {total_pages} 页  →  {target_db}",
         log_id, calendar, calendar_name)

    for i in range(1, total_pages + 1):
        payload['pageNum_'] = i
        data = safeFetch(session, headers, payload)
        with tjSql(target_db) as sql:
            sql.insertCourseList(
                data['data']['list'],
                warn=lambda msg: _log(msg, log_id, calendar, calendar_name, level='warning')
            )
        _log(f'第 {i}/{total_pages} 页完成 ({min(i * PAGESIZE, total)}/{total} 条)',
             log_id, calendar, calendar_name, seq=i)
        time.sleep(3)

    _log(f"学期 {calendar}  完成", log_id, calendar, calendar_name)
    return total, total_pages, calendar_name


def sync_one(session, calendar_id, msg=''):
    """蓝绿同步单个学期：建库 → 日志(running) → 爬取 → 命名 → 切换 → 日志(completed)。"""
    with tjSql() as sql:
        target_db = sql.ensureCalendarDb(calendar_id)
        log_id = sql.startFetchLog(calendar_id, msg=msg)

    try:
        total_courses, total_pages, calendar_name = fetchCourseList(
            session, calendar_id, target_db, log_id=log_id)
    except Exception as e:
        _log(f"学期 {calendar_id} 同步失败: {e}", log_id, calendar_id,
             level='error')
        # 尝试更新 fetchlog 状态——MySQL 可能还断着，单独 try
        try:
            with tjSql() as sql:
                sql.finishFetchLog(log_id, status='failed', errorMessage=str(e))
        except Exception as e2:
            _log(f"无法更新 fetchlog 状态: {e2}", log_id, calendar_id,
                 level='error')
        redis_publish(log_id, calendar_id, '', 'end', 'sync failed')
        return False, calendar_id, None

    with tjSql() as sql:
        sql.setCalendarName(calendar_id, calendar_name)
        sql.switchActiveDb(calendar_id)
        sql.finishFetchLog(log_id, status='completed',
                           totalCourses=total_courses, totalPages=total_pages)

    _log(f"学期 {calendar_id}  已切换到 {target_db}", log_id, calendar_id, calendar_name)
    redis_publish(log_id, calendar_id, calendar_name, 'end', 'sync completed')

    cleared = redis_cache_invalidate(calendar_id)
    if cleared:
        _log(f"已清除 {cleared} 条后端缓存")

    return True, calendar_id, calendar_name


def parse_calendars():
    parser = argparse.ArgumentParser(
        description='同济课程数据同步 — 蓝绿部署，独立学期更新')
    parser.add_argument('-c', '--calendars', type=int, nargs='+', required=True,
                        help='指定学期 (e.g. -c 122 / -c 122 121)')
    parser.add_argument('-m', '--msg', type=str, default='', help='同步备注')
    parser.add_argument('--fail-fast', action='store_true', help='任一学期失败则停止')
    parser.add_argument('--dry-run', action='store_true', help='只打印计划，不执行')

    args = parser.parse_args()
    return sorted(args.calendars), args


if __name__ == "__main__":
    semesters, args = parse_calendars()

    if args.dry_run:
        _log(f"干跑模式 — 将同步学期: {semesters}")
        _log(f"干跑模式 — 备注: {args.msg or '(无)'}")
        sys.exit(0)

    session = loginout.login()
    if session is None:
        sys.exit(1)

    failed = []
    for idx, cal in enumerate(semesters, 1):
        _log(f"[{idx}/{len(semesters)}] 正在同步学期 {cal}")
        try:
            ok, cal_id, cal_name = sync_one(session, cal, msg=args.msg)
        except Exception as e:
            _log(f"学期 {cal} 同步异常: {e}", level='error')
            ok = False
            cal_id = cal
            if args.fail_fast:
                sys.exit(1)

        if not ok:
            failed.append(cal_id)

    # 邮件通知
    if os.getenv('CRAWLER_SEND_EMAIL', 'false').lower() == 'true':
        email_client = SMTPEmailClient()
        now = datetime.now()
        with tjSql() as sql:
            names = [sql.calendarIdToText(c) or str(c) for c in semesters]
        status_text = '完成' if not failed else f'部分失败 (失败学期: {failed})'
        subject = f"课程数据更新{status_text} - {now.strftime('%Y-%m-%d')}"
        body = (f"夏凌！\n\n课程数据更新{status_text}。\n"
                f"更新学期：{', '.join(names)}\n"
                f"完成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n\n祝好！\n琪露诺bot")
        if email_client.send_email(os.getenv('SMTP_SENDER', ''), subject, body):
            _log("邮件通知已发送")
        else:
            _log("邮件通知发送失败", level='error')

    sys.exit(1 if failed else 0)
