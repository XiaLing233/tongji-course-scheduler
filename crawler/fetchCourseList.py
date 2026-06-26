import os
import time
from datetime import datetime

from dotenv import load_dotenv
from tqdm import tqdm

from utils import loginout
from utils import tjSql
from utils.smtp_email import SMTPEmailClient

load_dotenv()


class PipeTqdm(tqdm):
    """tqdm 在非 TTY 下可能用 \r 结尾而非 \n，导致 bash read 不返回行。
    这里在每个 display 后补一个 \n，确保管道里每行都以 \n 结束。"""
    def display(self, msg=None, pos=None):
        super().display(msg, pos)
        self.fp.write('\n')
        self.fp.flush()

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

            tqdm.write(
                f"[重试 {attempt}/{MAX_RETRIES}] "
                f"请求失败: {exc}")
            tqdm.write(f"  {delay}s 后重试...")

            if attempt < MAX_RETRIES:
                time.sleep(delay)
            else:
                tqdm.write(f"已达最大重试次数 {MAX_RETRIES}，放弃。")
                raise last_exc


PAGESIZE = 200


def fetchCourseList(session, calendar, target_db):
    """爬取一个学期的课程，写入 target_db。返回 (totalCourses, totalPages)。"""

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

    tqdm.write(f"学期 {calendar}  —  {total} 条课程, {total_pages} 页  →  {target_db}")

    for i in PipeTqdm(range(1, total_pages + 1), desc=f"学期 {calendar}", unit="页"):
        payload['pageNum_'] = i
        data = safeFetch(session, headers, payload)
        with tjSql.tjSql(target_db) as sql:
            sql.insertCourseList(data['data']['list'])
        time.sleep(3)

    tqdm.write(f"学期 {calendar}  [OK] 完成")
    return total, total_pages


def sync_one(session, calendar_id, name=None):
    """蓝绿同步单个学期：建库 → 日志(running) → 爬取 → 切换 → 日志(completed)。"""
    with tjSql.tjSql() as sql:
        target_db = sql.ensureCalendarDb(calendar_id, name)
        log_id = sql.startFetchLog(calendar_id)

    try:
        total_courses, total_pages = fetchCourseList(session, calendar_id, target_db)
    except Exception as e:
        tqdm.write(f"[FAIL] 学期 {calendar_id} 同步失败: {e}")
        with tjSql.tjSql() as sql:
            sql.finishFetchLog(log_id, status='failed', errorMessage=str(e))
        return

    with tjSql.tjSql() as sql:
        sql.switchActiveDb(calendar_id)
        sql.finishFetchLog(log_id, status='completed',
                           totalCourses=total_courses, totalPages=total_pages)

    tqdm.write(f"学期 {calendar_id}  已切换到 {target_db}")


if __name__ == "__main__":
    # TODO: US-1.3 argparse 替换
    latest_calendar = int(os.getenv('CRAWLER_LATEST_TERM', '0'))
    depth = int(os.getenv('CRAWLER_DEPTH', '1'))
    if not latest_calendar:
        tqdm.write("请使用 --calendar 参数或设置 CRAWLER_LATEST_TERM 环境变量")
        exit(-1)

    session = loginout.login()
    if session is None:
        exit(-1)

    semesters = list(range(latest_calendar - depth + 1, latest_calendar + 1))
    for idx, cal in enumerate(semesters, 1):
        tqdm.write(f"[{idx}/{len(semesters)}] 正在同步学期 {cal}")
        sync_one(session, cal)

    # 邮件通知
    if os.getenv('CRAWLER_SEND_EMAIL', 'false').lower() == 'true':
        email_client = SMTPEmailClient()
        now = datetime.now()
        with tjSql.tjSql() as sql:
            start_term = sql.calendarIdToText(semesters[0])
            end_term = sql.calendarIdToText(semesters[-1])
        subject = f"课程数据更新完成通知 - {now.strftime('%Y-%m-%d')}"
        body = (f"夏凌！\n\n课程数据已成功更新。\n"
                f"更新学期范围：{start_term} 至 {end_term}\n"
                f"更新完成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n\n祝好！\n琪露诺bot")
        if email_client.send_email(os.getenv('SMTP_SENDER', ''), subject, body):
            tqdm.write("[OK] 邮件通知已发送")
        else:
            tqdm.write("[FAIL] 邮件通知发送失败")
