from utils import loginout
from utils import tjSql
from utils.smtp_email import SMTPEmailClient
import configparser
import time
from datetime import datetime

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

    # fetch course list
    response = session.post("https://1.tongji.edu.cn/api/arrangementservice/manualArrange/page?profile", headers=headers, json=payload)

    # Recursively fetch all courses
    total = response.json()['data']['total_']

    # Debug
    isWait = False

    for i in range(1, total // PAGESIZE + 1 + 1): # floor division
        # Prepare payload
        payload['pageNum_'] = i

        # Fetch
        response = session.post("https://1.tongji.edu.cn/api/arrangementservice/manualArrange/page?profile", headers=headers, json=payload)

        # Insert into database
        with tjSql.tjSql() as sql:
            sql.insertCourseList(response.json()['data']['list'])

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

    print("Course list fetched successfully")

    # loginout.logout(session)
    

if __name__ == "__main__":
    # Login
    session = loginout.login()

    if (session is None):
        exit(-1)

    latest_calendar = 121
    depth = 2  # 爬取深度，从当前学期开始往前爬取的学期数

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
    config = configparser.ConfigParser()
    config.read("config.ini")
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
