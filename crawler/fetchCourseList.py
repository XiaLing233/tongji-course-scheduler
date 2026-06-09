from utils import loginout
from utils import tjSql
from utils.smtp_email import SMTPEmailClient
import configparser
import time
from datetime import datetime
from tqdm import tqdm

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


def fetchCourseList(session, calendar=120, depth=1):
    """
    Fetch course list from url, receive the authenticated session as parameter
    depth: the number of semesters to fetch, starting from current calendar
    """

    PAGESIZE = 200
    CALENDAR = calendar

    payload = {
        "condition": {
            "trainingLevel": "",
            "campus": "",
            "calendar": CALENDAR,
            "college": "",
            "course": "",
            "ids": [],
            "isChineseTeaching": None,
        },
        "pageNum_": 1,
        "pageSize_": PAGESIZE
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://1.tongji.edu.cn/taskResultQuery"
    }

    # 第一页：获取总数并入库
    data = safeFetch(session, headers, payload)
    total = data['data']['total_']
    total_pages = total // PAGESIZE + 1

    with tjSql.tjSql() as sql:
        sql.insertCourseList(data['data']['list'])

    tqdm.write(f"学期 {CALENDAR}  —  {total} 条课程, {total_pages} 页")

    # 逐页抓取（带进度条）
    # disable=False 确保管道 / 非 TTY 环境下也能正常输出，逐行写入 Redis Stream
    for i in tqdm(
        range(2, total_pages + 1),
        desc=f"学期 {CALENDAR}",
        unit="页",
        disable=False,
        miniters=1,
    ):
        payload['pageNum_'] = i
        data = safeFetch(session, headers, payload)

        with tjSql.tjSql() as sql:
            sql.insertCourseList(data['data']['list'])

        time.sleep(3)

    tqdm.write(f"学期 {CALENDAR}  [OK] 完成")


if __name__ == "__main__":
    session = loginout.login()
    if session is None:
        exit(-1)

    config = configparser.ConfigParser()
    config.read("config.ini")

    latest_calendar = config.getint("Spider", "latest_term")
    depth = config.getint("Spider", "depth")

    # 删除旧记录
    tqdm.write(f"开始删除旧记录  |  学期 {latest_calendar}, 深度 {depth}")
    with tjSql.tjSql() as sql:
        sql.deleteOldRecordsInRange(latest_calendar, depth)

    # 逐学期抓取
    semesters = list(range(latest_calendar - depth + 1, latest_calendar + 1))
    for idx, cal in enumerate(semesters, 1):
        tqdm.write(f"[{idx}/{len(semesters)}] 正在爬取学期 {cal}")
        fetchCourseList(session, calendar=cal, depth=depth)

    # 记录日志
    with tjSql.tjSql() as sql:
        sql.insertFetchLog(cal, depth)
    time.sleep(5)

    # 邮件通知
    email_client = SMTPEmailClient("config.ini")
    me = config.get("SMTP", "me")
    now = datetime.now()

    with tjSql.tjSql() as sql:
        start_term = sql.calendarIdToText(latest_calendar - depth + 1)
        end_term = sql.calendarIdToText(latest_calendar)

    subject = f"课程数据更新完成通知 - {now.strftime('%Y-%m-%d')}"
    body = f"夏凌！\n\n课程数据已成功更新。\n\n更新学期范围（闭区间）：{start_term} 至 {end_term}（学期代码 {latest_calendar - depth + 1} 至 {latest_calendar}）\n更新完成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n\n祝好！\n琪露诺bot"

    success = email_client.send_email(me, subject, body)
    if success:
        tqdm.write("[OK] 邮件通知已发送")
    else:
        tqdm.write("[FAIL] 邮件通知发送失败")
