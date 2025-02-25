from utils import loginout
from utils import tjSql
import time

def fetchCourseList(session):
    '''
    Fetch course list from url, receive the authenticated session as parameter
    '''

    # 在这里指定每页的大小和要爬的学期
    PAGESIZE = 100
    CALENDAR = 119

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
    isWait = True

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

    loginout.logout(session)
    

if __name__ == "__main__":
    # Login
    session = loginout.login()

    if (session == None):
        exit(-1)

    # import json
    # 测试环境，记录 cookies
    # with open("cookies.json", "w") as f:
        # json.dump(session.cookies.get_dict(), f)

    # read cookies
    # with open("cookies.json", "r") as f:
        # cookies = json.load(f)

    # import requests

    # session = requests.Session()
    # session.cookies.update(cookies)

    # Fetch course list
    fetchCourseList(session)