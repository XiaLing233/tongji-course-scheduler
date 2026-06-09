from utils import loginout
from utils import tjSql
from utils.smtp_email import SMTPEmailClient
import configparser
import time

from datetime import datetime

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

            # HTTP 状态码检查
            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )

            # JSON 解析
            data = response.json()

            # 结构校验：是否包含预期的 data.list
            if 'data' not in data or 'list' not in data['data']:
                raise RuntimeError(
                    f"响应结构异常，缺少 data.list 字段。"
                    f"实际 keys: {list(data.keys())}"
                )

            # 成功，返回解析后的数据
            return data

        except Exception as exc:
            last_exc = exc
            delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)

            print(
                f"[重试 {attempt}/{MAX_RETRIES}] "
                f"请求失败: {exc}"
            )
            print(f"  {delay}s 后重试...")

            if attempt < MAX_RETRIES:
                time.sleep(delay)
            else:
                # 最后一次也失败了，抛出异常让上层处理
                print(f"已达最大重试次数 {MAX_RETRIES}，放弃。")
                raise last_exc


def fetchCourseList(session, calendar=120, depth=1):
    '''
    Fetch course list from url, receive the authenticated session as parameter
    depth: the number of semesters to fetch, starting from current calendar
    '''

    # 在这里指定每页的大小和要爬的学期
    PAGESIZE = 200
    CALENDAR = calendar

    # prepare payload
    payload = {
        "condition":
        {
            "trainingLevel":"",
            "campus":"",
            "calendar":CALENDAR,
            "college":"",
            "course":"",
            "ids":[],
            "isChineseTeaching": None,
        },
        "pageNum_":1,
        "pageSize_":PAGESIZE
    }

    # Mock a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Referer": "https://1.tongji.edu.cn/taskResultQuery"
    }

    # 第一页：获取总数（带重试）
    data = safeFetch(session, headers, payload)
    total = data['data']['total_']

    print(f"学期 {CALENDAR} 共有 {total} 条课程，每页 {PAGESIZE} 条，共 {total // PAGESIZE + 1} 页")

    # Debug
    isWait = False

    for i in range(1, total // PAGESIZE + 1 + 1): # floor division
        # Prepare payload
        payload['pageNum_'] = i

        # Fetch (带重试)
        data = safeFetch(session, headers, payload)

        # Insert into database
        with tjSql.tjSql() as sql:
            sql.insertCourseList(data['data']['list'])

        print("\n\n\n=====================================")
        print("第", i, "页，共", total // PAGESIZE + 1, "页")
        print("=====================================\n\n\n")

        # Debug
        if isWait:
            print("Press Enter to continue, input NOBREAK to disable waiting")

            if input() == "NOBREAK":
                isWait = False

        else:
            time.sleep(3)


    print(f"学期 {CALENDAR} 课程列表抓取完成")

    # loginout.logout(session)
    

if __name__ == "__main__":
    # Login
    session = loginout.login()

    if (session is None):
        exit(-1)

    config = configparser.ConfigParser()
    config.read("config.ini")

    latest_calendar = config.getint("Spider", "latest_term")
    depth = config.getint("Spider", "depth")  # 爬取深度，从当前学期开始往前爬取的学期数

    # Delete old records in the depth range before fetching
    print(f"\n开始删除旧记录，当前学期 {latest_calendar}，深度 {depth}")
    with tjSql.tjSql() as sql:
        sql.deleteOldRecordsInRange(latest_calendar, depth)
    print("旧记录删除完成\n")


    for i in range(latest_calendar - depth + 1, latest_calendar + 1, 1):
        print(f"正在爬取学期 {i}")
        fetchCourseList(session, calendar=i, depth=depth)
    

    # Insert fetch log after all fetching is done
    with tjSql.tjSql() as sql:
        sql.insertFetchLog(i, depth)
        
        time.sleep(5)

    # Send email notification after all fetching is done
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
        print("Email notification sent successfully.")
    else:
        print("Failed to send email notification.")
