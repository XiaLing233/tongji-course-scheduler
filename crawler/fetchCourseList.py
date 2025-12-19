from utils import loginout
from utils import tjSql
import time

def fetchCourseList(session, calendar=120):
    '''
    Fetch course list from url, receive the authenticated session as parameter
    '''

    # 在这里指定每页的大小和要爬的学期
    PAGESIZE = 100
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

    for i in range(latest_calendar, latest_calendar - 8, -1):
        print(f"Fetching course list for calendar {i}")
        fetchCourseList(session, calendar=i)
        time.sleep(5)
